# CHKDOSFS reference analysis

This document records static findings from the original binary. Addresses are
CODE-relative unless marked DATA. Routine names are assigned during analysis;
compiler helper names and local block names are provisional. Runtime behaviour
and compatibility with the rebuilt kernel still need testing.

## Container and implementation

| Item | Original |
|---|---|
| File | 11,776 bytes, SHA-256 `2e3e8ebc58f7f1c3159dc7f261a8c1d7cb08ae4ba7a977770f9936294bff916c` |
| CODE | 9,152 stored bytes, relocatable |
| DATA | 2,464 stored bytes; maximum allocation 65,536 bytes |
| Implementation | DRI C SMALL/CLEAR runtime, dated 27-Aug-84; assembly OS interface |
| Checker/application | CODE 01EEh–1B53h, approximately 6.5 KiB including helpers |
| OS interface | CODE 1B54h–1C2Ah, 215 bytes |
| Remaining code | Startup, formatted output, arithmetic and string runtime |

The listing separates inline runtime strings and alignment bytes from code.
Its byte column covers the complete header, CODE, DATA and trailing file padding.
No rebuild from assembly is claimed: the C program will be the maintained output.

## Original command line

```
CHKDSK [drive: ...] [/V] [/F] [/D] [/L] [/R] [/B]
```

No drive means the current drive. Several drive operands are processed in order.
The parser accepts bare drive specifications through BDOS 152; filenames are
rejected. Switches are uppercase in the binary. DOS Plus can provide another
switch character; Concurrent DOS defaults to `/`.

| Switch | Recovered behaviour | Evidence (CODE) |
|---|---|---|
| `/V` | Verbose directory, cluster, cache and I/O messages | 020Dh; consumers throughout checker |
| `/F` | Enable writes and recovery; otherwise report without committing repairs | 0215h, 1744h, 18D9h, 09C7h |
| `/D` | Scan unreferenced clusters for erased-directory signatures | 021Dh, 08B2h |
| `/L` | Attempt contiguous-chain reconstruction; suppress several normal size/EOF corrections | 0225h, 0DD6h, 11DAh |
| `/R` | Select recovery of first-level directories instead of ordinary recovered files | 022Dh, 0978h, 103Eh |
| `/B` | Read allocated file data in contiguous cluster runs using an 8 KiB buffer | 0235h, 06C8h, 0DC6h, 12A2h |

These are recovered semantics, not a claim that all combinations are safe or
already tested. `/B` is not a full free-space surface scan. `/L` uses a specific
adjacent-entry/contiguous-allocation heuristic, not arbitrary file undelete.
The precise `/D` and `/R` interaction needs deliberately damaged reference
fixtures before finalising the replacement's help text.

## Checker flow

1. Validate the OS; reserve workspace below the stack.
2. Parse/reset/select the drive, reject an open drive, acquire the disk lock.
3. Copy its 29-byte DPB. Extflag FFFFh means FAT12; FFFEh means FAT16.
   CP/M media and missing physical DPHs are rejected.
4. Derive sector size, cluster geometry and directory-entry indexing from DPB.
   FAT12 is held in memory; FAT16 uses linked cached records. Directory caches
   have a next pointer, 32-bit record number, dirty word and buffer pointer.
5. Build per-cluster state, walk the fixed root and subdirectory chains, classify
   hidden files/directories/files and diagnose cross-links, sizes and EOF links.
6. Identify lost chains; optionally recover them into root entries or release
   them. Recovered ordinary names use `FILE%04xCHK` (8.3 name field).
7. Flush permitted changes to directory records and all FAT copies, print space
   totals, release the lock and reset drive state as required.

The cluster-state array occupies one byte per cluster, not a bitmap. Three
bitmap helpers are linked but have no direct callers in the decoded program.

## Kernel interface

