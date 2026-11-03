# DFORM

Concurrent DOS 4.1 command-line floppy formatter, adapted from CCP/M DFORM.
The default formats a 320K CP/M disk. `[1]` selects 160K CP/M. Both embed
the local CDOS boot sector and loader. Copy the matching system file to
complete a CP/M system disk.

`DFORM B:[DOS] [V]` formats a 360K FAT12 disk and verifies every
track. DOS mode requires two heads and rejects `[1]`. Confirm the drive
before answering Y. Formatting overwrites the target. The DOS profile writes
two FATs, an empty root directory and the same 4.11 system bootstrap as
DSKMAINT. Copy a compatible `CCPM.SYS` as the first file after formatting;
it must start at cluster 2 and be contiguous. The historical DOS bootstrap
requires a kernel generated with `OSSTART=60`, rather than the normal CP/M
build at `6000`. DFORM does not copy or regenerate the kernel.

The native formatter holds MXdisk, formats with XIOS 29 and reads/writes
physical sectors with 35/36. It supplies the selected geometry through a
temporary INT 1Eh table and restores the vector before releasing the disk.
CMD MIN reserves the aligned DMA scratch space.

`make check-dform-live` at the project root exercises the CDOS format and
verify path and reads and writes the FAT filesystem with mtools. It also
checks empty-disk recovery and cold-boots a copied, low-linked rebuilt kernel
on disposable PCE images.
