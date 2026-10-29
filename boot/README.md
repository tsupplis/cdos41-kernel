# IBM PC 320 KB boot track

The boot-sector and loader sources are unchanged local copies from the
CCP/M project. They load CCPM.SYS directly, so HDMAINT and its missing
hard-disk LBDOS loader are not needed for this floppy boot path.

The 4.1 SQUID XIOS has the same double-sided geometry: 40 cylinders,
8 sectors per track, 2 KB blocks, 64 directory entries, one reserved
logical track and reversed head-1 track numbering. `cpm86twist.py` is
copied unchanged and converts logical CP/M ordering to physical CHS.

`make` creates the 4096-byte boot track. `make check` verifies its layout:
147-byte boot sector at 0, double-sided marker at 511, 846-byte second
stage at 2304 and E5 filler elsewhere. The first stage enters at 7C00;
the loader starts at offset 100h and loads CCPM.SYS at its fixed header
address. No archived binary boot track is used as a build input.
