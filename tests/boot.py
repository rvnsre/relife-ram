"""Boot the actual hybrid ISO with no hard disk and collect serial evidence."""
import pathlib, subprocess, sys
out = pathlib.Path("dist")
iso = next(out.glob("*.iso"))
failed = False
for mode in ("bios", "uefi"):
    cmd = ["qemu-system-x86_64", "-m", "2048", "-accel", "tcg", "-smp", "2",
           "-cdrom", str(iso), "-boot", "d", "-display", "none", "-monitor", "none",
           "-serial", "stdio", "-no-reboot", "-smbios", "type=1,serial=RELIFE_CI"]
    if mode == "uefi":
        firmware = pathlib.Path("/usr/share/OVMF/OVMF_CODE_4M.fd")
        cmd += ["-drive", f"if=pflash,format=raw,readonly=on,file={firmware}"]
    with (out / f"qemu-{mode}.log").open("wb") as log:
        try:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=600)
            ok = result.returncode == 0
        except subprocess.TimeoutExpired:
            ok = False
    text = (out / f"qemu-{mode}.log").read_text(errors="replace")
    ok = ok and all(x in text for x in ("RELIFE_REPORT_END", "RELIFE_MEMORY_PASS", "RELIFE_SWAP_PASS"))
    print(f"{mode}: {'PASS' if ok else 'FAIL (inspect serial log)'}", flush=True)
    failed |= not ok
(out / "VALIDATION.txt").write_text(
    "QEMU BIOS/UEFI desktop, no hard disk, 2 GiB RAM, TCG.\n"
    "Memory gate: MemTotal - MemFree <= 700,000,000 bytes (conservative, includes cache).\n"
    f"Overall: {'FAILED; not release-ready' if failed else 'PASSED; hardware and media-removal tests still pending'}\n"
    "No physical hardware or memory-pressure validation performed.\n")
sys.exit(1 if failed else 0)
