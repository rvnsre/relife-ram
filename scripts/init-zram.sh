#!/bin/sh
set -eu

# Only low-memory live machines need compressed swap. No partition or disk
# backing is assigned to the RAM device.
memory=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
[ "$memory" -le 1177600 ] || exit 0
# Avoid allocating huge pages for sparsely used desktop mappings on 1 GiB.
thp=/sys/kernel/mm/transparent_hugepage/enabled
[ ! -w "$thp" ] || printf 'never\n' > "$thp"
device=/dev/zram0
if awk -v device="$device" '$1 == device {found=1} END {exit !found}' /proc/swaps; then
    exit 0
fi
modprobe zram num_devices=1
# The module can finish loading before udev has made its device ready.
udevadm wait --timeout=10 "$device"
zramctl --algorithm lz4 --size 512M "$device"
if ! mkswap "$device" || ! swapon --priority 100 "$device"; then
    zramctl --reset "$device"
    exit 1
fi
