#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
edition=extreme-lite
out="dist/$edition"
source="build/$edition/binary/live"
stage="$out/windows-stage"
mkdir -p "$stage/live"
kernel=("$source"/vmlinuz-*)
initrd=("$source"/initrd.img-*)
[[ ${#kernel[@]} == 1 && ${#initrd[@]} == 1 ]]
install -m 0644 "${kernel[0]}" "$stage/live/vmlinuz"
install -m 0644 "${initrd[0]}" "$stage/live/initrd.img"
install -m 0644 "$source/filesystem.squashfs" "$stage/live/"
cat > "$stage/grub.cfg" <<'GRUB'
set timeout=3
set default=0
terminal_output console
menuentry 'ReLife RAM' {
    if search --no-floppy --file --set=root /EFI/ReLife/relife-media; then
        probe --fs-uuid --set=relife_uuid ($root)
        linux /EFI/ReLife/live/vmlinuz boot=live components live-media=/dev/disk/by-uuid/${relife_uuid} live-media-path=/EFI/ReLife/live toram=filesystem.squashfs noeject nopersistence swap=false username=student hostname=relife locales=C.UTF-8 console=tty0 console=ttyS0,115200n8
        initrd /EFI/ReLife/live/initrd.img
    else
        echo 'ReLife boot files were not found.'
        sleep 5
    fi
}
GRUB
module_dir=()
if [[ -n ${GRUB_MODULE_DIR:-} ]]; then
  module_dir+=(--directory="$GRUB_MODULE_DIR")
fi
grub-mkstandalone --format=x86_64-efi "${module_dir[@]}" --locales="" --fonts="" \
  --modules="part_gpt part_msdos fat normal linux search search_fs_file probe echo sleep" \
  --output="$stage/ReLife.efi" "boot/grub/grub.cfg=$stage/grub.cfg"
python3 - "$stage" "$out/ReLife-Windows-UEFI-Payload.zip" <<'PY'
import pathlib
import sys
import zipfile

stage, out = map(pathlib.Path, sys.argv[1:])
names = ("ReLife.efi", "live/vmlinuz", "live/initrd.img", "live/filesystem.squashfs")
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as target:
    for name in names:
        target.write(stage / name, name)
PY
(cd "$out" && sha256sum ReLife-Windows-UEFI-Payload.zip >> SHA256SUMS)
