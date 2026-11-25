#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo on Debian 13'; exit 1; }
cd "$(dirname "$0")"
mkdir -p build
cd build
lb clean --purge || true
lb config --mode debian --distribution trixie --architectures amd64 --binary-image iso-hybrid --bootloaders "syslinux grub-efi" --firmware-chroot false --firmware-binary false --apt-indices false --debootstrap-options "--variant=minbase" --archive-areas 'main contrib non-free-firmware' --apt-recommends false --debian-installer none --memtest none --bootappend-live 'boot=live components toram=filesystem.squashfs nopersistence swap=false username=student hostname=relife console=tty0 console=ttyS0,115200n8' --chroot-squashfs-compression-type xz --iso-volume RELIFE_RAM
mkdir -p config/package-lists config/includes.chroot/etc/systemd/journald.conf.d config/includes.chroot/etc/skel config/includes.chroot/usr/local/bin config/hooks/live
cat > config/package-lists/relife.list.chroot <<'PKG'
live-boot
live-config
live-config-systemd
linux-image-amd64
systemd-sysv
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
sudo
PKG
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
  exec startx
fi
PROFILE
cat > config/includes.chroot/etc/systemd/system/relife-probe.service <<'SERVICE'
[Unit]
Description=Opt-in CI desktop memory probe
After=systemd-user-sessions.service
ConditionVirtualization=qemu
[Service]
Type=oneshot
ExecStart=/usr/local/bin/relife-probe
StandardOutput=tty
TTYPath=/dev/ttyS0
[Install]
WantedBy=multi-user.target
SERVICE
mkdir -p config/includes.chroot/etc/systemd/system/multi-user.target.wants
ln -sf ../relife-probe.service config/includes.chroot/etc/systemd/system/multi-user.target.wants/relife-probe.service
cat > config/includes.chroot/usr/local/bin/relife-probe <<'PROBE'
#!/bin/bash
set -eu
[ "$(cat /sys/class/dmi/id/product_serial)" = RELIFE_CI ] || exit 0
for i in $(seq 1 120); do pgrep -x icewm >/dev/null && break; sleep 2; done
pgrep -x icewm >/dev/null || { echo RELIFE_DESKTOP_FAIL; exit 1; }
sleep 60
echo RELIFE_REPORT_BEGIN
cat /proc/cmdline
cat /proc/meminfo
cat /proc/swaps
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
losetup -l
# Raw used includes all cache, including the compressed image. Conservative cap.
awk '/MemTotal:/{t=$2} /MemFree:/{f=$2} /MemAvailable:/{a=$2} END {printf "RAW_USED_BYTES=%.0f\nAVAILABLE_USED_BYTES=%.0f\n",(t-f)*1024,(t-a)*1024; if ((t-f)*1024 <= 700000000) print "RELIFE_MEMORY_PASS"; else print "RELIFE_MEMORY_FAIL"}' /proc/meminfo
[ "$(wc -l < /proc/swaps)" -eq 1 ] && echo RELIFE_SWAP_PASS
echo RELIFE_REPORT_END
systemctl poweroff
PROBE
chmod +x config/includes.chroot/usr/local/bin/relife-probe
cat > config/hooks/live/0900-trim.hook.chroot <<'TRIM'
#!/bin/sh
set -eu
printf '\nPre-trim disk usage:\n'
du -x -h -d 2 /usr /var | sort -h | tail -35
apt-get clean
rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /usr/share/man/* /usr/share/locale/*
find /usr/share/doc -type f ! -name copyright -delete
printf '\nPost-trim disk usage:\n'
du -x -h -d 2 /usr /var | sort -h | tail -35
TRIM
chmod +x config/hooks/live/0900-trim.hook.chroot
lb build
mkdir -p ../dist
cp live-image-amd64.hybrid.iso ../dist/relife-ram-v0.1.0-amd64.iso
cd ../dist
sha256sum *.iso > SHA256SUMS
