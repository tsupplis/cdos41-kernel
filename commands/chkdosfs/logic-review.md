# Original CHKDSK versus CHKDOSFS logic review

The reference is `chkdosorg.dis`, decoded from the frozen DOS Plus CHKDSK
binary; there is no maintained `chkdsk.a86` rebuild. CODE addresses below
are segment-relative. This compares application logic, not the C runtimes.

| Area | Original CODE | Maintained C | Assessment |
|---|---|---|---|
| Drive/options | 01EE–0428 | `chkdosfs.c` | Deliberate project interface: one mandatory drive, bracket options; slash accepted. Original accepts current/multiple drives and OS-specific switch character. |
| OS support | 0331, 1B54–1C2B | `native.c`, `os.a86` | Deliberately CDOS 4.1 only; the original also supports DOS Plus. Not a DOS Plus runtime replacement. |
| Lock and process state | 0429–04BD, 1BC9–1BF5 | `diskopen`, `diskclose`, KKEEP/KERROR | Improved: check acquisition, recheck open files under lock, restore KEEP/error mode/drive. Refuses any open-drive vector, more restrictive than the original target-drive test. |
| Geometry/FAT12/FAT16 | 04F5–07F2, 156E–1696 | `geomset`, `fatget`, `fatset` | Same DPB-based addressing and packed entries, checked arithmetic/bounds. Deliberate 512-byte physical-sector scope. |
| FAT copies | 1744–1830 | `mirrors`, `fatsector` | Improved: compare copies before repair; disagreement blocks all writes. Preserve packed neighbouring FAT12 entries. |
| Root/subdirectory traversal | 0C68–0DD5 | `walkdir`, `filechain` | Aligned ownership checks, bounded iterative traversal. Correctly stops interpreting records at the end marker, skips VFAT name records, still validates allocation beyond directory end. Original continues scanning unused entries. |
| Volume label/date | 0D23–0D9A | `volume_label` | Reporting omission closed during this review. Bounded label and timestamp fields; no unchecked month-table indexing. |
| Hidden/user/directory allocation | 0A2A–0A9A | `fscheck` and allocation counters | Reporting omission closed: total data capacity and allocated bytes by category. Recorded file bytes remain separate. |
| Size/EOF correction | 0E15–0FEA | `walkdir`, `filechain`, `filesize` | Aligned full-chain-capacity adjustment; no trimming to recorded length. Improved: preflight and confirmation; bad markers, cross-links and unowned evidence block repair. Invalid starts are refused rather than clearing the file record. |
| Lost-chain identification | 07F3–0958 | `fscheck`, `incoming`, `orphanchain` | Same allocated-versus-referenced distinction, with bounded detection of loops/joins. Bad clusters are not recoverable files. |
| Ordinary F recovery | 0FF1–119F | `recoverfiles`, `recovered_file` | Same FILEhhhh.CHK, archive attribute 20h, whole-chain size and zero timestamps. Improved: name collisions/root capacity checked; disjoint bounded recovery of cycles/shared tails; never adopts live/free/bad clusters. |
| F release | 09D4–0A17, 11A0–11D9 | `repairfs` | Improved: separate explicit confirmation. Original releases on declining conversion. |
| D/DF | 08B2–0909 | `erased_directories` | Original compares dot/dot-dot against the same record and cannot detect a remnant. Corrected distinct records plus plausibility checks, diagnostic-only even with F. |
| L/LF | 0DD6–0E03, 11DA–12A1 | contiguous candidate/preflight/commit | Same adjacent-entry, rounded-size and free-FAT heuristic; same suppression of ordinary size/EOF fixes. Improved ownership/overlap checks and tail-first commit. Split-sector FAT12 heads are detected but refused for repair. |
| R/RF | 0978–09D3, 103E–10AB | orphan directory preflight/reconnection | Same allocated first-level dot/dot-dot directory recovery, directory attribute 10h/size zero. Improved whole-tree, parent/name/ownership validation before root-only publication. Declining never releases unrelated data. |
| B/BF/RB | 0DC6–0DD5, 12A2–1383 | `read_cluster` and scan/recovery callers | Same full referenced-cluster data reads, not a free-space surface scan. Improved streaming beyond the old 8 KiB buffer limit, including L ranges and orphan adoption preflight; aborts on I/O failure. No fabricated data or bad-cluster marking. |
| Write/verification errors | 1438–156D, 18D9–1931 | native I/O, guarded writes, `verify_changes` | Improved: abort on first error, enforce F physically, reread changes, report possible partial writes. No crash-atomic transaction or rollback is claimed. |
| Verbose/output/status | Throughout | command/core | Same diagnostic purpose, not identical presentation: cache-allocation/read-count diagnostics and grouped-decimal formatting are not reproduced. Explicit return statuses distinguish errors from incomplete checks. |

No additional missing scan or recovery mode was found. “Aligned or improved”
applies within the declared CDOS/512-byte-sector scope and the intentionally
changed command interface; it does not mean unrestricted original compatibility.
Safety refusals are intentional: nesting is bounded to 32 frames; L/R plans to
256 candidates; ambiguous repairs are left to manual recovery.

`make check` checks the reference bytes/disassembly, compiled option parsing,
production C image checks and exact metadata changes, fault-injected write
prefixes, B read coverage, and the reporting regressions added by this audit.
Native FAT12/FAT16 tests exercise the CDOS adapter; they do not execute every
reference branch or establish bit-for-bit diagnostic equivalence.
