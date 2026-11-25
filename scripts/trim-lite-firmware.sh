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
