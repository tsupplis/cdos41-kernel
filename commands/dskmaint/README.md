# DSKMAINT


## 4.11 alignment — in progress

The first 0D84h CODE bytes (SQUIDDM1/2/3, DISPLAY, SYSTEM, PCCRT and SCREEN)
match the release after 316 DATA-address relocations. The release places the
020Ch-byte CONST group before DATA; our linker places it afterwards. This
accounts for those operand changes without changing the main command logic.
HELP/FUNC10/startup differences still require separate classification.

A substantive difference exists in the embedded DOS boot sector. The OEM
DOSBOOT.A86 used by this build is a non-system-disk message stub. The 4.11
command embeds a loader with CPM3.SYS/CCPM.SYS names and boot/read-error
handling instead. No boot code has been replaced in this assessment.
Recovering and testing that loader is required before closing DSKMAINT.
