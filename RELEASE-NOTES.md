ReLife RAM v0.3.0 Alpha 1 provides two amd64 live images. Extreme Lite runs the
offline Education Center without a browser. Education adds Firefox ESR and
confirmed links to ChatGPT, Claude and Gemini.

The release includes BIOS, UEFI, and USB-free UEFI VM reports. RAM figures count
the compressed system copied into memory. The reports identify the VM size,
include a shutdown check, and report both available-based and raw RAM use.

Windows Boot Setup stages the Extreme Lite system on an existing dedicated
FAT32 volume. It requires 64-bit UEFI firmware with Boot from File and the
ability to run an unsigned EFI application. Do not use the Windows EFI system
partition. Choose the ReLife EFI application from firmware to start a session.
The setup tool can remove ReLife files from the same volume. Procedure and
recovery instructions are in `windows/README.md`.

The bundled library contains six original Azerbaijani lessons. The native
center includes retrieval practice, flashcard import/export, lesson plans,
calculations, notes and a focus timer. The local stdio MCP adapter supports
three read-only tools for the bundled lessons and unit conversion. The alpha
scope is smaller than the full 150-function roadmap. Physical hardware,
proprietary provider accounts and Secure Boot are outside this VM validation.
