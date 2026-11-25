"""Actual ISO boot, desktop/browser RAM samples, screenshots and ACPI shutdown."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import threading
import time

parser = argparse.ArgumentParser()
parser.add_argument("edition", choices=("extreme-lite", "education"))
parser.add_argument("--ram", type=int, default=2048)
parser.add_argument("--ovmf-dir", type=Path, default=Path("/usr/share/OVMF"))
parser.add_argument("--disk", type=Path, help="test the staged UEFI loader on a disposable FAT32 image")
args = parser.parse_args()
OUT = Path(f"dist/{args.edition}").resolve()
if args.disk:
    MEDIA = ["-drive", f"file={args.disk.resolve()},format=raw,if=virtio,readonly=on", "-boot", "c"]
else:
    ISO, = OUT.glob("*.iso")
    MEDIA = ["-cdrom", str(ISO), "-boot", "d"]

GUEST = r'''set +e
exec >/dev/ttyS0 2>&1
for n in $(seq 1 120); do pgrep -x icewm >/dev/null && break; sleep 1; done
if ! pgrep -x icewm >/dev/null; then echo RELIFE_DESKTOP_FAIL; cat /home/student/.relife-x.log; systemctl poweroff; exit; fi
sleep 30
for n in $(seq 1 7); do
  awk '/^cpu /{printf "CPU_SAMPLE=%s,%s,%s,%s,%s,%s,%s,%s\n", $2,$3,$4,$5,$6,$7,$8,$9}' /proc/stat
  sleep 2
done
echo RELIFE_IDLE_BEGIN
pgrep -a icewm
cat /proc/meminfo
cat /proc/swaps
findmnt /run/live/medium
losetup -l
dpkg-query -W python3-tk xpdf
findmnt -n -o FSTYPE,OPTIONS /run/live/medium | grep -Eq '^tmpfs[[:space:]]+ro(,|$)' && echo RELIFE_TORAM_OK
[ "$(wc -l < /proc/swaps)" -eq 1 ] && echo RELIFE_SWAP_OK
awk '/MemTotal:/{t=$2} /MemFree:/{f=$2} /MemAvailable:/{a=$2} END {printf "IDLE_RAW_BYTES=%.0f\nIDLE_AVAILABLE_BYTES=%.0f\n",(t-f)*1024,(t-a)*1024}' /proc/meminfo
echo RELIFE_IDLE_END
sleep 5
as_student() { runuser -u student -- env HOME=/home/student DISPLAY=:0 XAUTHORITY=/home/student/.Xauthority "$@"; }
as_student pcmanfm --profile ReLife /home/student/Desktop/help.desktop >/tmp/relife-education.log 2>&1 &
for n in $(seq 1 20); do
  window=$(as_student xdotool search --onlyvisible --name '^ReLife.*T' | head -1)
  if [ -n "$window" ]; then
    echo RELIFE_EDUCATION_OK
    break
  fi
  sleep 1
done
cat /tmp/relife-education.log
echo RELIFE_EDUCATION_END
sleep 4
as_student pcmanfm --profile ReLife /home/student >/tmp/relife-files.log 2>&1 &
sleep 3
echo RELIFE_FILES_END
sleep 4
if command -v firefox-esr >/dev/null; then
as_student relife-firefox file:///usr/share/relife/start.html >/tmp/relife-browser.log 2>&1 &
sleep 30
echo RELIFE_BROWSER_BEGIN
pgrep -a firefox-esr
if pgrep -x firefox-esr >/dev/null; then echo RELIFE_BROWSER_OK; else cat /tmp/relife-browser.log; fi
awk '/MemTotal:/{t=$2} /MemFree:/{f=$2} /MemAvailable:/{a=$2} END {printf "BROWSER_RAW_BYTES=%.0f\nBROWSER_AVAILABLE_BYTES=%.0f\n",(t-f)*1024,(t-a)*1024}' /proc/meminfo
echo RELIFE_BROWSER_END
sleep 5
fi
echo RELIFE_SHUTDOWN_REQUEST
systemctl poweroff
'''

def screenshot(sock_path, target):
    try:
        with socket.socket(socket.AF_UNIX) as sock:
            sock.settimeout(5)
            sock.connect(str(sock_path))
            stream = sock.makefile('rwb', buffering=0)
            stream.readline()
            for request in ({'execute': 'qmp_capabilities'}, {'execute': 'screendump', 'arguments': {'filename': str(target)}}):
                stream.write((json.dumps(request) + '\n').encode())
                while True:
                    reply = json.loads(stream.readline())
                    if 'return' in reply or 'error' in reply:
                        break
        from PIL import Image
        with Image.open(target) as im:
            im.save(target.with_suffix('.png'))
        target.unlink()
    except Exception as error:
        print(f'screenshot: {error}', flush=True)

def boot(mode):
    log_path = OUT / f'qemu-{mode}.log'
    qmp = Path(f'/tmp/relife-{os.getpid()}-{mode}.sock')
    cmd = ['qemu-system-x86_64', '-m', str(args.ram), '-smp', '2', '-accel', 'tcg',
           *MEDIA, '-display', 'none', '-monitor', 'none',
           '-nic', 'none', '-serial', 'stdio', '-no-reboot', '-qmp', f'unix:{qmp},server=on,wait=off']
    if mode in ("uefi", "uefi-fat32"):
        variables = OUT / 'OVMF_VARS.fd'
        shutil.copy(args.ovmf_dir / 'OVMF_VARS_4M.fd', variables)
        cmd += ['-machine', 'q35', '-drive', f'if=pflash,format=raw,readonly=on,file={args.ovmf_dir / "OVMF_CODE_4M.fd"}',
                '-drive', f'if=pflash,format=raw,file={variables}']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    received = bytearray()
    def read():
        with log_path.open('wb') as log:
            while True:
                part = proc.stdout.read(1)
                if not part:
                    return
                log.write(part)
                log.flush()
                received.extend(part)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    stage = 0
    seen_idle = seen_browser = seen_education = seen_files = False
    deadline = time.monotonic() + 420
    heartbeat = time.monotonic()
    try:
        while proc.poll() is None and time.monotonic() < deadline:
            text = received.decode(errors='replace')
            if stage == 0 and 'relife login:' in text:
                proc.stdin.write(b'student\n'); proc.stdin.flush(); stage = 1
            elif stage == 1 and 'Password:' in text:
                proc.stdin.write(b'live\n'); proc.stdin.flush(); stage = 2
            elif stage == 2 and 'student@relife:' in text:
                encoded = base64.b64encode(GUEST.encode()).decode()
                for offset in range(0, len(encoded), 700):
                    redirect = ">" if offset == 0 else ">>"
                    chunk = encoded[offset:offset + 700]
                    proc.stdin.write(f"printf %s {chunk} {redirect} /tmp/relife-probe.b64\n".encode())
                proc.stdin.write(b"base64 -d /tmp/relife-probe.b64 | sudo -n bash\n")
                proc.stdin.flush(); stage = 3
            if not seen_idle and 'RELIFE_IDLE_END' in text:
                screenshot(qmp, OUT / f'{mode}-desktop.ppm'); seen_idle = True
            if not seen_education and 'RELIFE_EDUCATION_END' in text:
                screenshot(qmp, OUT / f'{mode}-education.ppm')
                seen_education = True
            if not seen_files and 'RELIFE_FILES_END' in text:
                screenshot(qmp, OUT / f'{mode}-files.ppm')
                seen_files = True
            if not seen_browser and 'RELIFE_BROWSER_END' in text:
                screenshot(qmp, OUT / f'{mode}-firefox.ppm'); seen_browser = True
            if time.monotonic() - heartbeat >= 30:
                print(f'{mode}, stage={stage}: {text[-1500:]}', flush=True)
                heartbeat = time.monotonic()
            time.sleep(.1)
    finally:
        if proc.poll() is None:
            proc.kill()
        code = proc.wait()
        reader.join(timeout=5)
        qmp.unlink(missing_ok=True)
    text = received.decode(errors='replace')
    metrics = {k: int(v) for k, v in re.findall(r'(IDLE_RAW_BYTES|IDLE_AVAILABLE_BYTES|BROWSER_RAW_BYTES|BROWSER_AVAILABLE_BYTES)=(\d+)', text)}
    cpu_ticks = [tuple(map(int, line.split(","))) for line in
                 re.findall(r"^CPU_SAMPLE=([0-9,]+)\r?$", text, re.M)]
    cpu_usage = []
    for before, after in zip(cpu_ticks, cpu_ticks[1:]):
        delta = [later - earlier for earlier, later in zip(before, after)]
        if sum(delta):
            cpu_usage.append(round(100 * (1 - (delta[3] + delta[4]) / sum(delta)), 2))
    result = {'mode': mode, 'idle_cpu_samples_percent': cpu_usage, 'desktop': seen_idle, 'firefox': 'RELIFE_BROWSER_OK' in text,
              'education': bool(re.search(r'^RELIFE_EDUCATION_OK\r?$', text, re.M)),
              'toram': 'RELIFE_TORAM_OK' in text, 'no_swap': 'RELIFE_SWAP_OK' in text,
              'shutdown': code == 0 and 'RELIFE_SHUTDOWN_REQUEST' in text, 'memory': metrics}
    # Memory target is reported separately; a boot pass cannot imply a memory pass.
    result['idle_700mb_available'] = metrics.get('IDLE_AVAILABLE_BYTES', 10**12) <= 700000000
    result['idle_700mb_raw'] = metrics.get('IDLE_RAW_BYTES', 10**12) <= 700000000
    print(json.dumps(result), flush=True)
    return result

results = [boot("uefi-fat32")] if args.disk else [boot("bios"), boot("uefi")]
report = "VALIDATION-WINDOWS-UEFI.json" if args.disk else "VALIDATION.json"
(OUT / report).write_text(json.dumps({'edition': args.edition, 'ram_mib': args.ram, 'hard_disks': int(bool(args.disk)), 'results': results,
    'limitations': ['Physical touchpad gestures require hardware validation.', 'No real-hardware shutdown, network browsing, media removal or pressure test.']}, indent=2))
required = ["desktop", "education", "toram", "no_swap", "shutdown"]
required += ["firefox"] if args.edition == "education" else ["idle_700mb_available"]
raise SystemExit(0 if all(all(result[key] for key in required) for result in results) else 1)
