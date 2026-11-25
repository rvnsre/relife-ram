#!/bin/sh
set -eu

# Only low-memory live machines need compressed swap. No partition or disk
# backing is assigned to the RAM device.
memory=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
[ "$memory" -le 1177600 ] || exit 0
modprobe zram
device=$(zramctl --find --algorithm lz4 --size 512M)
case "$device" in
    /dev/zram[0-9]*) ;;
    *) exit 1 ;;
esac
if ! mkswap "$device" || ! swapon --priority 100 "$device"; then
    zramctl --reset "$device"
    exit 1
fi
