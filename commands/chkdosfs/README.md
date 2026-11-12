# CHKDOSFS

FAT filesystem checker being recreated in C from Digital Research CHKDSK 1.0
(20-Mar-86), supplied with DOS Plus. The original explicitly accepts Concurrent
DOS as well as DOS Plus. The intended output is `CHKDOSFS.CMD`, complementing
`CHKCPMFS.CMD` for CP/M filesystems.

**Status: native C checker with confirmed size/EOF corrections and lost-chain
recovery/release.** Packaged on `cdosdos.img`; CHKCPMFS remains on
`cdosadmin.img`. All original B/D/F/L/R/V switches are supported, with the conservative repair
differences documented below; strict behavioural identity is not claimed.

## Alignment with the original

The routine-by-routine [logic review](logic-review.md) found no missing scan or
recovery mode. There is high confidence in alignment with the original's
filesystem checks and recovery decisions within the documented CDOS 4.1,
FAT12/FAT16 and 512-byte-sector scope. The command interface and some repair
refusals deliberately differ; strict behavioural identity is not claimed.

The C version improves the original logic:

- Corrects D's broken dot/dot-dot comparison while keeping remnants diagnostic-only.
- Validates complete ownership and candidate directory trees before recovery.
- Checks recovery-name collisions and root-directory capacity before publication.
- Stops on I/O errors instead of continuing with potentially stale data.
- Blocks repairs on malformed dot/volume-label entries in ordinary directories.
- Validates reserved FAT entries, allowing FAT16 shutdown/error status bits.
- Requires separate confirmation before releasing lost clusters.
- Rereads committed metadata to verify changes.

These improvements have targeted regression tests, exact image comparisons,
injected I/O failures and native FAT12/FAT16 verification. This is strong
evidence, not exhaustive proof for every damaged filesystem. Ambiguous repairs
are deliberately refused; partial physical writes are reported, with no claim
of crash-atomic recovery.

## Usage

```
CHKDOSFS drive: [BDFLRV]
  drive: A:..P:
  B      read file/directory data
  D      find erased-directory remnants
  F      repair
  L      find contiguous-chain candidates
  R      find orphaned first-level directories
  V      verbose
```

Exactly one drive is required, followed by an optional B/D/F/L/R/V option group.
B reads every sector of referenced file and allocated directory clusters,
including slack and directory clusters beyond the end marker. It also checks
inferred L ranges and orphan data before confirmed adoption; RB checks the
complete directory trees before RBF reconnects them. This is not a free-space
surface scan. A read failure aborts and blocks pending repairs. BF neither
reconstructs unreadable data nor marks clusters bad; file data is never written.

D reports plausible erased-directory remnants in free, unowned clusters.
It checks distinct dot/dot-dot entries, directory attributes, the self pointer,
parent range and zero directory sizes. These remnants are not consistency
errors or proof of recoverability. D does not allocate, restore, traverse or
rewrite them, even with F; DF can still perform the ordinary confirmed repairs
on independently established filesystem errors. Any D read failure blocks
repair of that scan.

L examines files whose starting FAT entry is free. The original heuristic
requires the physically next directory entry to start exactly after the
size-implied contiguous range, with every proposed FAT entry free. This does
not establish that the surviving bytes belong to the file: reconstruction
remains a heuristic, and L alone never writes.

LF offers a separate confirmation to rebuild the candidates. The complete
live-ownership scan must find no conflicting reference or candidate overlap.
The adjacent entry must be active; arithmetic, volume limits and directory
boundaries are checked. All candidates are checked again before writing.
L suppresses ordinary size/EOF corrections, as in the original; unresolved
problems block LF rather than silently falling back to those corrections.
File sizes, directory entries and all data sectors remain unchanged by LF.

Chains are linked tail-to-head, publishing the file's starting link last.
If that starting FAT12 entry spans two sectors, it is detection-only: LF
refuses because the head cannot be activated in one sector update. Entries
later in the unreferenced tail may span sectors, but the head remains free
until the complete tail is committed. At most 256 candidates are planned;
exceeding that bound stops the complete operation without writes.

R selects allocated orphan directories whose dot entries identify a
first-level directory (self pointer correct and parent pointer zero). It is
not undelete of free clusters: D can report those remnants, but R leaves them
unallocated. R alone validates and reports candidates without writing.

RF offers confirmed reconnection as FILEhhhh.CHK directories in the root.
The complete candidate trees must have valid parent links, bounded unique
allocation, plausible short-name records and no duplicate names or cross-links
with live files or other candidates. Damaged child chains or sizes are refused;
RF does not repair speculative directory contents. Up to 256 trees are planned,
with root capacity checked before writes and candidates rechecked after
confirmation. RF adds root entries with directory attribute 10h and zero size;
FAT chains, existing directory contents and all file data remain unchanged.

