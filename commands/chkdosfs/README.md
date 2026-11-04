# CHKDOSFS

FAT filesystem checker being recreated in C from Digital Research CHKDSK 1.0
(20-Mar-86), supplied with DOS Plus. The original explicitly accepts Concurrent
DOS as well as DOS Plus. The intended output is `CHKDOSFS.CMD`, complementing
`CHKCPMFS.CMD` for CP/M filesystems.

**Status: native C checker with confirmed size/EOF corrections and lost-chain
recovery/release.** Packaged on `cdosdos.img`; CHKCPMFS remains on `cdosadmin.img`. The original's
optional D/L/R/B modes are not implemented; full original parity is not claimed.

## Usage

```
CHKDOSFS drive: [FV]
  drive: A:..P:
  F      repair
  V      verbose
```

Exactly one drive is required, followed by an optional F/V option group.
V lists checked entries. With no F, the command does not write to the disk.
Options are case-insensitive; invalid arguments stop before disk access.

F first offers correction of file sizes and missing end-of-chain markers.
As in the original, an inconsistent size is adjusted to the full chain capacity;
excess clusters are not discarded to match a smaller recorded size. A complete
ownership scan precedes changes. Cross-links, bad clusters in live chains,
conflicting FAT copies, invalid directory starts and incomplete scans block
repair. Unrelated file attributes, timestamps and data sectors are preserved.

For lost chains, choose conversion into root files named FILEhhhh.CHK, with
hexadecimal suffixes based on their starting clusters. Existing names are never
overwritten. Root capacity is checked for the entire recovery before writes.
Orphan cycles and shared tails are separated into bounded, disjoint files;
links into live, bad or free clusters are cut without adopting those clusters.
New files receive the whole recovered chain's capacity as their size. New root
entries have zero attributes and timestamps, matching the original convention.

Declining conversion offers confirmed release of the unreferenced clusters.
Declining both leaves them unchanged. Each accepted stage updates every FAT
copy as needed and rereads the disk for verification. An I/O failure stops
repair immediately; a write failure may leave partial changes and is reported
as such. BDOS drive state is reset after writes before restoring the old drive.
There is no crash-atomic transaction or rollback after a failed physical write.

The original's following extra switches are not implemented:

| Original switch | Purpose |
|---|---|
| D | Search unreferenced clusters for erased-directory signatures |
| L | Reconstruct contiguous allocation using adjacent directory entries |
| R | Recover lost directories as directories instead of ordinary CHK files |
| B | Read allocated file data to find read errors; does not scan free space |
 CHKCPMFS retains F as a placeholder; CP/M
filesystem repair is a separate implementation.

The C implementation checks FAT12/FAT16 chains, directories, file lengths,
cross-links, lost clusters and FAT-copy agreement. Native CDOS tests cover a
360K FAT12 floppy and a FAT16 partition on a 306-cylinder, four-head,
17-sector hard disk. Both include nested files, clean and mismatched FAT
copies, repeat invocation and verbose output. Read-only images remain byte-identical; repair tests compare the complete
image against the exact expected FAT and directory changes. Full original parity remains pending.

| File | Purpose |
|---|---|
| `chkdosfs.c` | Drive/options, confirmations and command lifecycle |
| `check.c` | Ownership scan, corrections and recovered root files |
| `fat.c` | Cached FAT12/FAT16 reads and guarded mirrored writes |
| `native.c`, `os.a86` | CDOS locking, physical I/O and state restoration |
| `tests/` | Synthetic image/parameter tests and disposable native checks |
| `reference/chkdsk.cmd` | Frozen input, checked against `../../dosplus/chkdsk.cmd` |
| `chkdosorg.dis`, `symbols.json` | Annotated original instruction/data listing and routine map |
| `disassemble.py`, `analysis.md` | Reference validation and recovered design |

`make` builds `chkdosfs.cmd` with DRI C and RASM-86, following the existing
command build pattern. `make check` runs the synthetic FAT12/FAT16 checks and
verifies the frozen original against `../../dosplus/chkdsk.cmd`, its SHA-256,
complete disassembly byte coverage and direct branch targets. The C executable
is not intended to be byte-identical to the original.

The disassembly remains a reference, rather than a second maintained executable.

`make check-live` runs the bounded headless PCE FAT12 and FAT16 checks on
disposable images.
Build the local kernel and boot track first; this target does not rebuild the
full distribution.

Native repair tests cover combined file-size/EOF correction and recovered-file
creation on both FAT12 and FAT16. Synthetic tests also cover packed FAT12
sector boundaries, name collisions, orphan cycles/joins, full roots, advancing
directory end markers, cancellation and injected I/O failures.
