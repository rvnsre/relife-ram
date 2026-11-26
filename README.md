# ReLife RAM

ReLife is a Debian 13 amd64 live system for older computers. IceWM and PCManFM
provide a bottom taskbar, a Start menu and labelled desktop shortcuts.
Both images use original ReLife artwork, a searchable Start menu and a light
theme shared by the native desktop panels and GTK applications.
The source of the wallpaper and icons is in `desktop/make-assets.py`.

| Image | Included | VM test configuration |
| --- | --- | --- |
| Extreme Lite | Offline Education Center, Firefox ESR, Xpdf, Mousepad and firmware focused on older Wi-Fi adapters | 1 GiB RAM, 2 vCPUs |
| Education | Extreme Lite’s tools plus graphical network and sound settings | 2 GiB RAM, 2 vCPUs |

On either image open **Təhsil mərkəzi** from the desktop or Start menu. The
bundled Azerbaijani library includes maths, physics, statistics, agronomy,
English and digital literacy exercises. The center also has cards with spaced
repetition, text export, lesson plans, a worksheet builder, a daily planner, science calculations and a focus
timer. Export work before closing the app or powering off. Live sessions use a
volatile overlay, load the compressed system into RAM and start without
persistence or physical disk swap. Extreme Lite enables up to 512 MiB of
compressed RAM swap on live systems with up to 1,150 MiB of usable RAM.
Education includes the full bundled Intel, Realtek and Qualcomm packages
alongside MediaTek and Broadcom firmware.

## AI and MCP

Select **Onlayn AI** to open ChatGPT, Claude or Gemini in
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
mtools curl ca-certificates python3 cmake g++ pkg-config libudev-dev libinput-dev
libpugixml-dev libcairo2-dev libx11-dev libxtst-dev libxrandr-dev libxi-dev libglib2.0-dev librsvg2-bin`. Run `sudo bash build.sh extreme-lite` or
`sudo bash build.sh education`. The corresponding ISO and SHA-256 digest are
written to `dist/<edition>/`. Both images use an XZ boot archive and 1 MiB
SquashFS blocks with the x86 compression filter.

On a Debian host with QEMU, OVMF and Pillow run `python3 tests/boot.py
extreme-lite --ram 1024` or `python3 tests/boot.py education --ram 2048`.
CI captures BIOS and UEFI graphics, checks the desktop and Education Center
while Firefox loads a page from the VM's test network, and verifies shutdown.
The 1 GiB Extreme Lite test checks that RAM-only swap is active and that
MemTotal minus MemAvailable stays within 700,000,000 bytes at idle.
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

## Touchpad and power

Tap anywhere on the active touchpad surface with one finger for a left click
or two fingers for a right click. The physical buttons remain available. Use
two fingers to scroll, swipe three fingers left or right to switch apps, and
swipe four fingers up or down to adjust the volume. Three- and four-finger
gestures require a touchpad that reports the corresponding contact count.

Use **Başla → Kompüteri söndür → Söndür** for normal systemd poweroff.
The CI test activates the same graphical dialog and verifies that the VM
exits. Firmware and ACPI on physical computers must be tested separately.

## Network and window selection

Select **Şəbəkə** from the taskbar or Start and open **Şəbəkə seç** to
connect to Wi-Fi or to a wired profile. The network panel also provides a
shortcut to open the network's sign-in page. For a supported touchpad, swipe
three fingers left or right to open **Açıq pəncərələr**. Swipe again to highlight
a different window, and select **Keç**, press Enter or double-click the window's
name. **Super+Tab** and **Başla → Açıq pəncərələr** open the same picker.

See [the browser baseline](docs/audit/BROWSER.md) for the online VM test and
the remaining physical-device checks.
