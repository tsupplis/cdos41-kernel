# CHKCPMFS

`CHKCPMFS.CMD` is a read-only first-pass consistency checker for CP/M media
under Concurrent DOS 4.1. It scans ordinary file entries in user areas 0–15
on the currently selected drive through BDOS. It does not modify the disk.

Before scanning, it checks the drive's BDOS read-only state. If the drive is
writable, CHKCPMFS temporarily sets it read-only and resets the drive afterward
to restore write access. A drive that was already read-only remains so. If
write protection cannot be established, the scan stops; if write access cannot
be restored, CHKCPMFS reports the failure and instructs the operator to use
`SET d: [RW]`. CDOS may refuse the protection request when another process has
files open on the drive. The normal cleanup resets the drive; its next access
may require a re-login. If the command is interrupted, verify the state with
`SHOW` and use `SET d: [RW]` if needed.

The checker uses the selected drive's DPB and reports record counts beyond
128, extent reserved bits, allocation references beyond the DPB's maximum
block, references to directory-reserved blocks, and duplicate block references.
Every nonzero allocation slot is checked, including slots beyond the record
count; zero slots are allowed for sparse files. `CCPM.SYS` is checked like any
other file. The checker refuses DOS/FAT media identified by the CDOS
pseudo-label.

Run it only when the drive is idle. BDOS read-only protection is software-level,
not an exclusive lock against raw disk I/O or another process resetting the
drive. The checker does not hold an exclusive filesystem lock, so concurrent
activity can still make its results inconsistent. This version does not
inspect deleted directory slots, validate
timestamp/XFCB metadata, read data sectors, identify lost blocks, or repair
anything. Its results are limited to the directory entries BDOS exposes.
CP/M rebuilds its allocation vector from the directory when a disk is logged
in; there is no on-disk list of allocated-but-unreferenced data blocks. This
checker does not compare the directory with the live in-memory vector.

Run `make check` in this directory for synthetic BDOS and DMA tests. After
building the media, `make check-live` also tests disposable CP/M and FAT images
under CDOS in PCE and verifies that the images are unchanged.