| Interface | Original dependency |
|---|---|
| BDOS 12 | Version; AH=10h selects DOS Plus, low byte must be at least 32h |
| BDOS 154 | Obtain SYSDAT segment |
| CDOS UDA | SYSDAT:68h points to current PD; PD+10h is UDA segment |
| DOS Plus UDA | Word at SYSDAT:4Eh |
| Physical DPH table | SYSDAT:0C18h (CDOS), :0F08h (DOS Plus) |
| DPB | Pointer at DPH+8; copy 29 bytes |
| Open-drive vector | Word at SYSDAT:88h |
| CDOS serialization | MXdisk queue: BDOS 135/137/139; P_KEEP via BDOS156 PD+6 bit 1 |
| DOS Plus serialization | BDOS109 with parameter 8 / 0 |
| Sector I/O | Native XIOS10/11 through far pointer SYSDAT:28h; DS=SYSDAT, ES=UDA |
| Output | BDOS111 buffer/segment/length packet |

The CDOS DPH-table address and PD UDA field agree with our existing interfaces.
This does not prove all DPB/I/O assumptions or failure cleanup are compatible.
The C port should isolate these dependencies in a small assembly module.

## Behaviours to correct rather than reproduce blindly

- The old runtime overwrites interrupt vector 0 (011Ch). Use the maintained
  command runtime; do not transplant its startup code.
- Original MXdisk open/read calls do not check failure, and P_KEEP is cleared
  unconditionally on release. Check lock acquisition and restore prior state.
- Open-drive checking precedes lock acquisition. Recheck under the lock.
- Sector read/write routines report failures but advance to the next transfer
  (1438h/14D3h). An I/O failure must abort checking/repair, not feed stale data
  to filesystem analysis.
- Keep `/F` enforcement at the physical-write boundary too. The original
  enforces it in cache flush/recovery callers; 1A38h is only a warning routine.
- Bounds-check arithmetic, cache allocations, directory recursion and chain
  traversal. A damaged FAT must not cause an infinite loop or wraparound.
- Original printf uses a 132-byte stack buffer. Bound new output formatting.

## C recreation plan

| Module | Responsibility |
|---|---|
| `chkdosfs.c` | Options, drive lifecycle, diagnostics and summary |
| `fat.c` | FAT12/16 entries, cache, checked cluster/sector arithmetic |
| `check.c` | Directory/chain validation and cluster ownership |
| `repair.c` | Explicit recovery actions and guarded commit |
| `cpmif.a86` | BDOS/XIOS, DPB discovery, lock acquisition and restoration |

Keep the algorithm independent of the native I/O adapter so disposable host
images can exercise the same checker. Build the CMD with DRI C and RASM-86,
following CHSET. First compare read-only results on clean and damaged FAT12/16
images, then compare resulting bytes for each enabled repair. Tests must verify
that report-only runs perform zero writes and that failed I/O aborts safely.

## Routine map

Addresses refer to the unmodified CODE group. Local branch labels in the
listing retain their address until their complete purpose has been established.

