# DSKMAINT

Built from CDOS 4.1 OEM sources with the DOS floppy boot sector reconstructed
from the 4.11 release. Command syntax and disk geometry choices are unchanged.

## DOS format and boot

The format screen has two columns with seven choices:

| Key | Format |
| --- | --- |
| F2 | CP/M 160K |
| F3 | CP/M 320K |
| F4 | DOS FAT12 180K (existing legacy option) |
| F5 | DOS FAT12 360K |
| F6 | DOS FAT12 720K |
| F7 | DOS FAT12 1.2M |
| F8 | DOS FAT12 1.44M |

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
profiles, BPBs, metadata, CHRN table and F2–F8 menu bindings. The extended
format/menu module intentionally differs from the release; whole-executable
byte equivalence is not claimed.

`make check-dskmaint-live` runs each DOS 360K/720K/1.2M/1.44M choice on
disposable images, checks the written sector/FAT, then cold-boots both system
filenames using the normal distribution kernel. No release image is
modified.
