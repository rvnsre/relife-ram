#!/bin/bash
set -euo pipefail
destination=$(realpath "$1")
commit=fc30d316e163f4504043353d6610e670ce5c6439
digest=014e566cbdb44caea80afad15dfa753ecebc7a2b92d2bc49c30892cd0acc55f0
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
curl --fail --location --retry 3 --max-time 90 \
  "https://codeload.github.com/JoseExposito/touchegg/tar.gz/$commit" -o "$work/source.tar.gz"
printf '%s  %s\n' "$digest" "$work/source.tar.gz" | sha256sum --check
mkdir "$work/source"
tar -xzf "$work/source.tar.gz" -C "$work/source" --strip-components=1
cmake -S "$work/source" -B "$work/build" -DCMAKE_BUILD_TYPE=MinSizeRel \
  -DCMAKE_INSTALL_PREFIX=/usr -DAUTO_COLORS=OFF -DUSE_SYSTEMD=OFF
cmake --build "$work/build" --parallel 2
install -Dm755 "$work/build/touchegg" "$destination/usr/bin/touchegg"
strip --strip-unneeded "$destination/usr/bin/touchegg"
if [ -f "$work/source/LICENSE" ]; then
  install -Dm644 "$work/source/LICENSE" "$destination/usr/share/doc/touchegg/copyright"
else
  install -Dm644 "$work/source/COPYING" "$destination/usr/share/doc/touchegg/copyright"
fi