| CODE | Routine |
|---|---|
| 0000h | `runtime_entry` |
| 0026h | `runtime_fatal_inline_message` |
| 0032h | `runtime_heap_init` |
| 0041h | `runtime_heap_available` |
| 004Dh | `runtime_sbrk` |
| 0064h | `runtime_brk` |
| 00D5h | `bdos_call` |
| 00F1h | `runtime_default_drive` |
| 011Ch | `runtime_install_divide_handler` |
| 012Ah | `runtime_divide_error` |
| 013Fh | `runtime_os_features` |
| 0198h | `runtime_stack_init` |
| 01BFh | `runtime_stack_allocate` |
| 01EEh | `parse_options_and_check_drives` |
| 02FAh | `allocate_initial_arena` |
| 0331h | `initialize_options_and_memory` |
| 03D3h | `parse_drive_specification` |
| 0429h | `acquire_disk_lock` |
| 0477h | `release_disk_lock` |
| 04BEh | `allocate_drive_workspace` |
| 04F5h | `check_drive` |
| 0BA9h | `print_cluster_space_total` |
| 0BEBh | `print_grouped_decimal` |
| 0C68h | `walk_directory` |
| 0CD9h | `check_directory_entry` |
| 0FF1h | `recover_lost_chain_heads` |
| 1032h | `create_recovered_root_entry` |
| 11A0h | `release_lost_clusters` |
| 11DAh | `rebuild_contiguous_file_chain` |
| 12A2h | `read_file_cluster_runs` |
| 12FFh | `read_contiguous_clusters` |
| 1384h | `select_directory_entry` |
| 1438h | `read_disk_sectors` |
| 14D3h | `write_disk_sectors` |
| 156Eh | `get_fat_entry` |
| 1602h | `cluster_out_of_range` |
| 161Ch | `set_fat_entry` |
| 1697h | `select_fat_cache_record` |
| 1744h | `flush_fat_cache` |
| 1831h | `select_directory_cache_record` |
| 18D9h | `flush_directory_cache` |
| 1932h | `bitmap_test_unused` |
| 1964h | `bitmap_set_unused` |
| 1989h | `bitmap_clear_unused` |
| 19B0h | `print_directory_filename` |
| 1A38h | `warn_read_only_once` |
| 1A71h | `fatal_error` |
| 1A89h | `lowercase_unused` |
| 1AA5h | `zero_memory` |
| 1ABFh | `copy_bytes` |
| 1AE3h | `bytes_equal` |
| 1B0Eh | `ask_yes_no` |
| 1B2Fh | `cleanup_and_exit` |
| 1B44h | `main_wrapper` |
| 1B54h | `get_kernel_segments` |
| 1B7Bh | `copy_drive_dpb` |
| 1BA4h | `get_drive_dpb` |
| 1BC9h | `get_open_drive_vector` |
| 1BD2h | `set_process_keep` |
| 1BF6h | `xios_read` |
| 1BFBh | `xios_write` |
| 1BFEh | `xios_transfer` |
| 1C2Ch | `console_write_block` |
| 1C5Ah | `printf` |
| 1C9Fh | `sprintf` |
| 1CB7h | `format_output` |
| 1EA3h | `format_unsigned_word` |
| 1F24h | `add_decimal_strings` |
| 1F7Ch | `format_unsigned_long` |
| 200Ch | `runtime_long_load` |
| 2015h | `runtime_long_store` |
| 2020h | `runtime_long_add` |
| 202Dh | `runtime_long_subtract` |
| 203Ah | `runtime_long_remainder` |
| 2047h | `runtime_long_divide` |
| 214Eh | `runtime_long_compare_not_equal` |
| 2160h | `runtime_long_compare_greater` |
| 2188h | `runtime_long_compare_entry_zero` |
| 218Ch | `runtime_long_compare_entry_flags` |
| 2191h | `runtime_long_compare_entry_signed` |
| 2196h | `runtime_long_add_assign` |
| 21A1h | `runtime_long_subtract_assign` |
| 21ACh | `runtime_long_and_assign` |
| 21B7h | `runtime_long_or_assign` |
| 21C2h | `runtime_long_xor_assign` |
| 21CDh | `runtime_long_shift_left_assign` |
| 21DAh | `runtime_long_shift_right_assign` |
| 21E7h | `runtime_long_multiply` |
| 220Bh | `runtime_long_stack_reorder` |
| 2214h | `runtime_long_stack_rotate` |
| 221Dh | `runtime_long_stack_swap` |
| 222Eh | `runtime_detect_os` |
| 22CBh | `runtime_probe_file_support` |
| 22F3h | `strcat_unused` |
| 22F9h | `strcpy` |
| 232Ch | `strcmp_unused` |
| 2353h | `stricmp_unused` |
| 239Bh | `strlen` |
