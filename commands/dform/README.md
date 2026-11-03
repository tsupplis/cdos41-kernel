# DFORM

Concurrent DOS 4.1 command-line floppy formatter, adapted from CCP/M DFORM.
The default formats a 320K CP/M disk. `[1]` selects 160K CP/M. Both embed
the local CDOS boot sector and loader. Copy the matching system file to
complete a CP/M system disk.

`DFORM B:[DOS] [V]` creates a 360K FAT12 data disk and verifies every
track. DOS mode requires two heads and rejects `[1]`. Confirm the drive
before answering Y. Formatting overwrites the target. The DOS profile writes
two FATs and an empty root directory with a non-system boot sector.

The native formatter holds MXdisk, formats with XIOS 29 and reads/writes
physical sectors with 35/36. It supplies the selected geometry through a
temporary INT 1Eh table and restores the vector before releasing the disk.
CMD MIN reserves the aligned DMA scratch space.

`make check-dform-live` at the project root exercises the CDOS format and
verify path, reads and writes the FAT filesystem with mtools, and cold-boots
the non-system sector on disposable PCE images.
