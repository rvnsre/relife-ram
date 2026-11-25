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

Extreme Lite keeps Intel Wi-Fi 4/5 and AX200/AX201 firmware, Realtek firmware,
and Qualcomm Atheros Wi-Fi 4/5 and QCA6390 firmware. Education retains the
full Intel, Realtek and Qualcomm Atheros packages and adds MediaTek and
Broadcom firmware. The 1 GiB Extreme Lite VM gate checks idle memory against
700 MB and captures Firefox's memory use after loading the test page. It
also verifies compressed RAM swap has no backing device.
