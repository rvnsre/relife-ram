#!/bin/bash
# Simulate firmware selecting the staged loader, using only a disposable GPT disk image.
set -euo pipefail
cd "$(dirname "$0")/.."
stage=dist/extreme-lite/windows-stage
image=dist/extreme-lite/windows-test.img
truncate -s 1200M "$image"
printf 'label: gpt\nstart=2048, size=2400000, type=uefi\n' | sfdisk "$image"
fat="$image@@1048576"
mformat -i "$fat" -F -T 2400000 ::
mmd -i "$fat" ::EFI ::EFI/ReLife ::EFI/ReLife/live ::EFI/BOOT
mcopy -i "$fat" "$stage/ReLife.efi" ::EFI/BOOT/BOOTX64.EFI
mcopy -i "$fat" "$stage/ReLife.efi" ::EFI/ReLife/ReLife.efi
mcopy -i "$fat" "$stage/live/"* ::EFI/ReLife/live/
printf 'ReLife USB-free boot media v1\n' | mcopy -i "$fat" - ::EFI/ReLife/relife-media
