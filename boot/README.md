# IBM PC 320 KB boot track

The boot-sector and loader sources are unchanged local copies from the
CCP/M project. They load CCPM.SYS directly; the floppy boot path is
independent of HDMAINT's hard-disk loaders.

The 4.1 SQUID XIOS has the same double-sided geometry: 40 cylinders,
8 sectors per track, 2 KB blocks, 64 directory entries, one reserved
logical track and reversed head-1 track numbering. `cpm86twist.py` is
copied unchanged and converts logical CP/M ordering to physical CHS.

`make` creates the 4096-byte boot track. `make check` verifies its layout:
147-byte boot sector at 0, double-sided marker at 511, 846-byte second
stage at 2304 and E5 filler elsewhere. The first stage enters at 7C00;
the loader starts at offset 100h and loads CCPM.SYS at its fixed header
address. No archived binary boot track is used as a build input.

## FAT hard-disk loader references

`dribio.com` (4,736 bytes) contains the FAT loader followed by zero padding.
`dridos.com` (17,024 bytes) is the all-zero dummy system file reserved by
HDMAINT. The original names and placement are part of the FAT boot layout.

`make -C ../commands/hdmaint check-fat` assembles `pcboot3.a86` and verifies
that its 1,280-byte output matches DRIBIO exactly. It also checks the
2,048-byte loader slot at file offset 7280h in `base/hdmaint.cmd`, the zero
padding and DRIDOS contents. This verifies the tertiary FAT stage. The
partition boot sector and complete hard-disk boot have also been verified
under PCE for both CP/M and FAT12 partitions, with no floppy media attached.
See [HDMAINT installation checks](../commands/hdmaint/README.md#installation-and-cold-boot-verification)
for the tested geometry, installation steps and scope.
