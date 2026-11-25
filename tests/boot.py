"""Actual ISO boot, desktop/browser RAM samples, screenshots and ACPI shutdown."""
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

OUT = Path('dist').resolve()
ISO = next(OUT.glob('*.iso'))

GUEST = r'''set +e
exec >/dev/ttyS0 2>&1
for n in $(seq 1 120); do pgrep -x icewm >/dev/null && break; sleep 1; done
if ! pgrep -x icewm >/dev/null; then echo RELIFE_DESKTOP_FAIL; cat /home/student/.relife-x.log; systemctl poweroff; exit; fi
sleep 30
echo RELIFE_IDLE_BEGIN
pgrep -a icewm
cat /proc/meminfo
cat /proc/swaps
findmnt /run/live/medium
losetup -l
dpkg-query -W firefox-esr touchegg
awk '/MemTotal:/{t=$2} /MemFree:/{f=$2} /MemAvailable:/{a=$2} END {printf "IDLE_RAW_BYTES=%.0f\nIDLE_AVAILABLE_BYTES=%.0f\n",(t-f)*1024,(t-a)*1024}' /proc/meminfo
echo RELIFE_IDLE_END
sleep 5
runuser -u student -- env HOME=/home/student DISPLAY=:0 XAUTHORITY=/home/student/.Xauthority relife-firefox file:///usr/share/relife/start.html >/tmp/relife-browser.log 2>&1 &
sleep 40
echo RELIFE_BROWSER_BEGIN
pgrep -a firefox-esr
if pgrep -x firefox-esr >/dev/null; then echo RELIFE_BROWSER_OK; else cat /tmp/relife-browser.log; fi
awk '/MemTotal:/{t=$2} /MemFree:/{f=$2} /MemAvailable:/{a=$2} END {printf "BROWSER_RAW_BYTES=%.0f\nBROWSER_AVAILABLE_BYTES=%.0f\n",(t-f)*1024,(t-a)*1024}' /proc/meminfo
echo RELIFE_BROWSER_END
sleep 5
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
    cmd = ['qemu-system-x86_64', '-m', '2048', '-smp', '2', '-accel', 'tcg',
           '-cdrom', str(ISO), '-boot', 'd', '-display', 'none', '-monitor', 'none',
           '-serial', 'stdio', '-no-reboot', '-qmp', f'unix:{qmp},server=on,wait=off']
    if mode == 'uefi':
        variables = OUT / 'OVMF_VARS.fd'
        shutil.copy('/usr/share/OVMF/OVMF_VARS_4M.fd', variables)
        cmd += ['-machine', 'q35', '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
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
    seen_idle = seen_browser = False
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
                proc.stdin.write(f'echo {encoded} | base64 -d | sudo -n bash\n'.encode())
                proc.stdin.flush(); stage = 3
            if not seen_idle and 'RELIFE_IDLE_END' in text:
                screenshot(qmp, OUT / f'{mode}-desktop.ppm'); seen_idle = True
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
    result = {'mode': mode, 'desktop': seen_idle, 'firefox': 'RELIFE_BROWSER_OK' in text,
              'shutdown': code == 0 and 'RELIFE_SHUTDOWN_REQUEST' in text, 'memory': metrics}
    # Memory target is reported separately; a boot pass cannot imply a memory pass.
    result['idle_700mb_available'] = metrics.get('IDLE_AVAILABLE_BYTES', 10**12) <= 700000000
    result['idle_700mb_raw'] = metrics.get('IDLE_RAW_BYTES', 10**12) <= 700000000
    print(json.dumps(result), flush=True)
    return result

results = [boot('bios'), boot('uefi')]
(OUT / 'VALIDATION.json').write_text(json.dumps({'ram_mib': 2048, 'hard_disks': 0, 'results': results,
    'limitations': ['Physical touchpad gestures require hardware validation.', 'No real-hardware shutdown, network browsing, media removal or pressure test.']}, indent=2))
raise SystemExit(0 if all(r['desktop'] and r['firefox'] and r['shutdown'] for r in results) else 1)
