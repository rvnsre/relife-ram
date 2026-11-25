# ReLife RAM — v0.1.0 engineering prototype

A free education-oriented RAM-resident Linux prototype, inspired by PorteuX. Debian 13 amd64, IceWM, Xorg. Not a validated release.

## Build
On a disposable Debian 13 VM with internet and at least 20 GB free disk:

```sh
sudo apt update
sudo apt install live-build debootstrap xorriso squashfs-tools isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin dosfstools mtools
sudo ./build.sh
```

Or push these files into a new GitHub repository on `main`, enable Actions and run **Build ReLife RAM ISO**. Download its artifact. CI builds a hybrid BIOS/UEFI ISO and boots it in QEMU with no hard disk. See Actions logs and artifact VALIDATION.txt for actual results. No successful build is claimed until CI completes.

## Boot and test
Start in a disposable VM (2 GB RAM, no hard disk), boot the ISO, log in to the live console and run `startx`. Use `relife-check` from xterm. The `toram` boot flag requests copying live media into memory; no persistence is configured and disk swap is not requested. Confirm actual mounts and swap before claiming zero HDD I/O. Do not use on real hardware until tested.

## Acceptance criteria
- 700,000,000 bytes maximum idle system memory, including RAM-resident image; measure `MemTotal - MemAvailable` and independently account for tmpfs/image storage without double counting. Record both and test under memory pressure. This script's check is only a preliminary estimate, not proof of the cap.
- Boot on 2 GB RAM with BIOS and UEFI; verify no physical-disk dependency after boot, no swap partitions and no automatic mounting of internal disks.
- Test on Intel/AMD old graphics and Wi-Fi. Firmware and browser support are not complete.
- Browser and educational apps are separate future modules; their memory is additional. User data is volatile unless explicitly exported. Shutdown loses unsaved work.
- No Windows installer yet. USB-free internal-disk boot requires a separate validated bootloader integration, backup and recovery, BitLocker/Secure Boot checks, and explicit consent. Never modify partitions in the prototype.
- This repository has not yet been built or boot-tested. No ISO or measured performance is included.

## Validation and license
700 MB means 700,000,000 bytes, including the compressed system in RAM. CI reports both MemTotal minus MemAvailable and the more conservative MemTotal minus MemFree; the latter gates the memory target. No measurement is claimed before successful execution. The QEMU probe runs only with the RELIFE_CI DMI serial. Real hardware, removing boot media, pressure testing, and a disk containing swap remain unvalidated. BIOS/UEFI test logs are uploaded even on failure. No release is automatically published.

Original project scripts are GPL-3.0-only (see LICENSE). Debian packages retain their own licenses. Binary redistribution must preserve package copyright notices and corresponding-source obligations; the initial CI artifact is experimental, not a completed distribution compliance audit.

References: [live-boot](https://manpages.debian.org/trixie/live-boot-doc/live-boot.7.en.html), [live-build](https://manpages.debian.org/trixie/live-build/lb_config.1.en.html). Local swap is opt-in in live-boot; this configuration explicitly uses swap=false and masks swap.target. Internal disks are not automatically mounted by this desktop configuration.

To keep the RAM image small, automatic firmware bundles are disabled. Devices requiring proprietary firmware (especially Wi-Fi/graphics) need separately tested modules in a future revision. Package copyright notices are retained.
