# ReLife RAM

ReLife is a Debian 13 amd64 live system for older computers. IceWM and PCManFM
provide a bottom taskbar, a Start menu and labelled desktop shortcuts.

| Image | Included | VM test configuration |
| --- | --- | --- |
| Extreme Lite | Offline Education Center, Xpdf, Mousepad, XTerm, ALSA and NetworkManager's text UI | 1 GiB RAM, 2 vCPUs |
| Education | Extreme Lite's offline tools plus Firefox ESR, graphical network settings, PulseAudio and on-demand AI web links | 2 GiB RAM, 2 vCPUs |

On either image open **Təhsil mərkəzi** from the desktop or Start menu. The
bundled Azerbaijani library includes maths, physics, statistics, agronomy,
English and digital literacy exercises. The center also has cards with spaced
repetition, text export, lesson plans, a worksheet builder, a daily planner, science calculations and a focus
timer. Export work before closing the app or powering off. Live sessions use a
volatile overlay, load the compressed system into RAM and start without
persistence or physical disk swap.

## AI and MCP

In Education, select **Onlayn AI** to open ChatGPT, Claude or Gemini in
Firefox. The launcher opens the provider only after confirmation. It does not
attach local lessons, notes or documents. Provider accounts and services are
managed by their respective providers.

Both images include a separate local stdio MCP server. Configure a compatible
client to run `/usr/local/bin/relife-mcp` with additional repeated `--allow`
arguments for the tools you want to expose:

- `education.search_library` searches only the bundled, public lesson data.
- `education.get_lesson` reads a bundled lesson by its public ID.
- `education.convert_units` converts supported length, mass and time units.

With zero permissions, discovery returns zero tools. The server exposes no
network listener, user-file access, code execution or writes. The AI web links
and the local MCP server are separate entry points. The browser launchers
do not connect the provider to MCP.

## Build and validate

On disposable Debian 13, install `live-build debootstrap xorriso squashfs-tools
isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin grub-common dosfstools
mtools curl ca-certificates`. Run `sudo bash build.sh extreme-lite` or
`sudo bash build.sh education`. The corresponding ISO and SHA-256 digest are
written to `dist/<edition>/`.

On a Debian host with QEMU, OVMF and Pillow run `python3 tests/boot.py
extreme-lite --ram 1024` or `python3 tests/boot.py education --ram 2048`.
CI captures BIOS and UEFI graphics, checks the desktop and Education Center
with networking disconnected, and verifies shutdown. The Extreme Lite gate
uses MemTotal minus MemAvailable and checks it against 700,000,000 bytes.
The result JSON also records MemTotal minus MemFree, which includes reclaimable
cache, and states the VM RAM allocation. There is a separate FAT32 boot test.
Historical measurements remain in [VALIDATION.md](VALIDATION.md).

For the Windows USB-free UEFI flow, see [Windows Boot Setup](windows/README.md).
The image uses unsigned amd64 EFI boot code. Physical firmware, Wi-Fi and
touchpad support depend on the device. Student login on the live console is
`student` with password `live`.

Project scripts and assets are GPL-3.0-only. Bundled Debian packages retain
their original licenses.

See the [education roadmap](docs/EDUCATION-ROADMAP.md) for the status of all
150 requirements.
