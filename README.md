# ReLife RAM v0.2.0 — education desktop candidate

A small Debian 13 amd64 live system with a familiar bottom taskbar, Start menu,
large labelled desktop icons, file manager, text editor and preinstalled Firefox ESR.
The desktop uses IceWM and PCManFM, with tiny project-owned XPM icons and flat colours.
It does not include Windows code or a heavy desktop environment.

## Build

On disposable Debian 13: install live-build, debootstrap, xorriso, squashfs-tools,
isolinux, syslinux-common, grub-pc-bin, grub-efi-amd64-bin, dosfstools, mtools, curl
and ca-certificates; run `sudo bash build.sh`. GitHub Actions builds the actual ISO.
The `overlay/` directory must be alongside `build.sh`.

The build downloads Touchégg 2.0.18 from its official GitHub release, prints its
SHA-256 and installs its dependencies from Debian. Other software is from Debian.
Project scripts/assets are GPL-3.0-only; bundled packages retain their own licenses.

## Changes

- Simple Start menu: Internet, Files, Write, Network, Sound, Help, Restart, Power off.
- Super opens Start, Super+E opens Files, Super+B opens Firefox, Alt+Tab switches apps.
- Power commands call `sudo -n systemctl poweroff/reboot`. `noeject` removes the live
  medium removal prompt. Tests require the virtual machine to actually exit on shutdown.
- Tap anywhere for left-click, two-finger tap for right-click, two-finger scrolling.
- Three-finger left/right swipes switch applications; four-finger up/down swipes
  change volume. Existing physical left/right buttons keep their default behavior.
  Four-finger operation requires hardware/driver support. Physical gestures cannot
  be certified by a VM; no promise is made for old two-contact touchpads.
- Firefox is preinstalled. The launcher selects small content-process pools and
  cache sizes based on RAM/CPU, avoids disk cache/prefetch/background studies, reduces
  animation, and blocks unsolicited autoplay. Site isolation, sandboxing, TLS and
  Safe Browsing remain at Firefox defaults. No universal speed multiplier is claimed.
  Preferences are written to `~/.mozilla/firefox/relife/user.js` and hardware decisions
  are recorded in `relife-hardware.json`. Modern isolated sites may create additional
  processes beyond the nominal pool; these are not a hard total-process or RAM cap.

## Memory, boot and validation

The original 700,000,000-byte idle target includes the compressed system copied
into RAM. Firefox's files add to that image even when the browser is closed, and
an open browser uses additional RAM. This revision must be measured afresh.
Do not reuse v0.1.0's measurements as v0.2.0 results.

CI records separate desktop-idle and browser-open samples, both
MemTotal minus MemAvailable and the stricter MemTotal minus MemFree. It captures
real desktop/browser screenshots and checks BIOS, UEFI and actual ACPI shutdown.
A boot/shutdown pass does not imply that the memory target passed. Consult
`dist/VALIDATION.json` and serial logs in the validation artifact.

`toram=filesystem.squashfs`, no persistence, no physical-disk swap and volatile
journals remain configured. No internal disks are attached in VM tests.
Physical hardware shutdown, touchpad gestures, disk-swap exclusion with an attached
disk, Wi-Fi/graphics firmware, live-media removal and memory pressure require tests.
Automatic firmware bundles remain disabled to control RAM image size.

User data is volatile unless explicitly exported. Student login is `student` with
the standard live password `live`; tty1 logs in automatically. No Windows installer
or USB-free installation is included. No validated v0.2.0 release exists until its
build/test evidence is published. See historical v0.1.0 results in `VALIDATION.md`.
