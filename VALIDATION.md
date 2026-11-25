ReLife RAM experimental validation — 2026-11-25

Public repository: https://github.com/rvnsre/relife-ram
Downloaded and locally tested ISO source commit: e70c6d98aaeb255334aa7b58f5aa7d324fd43890
ISO SHA-256: ec6b347f7c451197e7db4989040d43d791f2d6de4d5718c670bfbec7dc992495
ISO build: https://github.com/rvnsre/relife-ram/actions/runs/45576986307
CI ISO and diagnostic artifact: https://github.com/rvnsre/relife-ram/actions/runs/45576986307/artifacts/15006446786
Subsequent Xorg launcher/startup-log change: 0b2d78b6d0df44023c4905fff101be784bab40d8
Subsequent build: https://github.com/rvnsre/relife-ram/actions/runs/45579277228

Local QEMU BIOS test: 2 GiB RAM, 2 virtual CPUs, TCG, no hard disk.
PASS: Linux boots, student/live login works, Xorg and icewm-session/icewm run.
PASS: /run/live/medium is a read-only tmpfs; the SquashFS image was copied into RAM.
PASS in diskless test: /proc/swaps empty, SwapTotal/SwapFree 0.
Sample after allowing desktop startup:
MemTotal 2020960 KiB; MemFree 1331492 KiB; MemAvailable 1469176 KiB.
MemTotal - MemAvailable = 565026816 bytes (565.03 decimal MB).
MemTotal - MemFree = 706015232 bytes (706.02 decimal MB).
Shmem = 315332 KiB (includes the RAM image).
The 565 MB figure already counts non-reclaimable tmpfs image memory; do not add Shmem again.
The 706 MB conservative figure also counts reclaimable file cache, including diagnostic reads.
A strict all-resident-pages <= 700000000 byte claim is NOT established.

CI combined BIOS/UEFI probe for e70c6d9 FAILED: no completed probe report;
UEFI remained after OVMF DVD start until the 600-second timeout.
Local UEFI attempt also did not reach a Linux serial login during the observation window.
This does not prove failure on all UEFI hardware, but UEFI support is NOT validated.
The CI memory gate has NOT passed. Local evidence is independent from CI.
No physical hardware, media-ejection, memory-pressure or attached-disk-with-swap validation.
No firmware bundles, browser, educational suite or Windows/USB-free installer.
Unsaved user files are volatile.
No alpha release was published because these acceptance gaps remain.
