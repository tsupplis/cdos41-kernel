# REDOS.COM

Run `REDOS [drive:]` from DOS 2.0 or later. The destination defaults to the
current drive. REDOS checks for fixed-disk media, rejects a destination that
already has either IBM system file, and opens the reserved DRIBIO.COM and
DRIDOS.COM placeholders. It prompts for a PC DOS system disk in A:, copies
IBMBIO.COM and IBMDOS.COM into the placeholders, transfers their DOS dates
and times, and renames the placeholders to the IBM names. The normal exit
path restores the original default drive.

The command uses extended DOS FCBs for hidden/system files. Its historical
size test checks the low word of the DRIBIO slot against 1200h. The floppy
reads request 1400h records and pass the returned count to each block write.

The labelled ASM86 source reconstructs the executable from the CDOS 4.11
release. The historical REDOS.SUB supplies the build recipe. `make check`
compares the complete 1,664-byte COM file with ../../base/redos.com.
