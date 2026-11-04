# DFORM

Concurrent DOS 4.1 command-line floppy formatter, adapted from CCP/M DFORM.
The default formats a 320K CP/M disk. `[1]` selects 160K CP/M. Both embed
the local CDOS boot sector and loader. Copy the matching system file to
complete a CP/M system disk.

DOS profiles are explicit and always double-sided:

| Option | Capacity | Geometry | FAT12 layout |
| --- | --- | --- | --- |
| `[DOS]` or `[DOS360]` | 360K | 40×2×9 | 2 sectors/cluster, 2 sectors/FAT, 112 root entries |
| `[DOS720]` | 720K | 80×2×9 | 2 sectors/cluster, 3 sectors/FAT, 112 root entries |
| `[DOS1200]` | 1.2M | 80×2×15 | 1 sector/cluster, 7 sectors/FAT, 224 root entries |
| `[DOS1440]` | 1.44M | 80×2×18 | 1 sector/cluster, 9 sectors/FAT, 224 root entries |

Example: `DFORM B:[DOS1440] [V]`. `[V]` verifies every track; `[1]` is
incompatible with DOS profiles. Confirm the target before answering Y.
Formatting overwrites all contents. Use a drive/controller supporting the
selected capacity; 3.5-inch AT drives are identified by CMOS type 3 or 4.

Both formatters install the same maintained DOS boot sector. Copy the normal
`CCPM.SYS` as the first file on the newly formatted disk, then boot it.
No alternative kernel build or separate system-install command is required.
The file must remain contiguous from cluster 2; copying it first onto an
empty disk provides that layout. `CPM3.SYS` is also accepted for compatibility.
DOS floppy boot does not use DRIBIO.COM/DRIDOS.COM.

The native formatter holds MXdisk, formats with XIOS 29 and reads/writes
physical sectors with 35/36. It supplies the selected geometry through a
temporary INT 1Eh table and restores the vector before releasing the disk.
CMD MIN reserves 32K for a 16K-aligned head buffer (18 sectors fit); its
zero-filled storage is omitted from CMD LEN.

`make check-dform-live` at the project root exercises the CDOS format and
verify path and reads and writes the FAT filesystem with mtools. It also
checks empty-disk recovery and cold-boots a normal distribution kernel
on disposable PCE images. The 1.44M case writes/reads a 1,433,600-byte
file through native BDOS, exercising FAT entries beyond the old 1.2M limit.
