# DSKMAINT

Built from CDOS 4.1 OEM sources with the DOS floppy boot sector reconstructed
from the 4.11 release. Command syntax is preserved; native CP/M capacity choices are extended.

## Format selection

Choose F2 for CP/M or F3 for DOS, then select a capacity from the
three-column format screen. Esc returns to the previous menu.

| Key | CP/M | DOS FAT12 |
| --- | --- | --- |
| F4 | 160K | 180K |
| F5 | 320K | 360K |
| F6 | 720K | 720K |
| F7 | 1200K | 1200K |
| F8 | 1440K | 1440K |

## DOS boot

The formatter installs the shared, header-aware `dosbootx.a86` bootstrap.
Copy the normal distribution `CCPM.SYS` as the first file on the newly
formatted DOS floppy, then boot it. No special kernel build is required.
The system file must be contiguous from cluster 2; `CPM3.SYS` is also
accepted. Formatting installs the bootstrap, while copying the system file
remains the user's responsibility. No DRIBIO/DRIDOS files are needed on
floppies. The original 4.11 `dosboot.a86` is retained as a checked reference.

## Verification

`make check` checks the independent 4.11 sector, verifies unchanged FUNC10,
HELP data and constants against 4.11, and inspects the linked extended format
profiles, BPBs, metadata, CHRN table and family and F4–F8 capacity menu bindings. The extended
format/menu module intentionally differs from the release; whole-executable
byte equivalence is not claimed.

`make check-dskmaint-live` runs each DOS 360K/720K/1.2M/1.44M choice on
disposable images, checks the written sector/FAT, then cold-boots both system
filenames using the normal distribution kernel. No release image is
modified.

## CP/M boot stages

`bootsect.a86` and `loader.a86` are identical local copies of the maintained
CP/M/CCP/M sources. DSKMAINT owns their build; DFORM and media recipes use
those same generated images. The loader recognizes 160K, 320K, 720K, 1200K
and 1440K geometry markers and loads `CPM.SYS` or `CCPM.SYS`.

HDMAINT's independent `DRIBIO.COM` and `DRIDOS.COM` references live in `base`;
they are unrelated to the floppy boot path.
