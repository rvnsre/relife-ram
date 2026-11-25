# ReLife browser baseline

Both live images use Debian's Firefox ESR (Gecko and SpiderMonkey, GTK 3 on
X11). The ReLife profile selects content-process and memory-cache preferences
from RAM and CPU affinity. It leaves Firefox's site isolation, sandbox and
certificate verification enabled. No browser process starts at desktop login.

The network regression was missed by the previous virtual hardware matrix
because the NIC was disconnected and Firefox loaded a local file. The new VM
test uses an Ethernet NIC, verifies DHCP/HTTP and checks the title of a page
actually loaded over HTTP by Firefox. The virtual HTTP endpoint is local to
the test. Real Wi-Fi drivers, access-point authentication, captive portals,
public HTTPS and browsing benchmarks still need physical-device testing.

The live user's active local desktop can add NetworkManager profiles. The
rule is scoped to the profile-management action, since Debian's default
policy requires administrator authentication for a new system profile.

Builds retain official Debian firmware for popular Intel, Realtek and Qualcomm
Atheros adapters. Education includes additional MediaTek and Broadcom firmware.
VM reports retain the original 700 MB measurement and record raw/free-based RAM
too. The added driver coverage can increase the compressed live image and its
RAM footprint.
