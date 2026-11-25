#!/bin/sh
set -eu

# Keep Wi-Fi 4/5 firmware, Realtek adapters and the Intel AX200/201 and QCA6390
# families in the image copied into RAM. Education retains the full packages.
firmware=/usr/lib/firmware
find "$firmware" -maxdepth 1 -name 'iwlwifi-*' \( \
    -name 'iwlwifi-bz-*' -o -name 'iwlwifi-gl-*' -o -name 'iwlwifi-ma-*' -o \
    -name 'iwlwifi-so-*' -o -name 'iwlwifi-ty-*' \) -delete
find "$firmware/ath11k" -mindepth 1 -maxdepth 1 ! -name QCA6390 -exec rm -rf -- {} +
rm -rf -- "$firmware/ath12k" "$firmware/ath10k/WCN3990"

# Retain the older Intel fallback files whenever the exact version named by
# the packaged kernel is absent. Otherwise keep that version for each family.
set -- /lib/modules/*
[ "$#" -eq 1 ] && [ -f "$1/modules.dep.bin" ] || exit 0
expected=$(modinfo -k "${1##*/}" -F firmware iwlwifi) || exit 0
for latest in $expected; do
    case "$latest" in iwlwifi-*.ucode) ;; *) continue ;; esac
    [ -f "$firmware/$latest" ] || continue
    latest_api=${latest%.ucode}
    latest_api=${latest_api##*-}
    case "$latest_api" in ''|*[!0-9]*) continue ;; esac
    for candidate in "$firmware/${latest%-*}"-*.ucode; do
        [ -f "$candidate" ] || continue
        candidate_api=${candidate%.ucode}
        candidate_api=${candidate_api##*-}
        case "$candidate_api" in ''|*[!0-9]*) continue ;; esac
        if [ "$candidate_api" -lt "$latest_api" ] &&
            ! printf '%s\n' "$expected" | grep -Fxq "${candidate##*/}"; then
            rm -- "$candidate"
        fi
    done
done
