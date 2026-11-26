# Alpha 7 performance and usability

## Idle tray

The Alpha 6 and Alpha 7 native tray binaries ran side by side in the same IceWM session in a 1 GiB, two-vCPU QEMU BIOS guest. The guest booted from the published Alpha 6 image. An Xlib interposer counted each tray's calls to XClearWindow after five seconds of settling. Both binaries call it once per repaint. Over 120 idle seconds, Alpha 6 repainted 40 times and Alpha 7 repainted twice.

The updated panel listens for network link and keyboard state changes and wakes on the next minute boundary for its clock. A restricted Xvfb session that denied network notifications observed 40 and 41 repaints respectively. The panel falls back to polling in that environment. The experiment measures redraw frequency. Whole-system CPU, battery life and application launch time require separate measurements.

See the [Linux kernel CPU idle documentation](https://docs.kernel.org/admin-guide/pm/cpuidle.html).

## SquashFS compression

Both tests used the same Firefox ESR libxul.so from the published Alpha 6 Extreme Lite image, one decompression worker and 1 MiB SquashFS blocks. XZ used its x86 filter and Zstandard used level 19. After one warm-up per format, five passes alternated order on the same host. Each pass read out the entire library into /dev/null.

| Codec | Bytes | Five samples (s) | Median (s) |
| --- | ---: | --- | ---: |
| XZ | 53,186,560 | 1.920, 2.015, 1.969, 1.876, 2.034 | 1.969 |
| Zstandard | 58,937,344 | 0.269, 0.269, 0.278, 0.258, 0.264 | 0.269 |

Alpha 7 keeps XZ for its smaller compressed footprint. Firefox startup touches only part of the library and can reuse cached pages. This benchmark measures sequential decompression on the build host. Startup on a Celeron and on an older HDD still needs measurement.

See the [Linux kernel SquashFS codec descriptions](https://github.com/torvalds/linux/blob/master/fs/squashfs/Kconfig).

## First-use design

Firefox Home presents offline learning first and needs no external fonts, scripts or graphics. The window chooser pairs document names with application icons and includes keyboard instructions. The two layouts follow [W3C guidance on understandable controls](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o1-understandable/) and reflect the interface alternatives examined in [Wiedenbeck's study of novice computer users](https://doi.org/10.1080/014492999119129). Classroom testing is needed to quantify ease of use.

## Network coverage

The previous release associated with a WPA-PSK test access point using two mac80211_hwsim radios in a QEMU guest. Release automation checks DHCP and Firefox HTTP through an emulated Ethernet adapter. Device firmware, a physical Wi-Fi adapter, public connectivity, and captive portals require separate testing.
