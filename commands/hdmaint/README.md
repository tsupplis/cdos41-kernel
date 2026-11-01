# HDMAINT 4.1

The final output is hdmaint.cmd. The OEM main source is named h70.a86;
the archive does not explain that filename.

The main program and boot stages are recompiled from the CDOS 4.1 OEM
sources. The missing flat loader BDOS is recovered from ossrc/ccpmv31/D8/
LBDOS.A86. Its executable code matches the loader embedded in the original
HDMAINT. The serial text is set to 1031-0000-009373 to match that reference.

rebuild.py reproduces the SID insertion in hdmaint.sub. It merges the two
H86 files up to their EOF records, trims the primary/secondary boot sector
padding, retains the two CP/M boot copies, and inserts the complete bundle
at the labelled placeholder. The FAT secondary stage has a 7C00h assembly
origin; its leading gap is removed. The FAT tertiary stage is padded to
its reserved 2048 bytes. Empty auxiliary CMD descriptors 5 and 8 are
omitted as in the historical SID-saved file. All transformations assert
the expected boundaries and values.

make check compares the entire resulting command byte-for-byte with
base/hdmaint.cmd and independently checks PCBOOT3 against boot/dribio.com.

## Installation and cold-boot verification

Verified under PCE with the rebuilt HDMAINT and current `CCPM.SYS`, using
an initially empty disposable 306-cylinder, 4-head, 17-sector hard disk:

| Partition | Layout | Installation | Cold boot without floppies |
| --- | --- | --- | --- |
| CP/M | Cylinders 0–99, type DBh, start LBA 1 | Created and verified; CP/M loader installed | CDOS 4.1 reaches `D>` |
| FAT12 | Cylinders 100–305, type 01h, start LBA 6800 | Created and verified; FAT loader installed | CDOS 4.1 reaches `C>` |

HDMAINT reported zero bad blocks and successful loader installation for
both partitions. After its requested floppy reboot, PIP copied `CCPM.SYS`
from A: to C: and D: with `[RVW]`. Each cold boot used a separate copy of
the resulting disk, selecting its partition through the MBR active flag;
both floppy images were removed from the test configuration. The emulator
was restarted for each boot, so neither test reused an in-memory kernel.

This covers partition creation, both loader-installation paths, loading the
current kernel and reaching the command processor. It does not claim physical
hardware validation, bad-sector recovery or every partition geometry.