R selects directory recovery rather than ordinary orphan-file conversion.
Unrelated orphan clusters remain reported. Declining RF cancels that recovery;
it never falls through to freeing orphan clusters. This is intentionally safer
than the original's release-on-decline path. Ordinary confirmed F corrections
on live files may precede RF; later cancellation preserves and reports those
previous changes accurately.

V lists checked entries. With no F, the command does not write to the disk.
Options are case-insensitive; invalid arguments stop before disk access.

Without L, F first offers correction of file sizes and missing end-of-chain markers.
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
New files receive the whole recovered chain's capacity as their size. New ordinary recovered files have archive attribute 20h and zero timestamps,
as in the original. Recovered directories use attribute 10h and zero size.

Declining conversion offers confirmed release of the unreferenced clusters.
Declining both leaves them unchanged. Each accepted stage updates every FAT
copy as needed and rereads the disk for verification. An I/O failure stops
repair immediately; a write failure may leave partial changes and is reported
as such. BDOS drive state is reset after writes before restoring the old drive.
There is no crash-atomic transaction or rollback after a failed physical write.

CHKCPMFS retains F as a placeholder; CP/M
filesystem repair is a separate implementation.

The C implementation checks FAT12/FAT16 chains, directories, file lengths,
cross-links, lost clusters and FAT-copy agreement. Native CDOS tests cover a
360K FAT12 floppy and a FAT16 partition on a 306-cylinder, four-head,
17-sector hard disk. Both include nested files, clean and mismatched FAT
copies, repeat invocation and verbose output. Read-only images remain byte-identical; repair tests compare the complete
image against the exact expected FAT and directory changes. Intentional safety differences are described above.

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

## Safety and tests

The replacement's added detection must not authorize speculative writes.
Repair requires a complete ownership scan, F and confirmation. Conflicting
FAT copies, live-chain cross-links and uncertain ownership prevent writes.

`make check` runs the production checker/writer against exact expected image
bytes. Its safety matrix fails every physical write in representative FAT12
and FAT16 corrections, release, and recovery operations. It verifies the exact
successful write prefix and that no later write is attempted. Read failures
cover preflight, repair and verification. Read-only and cancelled operations
must preserve the complete image. Regular file data must remain unchanged.

Same-sector FAT entries are updated together in a single sector image. A
packed FAT12 entry spanning sectors still requires multiple physical writes;
all required input is read before writing. Multiple sectors/copies are not
crash-atomic. Failed writes may leave partial changes; failed verification
after writes reports that explicitly. No untested rollback is attempted.

The original D branch compares both '.' and '..' against the same directory
entry (CODE 08DAh and 08F0h load the same pointer). Detection therefore cannot
succeed. This replacement checks the first and second entries separately and
adds plausibility checks. This intentional correction remains diagnostic-only.

Exit status: 0 for a clean completed check, 1 for remaining consistency errors,
2 for an aborted, refused or incomplete operation. D remnants alone do not
change a clean filesystem's status.

L/LF tests compare exact images, test every write-failure prefix and check that
no published head leads to an incomplete tail. They cover ownership conflicts,
directory/volume boundaries, cancellation, the candidate cap and interactions
with ordinary orphan recovery/release. Native FAT12 and FAT16 tests restore
the fixture's original chain bytes while retaining the original file sizes.

R/RF tests cover nested and multi-cluster trees, complete preflight of all
candidates, bad parent/dot entries, malformed records, duplicate names,
cross-links, root capacity, cancellation and staged cancellation. Every root
write position is fault-injected; only the exact successful metadata prefix
may change. Native FAT12 and FAT16 tests reconnect an orphaned directory while
preserving all FAT and data bytes; the FAT12 test also checks the kernel DIR
listing after the checker releases the lock and resets drive state.

B tests compare exact sector-read coverage against the same scan without B,
including fragmentation, multi-sector clusters, directory slack, inferred L
ranges and recovered trees. Injected read failures must stop immediately and
block pending metadata changes. Combined BF/RBF failures check exact successful
write prefixes; ordinary file data must remain byte-identical. Native tests
cover FAT12 B/BF recovery and FAT16 B/BF and RB/RBF scans.

The final [logic review](logic-review.md) maps original CODE routines to the C
implementation, including safety improvements and deliberate compatibility
limits. Volume labels/timestamps and allocated-space totals by category are
reported; timestamps are bounded before formatting.
