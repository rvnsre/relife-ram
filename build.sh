#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo on Debian 13'; exit 1; }
cd "$(dirname "$0")"
edition=${1:-extreme-lite}
case "$edition" in
  extreme-lite) name=ReLife-Extreme-Lite ;;
  education) name=ReLife-Education ;;
  *) echo 'Usage: build.sh [extreme-lite|education]' >&2; exit 2 ;;
esac
mkdir -p "build/$edition"
cd "build/$edition"
lb clean --purge || true
lb config --mode debian --distribution trixie --architectures amd64 --binary-image iso-hybrid --bootloaders "syslinux grub-efi" --firmware-chroot false --firmware-binary false --apt-indices false --debootstrap-options "--variant=minbase" --archive-areas 'main contrib non-free-firmware' --apt-recommends false --debian-installer none --memtest none --bootappend-live 'boot=live components toram=filesystem.squashfs noeject nopersistence swap=false username=student hostname=relife locales=C.UTF-8 console=tty0 console=ttyS0,115200n8' --chroot-squashfs-compression-type xz --checksums none --uefi-secure-boot disable --iso-volume RELIFE_RAM
mkdir -p config/package-lists config/includes.chroot/etc/systemd/journald.conf.d config/includes.chroot/etc/skel config/includes.chroot/usr/local/bin config/hooks/live
cat > config/package-lists/relife.list.chroot <<'PKG'
live-boot
live-config
live-config-systemd
user-setup
xauth
x11-xserver-utils
keyboard-configuration
linux-image-amd64
systemd-sysv
xserver-xorg
xserver-xorg-core
xserver-xorg-input-libinput
xserver-xorg-video-vesa
xserver-xorg-video-fbdev
xinit
icewm
xterm
pcmanfm
fonts-dejavu-core
network-manager
wpasupplicant
iproute2
ca-certificates
alsa-utils
pulseaudio
pavucontrol
network-manager-gnome
mousepad
bc
mupdf
xdg-utils
xdotool
python3
python3-tk
curl
sudo
PKG
if [ "$edition" = education ]; then
  echo firefox-esr >> config/package-lists/relife.list.chroot
fi
mkdir -p config/bootloaders/grub-pc
cat > config/bootloaders/grub-pc/config.cfg <<'GRUB'
set default=0
set timeout=5
terminal_output console
GRUB
cat > config/includes.chroot/etc/skel/.xinitrc <<'X'
exec icewm-session
X
cat > config/includes.chroot/etc/systemd/journald.conf.d/ram.conf <<'J'
[Journal]
Storage=volatile
RuntimeMaxUse=16M
J
cat > config/includes.chroot/usr/local/bin/relife-check <<'CHECK'
#!/bin/sh
set -eu
awk '/MemTotal:/{t=$2} /MemAvailable:/{a=$2} END {printf "RAM used (MemTotal - MemAvailable): %.1f MiB\n", (t-a)/1024; if((t-a)*1024>700000000) exit 1}' /proc/meminfo
printf '\nSwap:\n'; cat /proc/swaps
printf '\nMounts:\n'; findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
CHECK
chmod +x config/includes.chroot/usr/local/bin/relife-check
# Disable swap activation and hibernation even if a disk is later attached.
mkdir -p config/includes.chroot/etc/systemd/system config/includes.chroot/etc/skel
for unit in swap.target sleep.target suspend.target hibernate.target hybrid-sleep.target; do
  ln -sf /dev/null "config/includes.chroot/etc/systemd/system/$unit"
done
cat > config/includes.chroot/etc/skel/.bash_profile <<'PROFILE'
if [ -z "${DISPLAY:-}" ] && [ "$(tty)" = /dev/tty1 ]; then
  exec startx >> "$HOME/.relife-x.log" 2>&1
fi
PROFILE
# Project-owned lightweight UI, browser profile and touchpad settings.
cp -a ../../overlay/. config/includes.chroot/
if [ "$edition" = extreme-lite ]; then
  skel=config/includes.chroot/etc/skel
  rm -f "$skel/Desktop/internet.desktop" config/includes.chroot/usr/share/applications/relife-firefox.desktop
  sed -i '/relife-firefox/d' "$skel/.icewm/"{menu,toolbar,keys}
fi
cat > config/hooks/live/0200-firefox.hook.chroot <<'GESTURES'
#!/bin/sh
set -eu
test ! -x /usr/bin/firefox-esr && exit 0
mkdir -p /usr/lib/firefox-esr/distribution
ln -sf /etc/firefox/policies/policies.json /usr/lib/firefox-esr/distribution/policies.json
GESTURES
chmod +x config/hooks/live/0200-firefox.hook.chroot
cat > config/hooks/live/0900-trim.hook.chroot <<'TRIM'
#!/bin/sh
set -eu
printf '\nPre-trim disk usage:\n'
du -x -h -d 2 /usr /var | sort -h | tail -35
apt-get clean
rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /usr/share/man/*
find /usr/share/doc -type f ! -name copyright -delete
printf '\nPost-trim disk usage:\n'
du -x -h -d 2 /usr /var | sort -h | tail -35
TRIM
chmod +x config/hooks/live/0900-trim.hook.chroot
cat > config/hooks/live/0999-timeout.hook.binary <<'MENU'
#!/bin/sh
set -eu
sed -i 's/^timeout .*/timeout 50/' isolinux/isolinux.cfg
MENU
chmod +x config/hooks/live/0999-timeout.hook.binary
lb build
out="../../dist/$edition"
mkdir -p "$out"
cp live-image-amd64.hybrid.iso "$out/$name-x86_64.iso"
cp chroot/var/lib/dpkg/status "$out/package-status.txt"
(cd "$out" && sha256sum "$name-x86_64.iso" > SHA256SUMS)
