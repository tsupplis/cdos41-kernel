# DSKMAINT

Built from CDOS 4.1 OEM sources with the DOS floppy boot sector reconstructed
from the 4.11 release. Command syntax and disk geometry choices are unchanged.

## DOS format and boot

The earlier OEM sector displayed a non-system disk message. DSKMAINT now writes
the 4.11 bootstrap, assembled from labelled instructions in dosboot.a86. All
512 bytes match the independent release sector. The formatter overlays the BPB
for the selected disk geometry. The loader accepts the 360 KB format (FDh).

To boot, copy CCPM.SYS or CPM3.SYS as the first file on a newly formatted disk.
The release loader checks the first root entry and cluster 2 and reads the file
contiguously. It enters the kernel at 0060:0000. Generate the kernel for this
floppy with GENCCPM OSSTART=60. The normal CP/M distribution uses OSSTART=6000
and its own boot path.

## Verification

`make check` in this directory checks the embedded DOS sector and compares the
seven main assembly modules, SCD startup and FUNC10 against 4.11. The main code
contains 316 relocated data operands, FUNC10 contains 31, and the startup has
one relocated call. The main data contains 140 relocated words. The release
links the 020Ch-byte constants before DATA. The constants, help data and FUNC10
data compare exactly after accounting for that layout.

The remaining compiled HELP body differs in instruction selection and size.
The 4.11 and rebuilt executables displayed the same DSKMAINT main menu, first
help page, next page and return-to-menu screen with the original HELP.HLP.
Whole-executable byte identity is unverified.

At the project root, `make check-dskmaint-live` runs the actual format command
on a disposable 360 KB drive B. It checks the resulting sector and FAT, then
cold-boots three copies: empty media displays the recovery prompt, original
4.11 CCPM.SYS reaches A>, and a locally generated low-linked system named
CPM3.SYS also reaches A>. Release disks and host filesystems are untouched.
