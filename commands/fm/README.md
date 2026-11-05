# FM — C reconstruction

Experimental reconstruction of `extra/fm.cmd`. The original remains the
version shipped on the disks. Promote a replacement only after comparative
user testing of layout, configuration, keys and file operations.

| Component | Status |
|---|---|
| Original CMD container | All 73,856 bytes covered and checked against SHA-256 |
| First-pass disassembly | 23,716 reachable instructions; 3,486 CODE bytes still unclassified |
| ASM86 reconstruction | Not yet implemented; the listing is not assembler source |
| Configuration | Original defaults and FM.CFG assignments; local/system lookup integrated |
| Menus | 28 descriptors checked; Tab focus, scrolling and setup submenu integrated |
| UI cores | Read-only pane composes names, key translation, navigation and rendering; live read-only browser validated |
| Directory display | Sorted file/directory views, FAT child/parent navigation and CP/M users |
| Selection | Per-drive wildcard subsets, configured drive picker, comma/Insert marking and Delete unmarking |
| Type | Internal read-only paged viewer; menu or F2/Ctrl-B, marked files or current file |
| Print | Internal list-device printing; selected files, cancellation and selection retention |
| Rename | Per-file prompt; skip/cancel, native collision refusal and retained selections |
| Delete | One explicit confirmation; failed files retained, protected attributes unchanged |
| Copy | Drive, new-name, CP/M user, FAT directory and Dir #1/#2 destinations implemented; disk swapping pending |
| Launch | Not implemented |
| Distribution replacement | Not enabled |

## Build

Uses `drccpm_cc` and `drccpm_link`, following WINDOW and CHKDOSFS.

```
make              # FMCHECK core tests and experimental FMVIEW
make check        # reference byte coverage, host and native core checks
make check-live   # disposable FAT/configuration and CP/M-user scenarios
make reference    # explicitly regenerate the reviewed reference listing
make clean
```

The executables are `fmcheck.cmd` and `fmview.cmd`; there is no replacement
`fm.cmd` yet. `disassemble.py` uses NDISASM only as a decoder, not an assembler.
No parent build or media recipe is changed. Maintained LINK86 `.inp` files follow
PRINT and avoid the command-tail limit when linking the shared modules.

Native DR C/LINK86 wrappers share scratch files: concurrent compiles can
produce an object from the wrong source or corrupt compiler input. The Makefile
serializes its targets even with `-j`. After building, independent live-test
Python scripts may be run concurrently in their separate disposable machines.

## Reference

The CMD has a 128-byte header, 58,176-byte CODE group, 15,504-byte DATA group,
and 48 bytes of record padding. DATA may grow to 64 KiB. The embedded runtime
identifies Digital Research C 1.11, small model, 27 August 1984. This identifies
the linked runtime; it does not prove the source compiler for every module.

`fmorg.dis` follows direct branches and calls from identified entry points.
It preserves each original byte, including unknown areas, without pretending
unknown bytes are data. `symbols.json` records confirmed function names and
addresses. Unresolved indirect transfers are listed at the end. Byte coverage
is not assembly equivalence, code comprehension or functional parity.

## Modular implementation

| Module | Responsibility |
|---|---|
| `config.c`, `cfgio.c` | Configuration parsing and native FCB loading |
| `menu.c` | Ordered file/setup menu descriptors |
| `layout.c` | All five menu positions and expanded bottom menu |
| `screen.c` | Cursor protocol and output sink |
| `frame.c` | Border cells and original colour translation |
| `keys.c` | Terminal remapping and key normalization |
| `navigate.c` | Selection and viewport movement |
| `dirlist.c` | Original display-name formatting and sorting |
| `scan.c` | Bounded read-only search with injected BDOS operations |
| `select.c`, `selectio.c`, `marks.c` | Subset input, drive selection and display-only marks |
| `type.c`, `typeio.c`, `viewer.c` | Text conversion, native read-only FCB stream and paged Type action |
| `prtext.c`, `printjob.c`, `printio.c` | Printer text conversion, selected-file batch and native list ownership |
| `renjob.c`, `renio.c` | Rename selection loop and validated native rename |
| `deljob.c`, `delio.c` | Confirmed file deletion and concrete-name BDOS adapter |
| `copyjob.c`, `copynam.c`, `copyio.c` | Copy selection, validated destination names and transactional record transfer |
| `fatdest.c` | Verified process-local FAT destination aliases without changing the source mapping |
| `book.c` | Session bookmarks with independent directory identities and navigation clones |
| `launch.c` (planned) | External tools, command shell, return to FM |
| `event.c` | Read-only input/navigation/repaint loop and Escape cleanup |
| `conio.c` | Direct-screen lock ownership, BDOS-output boundary and mapped input |
| `browse.c` | Read-only pane, selection highlight and repaint |
| `term.c`, `fmxios.a86` | CDOS window discovery and guarded direct-screen backend |
| `native.c` | Native BDOS search, input and FAT directory mapping |
| `focus.c` | Menu focus, scrolling and setup submenu |
| `fmview.c` | Experimental read-only application and view transitions |

Keep all original layouts, prompts and bindings traceable to the reference.
Do not mix raw keys with file-operation logic, or terminal output with disk
access. Start with a read-only browser; destructive actions follow their
own comparative tests.

## Configuration compatibility

The supplied `extra/fm.cfg` describes lookup on the system drive, user 0
(FAT root directory). Preserve the original file unchanged. Native lookup, line handling and defaults
are integrated; OVPMODE remains under investigation.

The actual parser recognises these settings, beyond the eight colour settings
in the supplied example:

| Settings | Purpose |
|---|---|
| `OBJECT FG COLOR`, `OBJECT BG COLOR` | File window |
| `COMMAND FG COLOR`, `COMMAND BG COLOR` | Command menu |
| `PROMPT FG COLOR`, `PROMPT BG COLOR` | Prompt |
| `KEY FG COLOR`, `KEY BG COLOR` | Key legend |
| `MENU SIZE`, `PROMPT SIZE`, `MENU POSITION` | Layout |
| `TOP MARGIN`, `BOTTOM MARGIN`, `LEFT MARGIN`, `RIGHT MARGIN` | Layout |
| `OVPMODE` | Recognised; operational meaning still under investigation |

Keywords include a literal `=`. Letter case is ignored; spacing is significant.
Numeric values skip ASCII spaces, require decimal digits, wrap at 16 bits and
are assigned as bytes. The parser does not clamp values. FMVIEW rejects invalid
colours or geometry before opening its display. Full-file input accepts CR/LF,
Ctrl-Z and a final unterminated line; oversized lines are discarded as a unit.

`cfgio.c` tries the current location, then the floating system drive P: in
user 0. It restores the user/DMA and commits settings only after successful
read and close. The original release FM.CFG and a custom left-hand colour
configuration are covered by live tests. System-drive lookup is also tested
from another drive in user 4. Complete original configuration semantics,
including OVPMODE and compact/horizontal menus, remain unfinished.

The example's prose calls the first two windows WINDOW and MENU, but its
actual assignments use OBJECT and COMMAND. Match the executable's parser.

## Terminal dispatch

Two verified DATA tables at `0ADEh` and `0B00h` supply terminal callbacks.
The selector at `0ADCh` initially points to the first; CODE `7970h` selects
the second. Their nonzero entries are now disassembly roots, checked against
the original table words on every reference check. Slot meanings remain
unassigned unless traced.

The first table positions the cursor through `ESC Y`, followed by row+32
and column+32 (CODE `6CCDh`). Its output routines use BDOS 6. This supports
keeping terminal rendering separate from navigation and file operations.
The runtime menu-handler arrays are allocated dynamically from DATA `1C1Eh`
(17 file actions) and `1C40h` (11 setup actions). CODE `64FEh..6516h` and
`6623h..663Bh` copy these handlers into the arrays used by the event loop.
Menu descriptors come from pointer tables `1C56h` and `1C78h`; record offsets
+2/+8/+10 hold label/command/description and +4/+6 hold selection bounds.

`menu.c` preserves these strings and bounds without executing any action.
`tests/menu.py` compares the compiled descriptors directly to the original
binary, not just a second transcription. `menus.json` keeps handler and DATA
record addresses for review. Several entries share the external-tool handler,
including disk copy/format and setup tools; their command strings differ.

## Keys and command line

The original legend gives the following file-view bindings. Dispatch and
context-specific variations still need execution tests.

| Key | Action |
|---|---|
| Escape | Exit/back |
| F1 / Ctrl-A | Help |
| F2 / Ctrl-B | Type |
| F3 / Ctrl-C | Repeat |
| F4 / Ctrl-D | Cancel |
| F5 / Ctrl-E | Run |
| F6 / Ctrl-V | Edit |
| F7 / Ctrl-W | Directory 1 |
| F8 / Ctrl-X | Directory 2 |
| F9 / Ctrl-Y | Directory view |
| F10 / Ctrl-Z | Command |
| Arrows, typed filename | Move to a file |

Alternate terminal text mentions space/backspace navigation and TERM.DAT.
Do not replace this with a PC-only scan-code assumption. The runtime lowercases
the command tail before argument parsing. Application arguments and switches
are not yet established; do not invent new syntax.

## Default layout

`layout.c` translates MENU POSITION=1..5 (CODE `8032h..8565h`). With 24 rows,
80 columns and the defaults restored by `5D3Ah`, the outer rectangles are:

| Region | Row | Column | Width | Height |
|---|---:|---:|---:|---:|
| Files | 0 | 0 | 60 | 21 |
| Command menu | 0 | 60 | 20 | 21 |
| Prompt | 21 | 0 | 80 | 1 |

Coordinates are zero-based. Borders are available in the host preview; the
remaining bottom area and key legend are not drawn yet. Positions 1/2/3/4/5 put the menu right/bottom/left/top/bottom respectively.
Position 5 uses a one-row menu; position 2 uses three or eight rows depending
on DATA `0D00h`. The source of that mode flag still needs tracing. Invalid rectangles are rejected before drawing.

`tests/layout.py` executes the original geometry calculation with a
strict, limited instruction interpreter and compares 480 configurations with
the compiled C module. Native DR C checks also cover every position. This checks geometry, not
the eventual screen appearance.

## Rendering boundary

`screen.c` emits the recovered cursor-position and visibility sequences to an
injected sink. Positioning is checked against supplied terminal dimensions.
Tests capture bytes on both the host and the actual DR C executable.

The border renderer and colour mapping are checked against the original DATA
(512 colour cases and six border comparisons). `term.c` supplies the native
locked-cell backend; `conio.c` releases that lock before BDOS output to avoid
deadlock. Resizing and complete original redraw behaviour remain pending.

## Console ownership and input

The original acquires its direct-screen semaphore at `6DC3h`, releases it at
`6DD7h`, and temporarily releases/reacquires it around BDOS output through
`6E01h`/`6DECh`. This is a direct-memory lock, not an output-stream mutex.
`conio.c` keeps that ownership explicit and releases it before input polling.
Output failures still attempt to restore prior ownership; failed acquisition
never leaves the state marked locked. Host tests exercise failure paths and
input mapping; native DR C tests verify callback ordering and normalized input.

`fm_native_key` uses BDOS 6 readiness/read calls. Input passes through the
recovered terminal remapping and normalization, preserving a real NUL byte.
`term.c` now discovers the current console through a local WINDOW-style XIOS
bridge (`fmxios.a86`). It requires BDOS identity 1441h, validates console number
and image pointer, writes only within the 24x80 virtual image while locked,
and refreshes the physical window after unlocking. The status line is untouched.
Host tests simulate the gateway and verify discovery, bounds and lock ordering;
the PCE scenarios exercise actual display, keyboard input and exit cleanup.
Alternate terminal-map discovery remains pending.

## Key translation

`keys.c` reproduces CODE `66EEh..6749h` (terminal mapping) and
`68C8h..6909h` (normalization). Mapping is sequential: an output byte may
match a later source entry. The source-table NUL terminator is respected.

| Translated input | FM control value |
|---|---|
| C8h / D0h / CBh / CDh | 11 / 10 / 8 / 12 |
| C7h or C9h | 1 |
| CFh or D1h | 26 |
| D2h / D3h | comma / 127 |
| Tab | 3 |
| BBh or E1h | question mark |
| Other bytes | Unchanged |

All 256 inputs are compared with the original machine-code routine.
Native DR C tests cover navigation values, Escape and cascading mappings.
Native PC input is integrated. Alternate terminal-table discovery and the full
set of context-sensitive actions remain pending.

## Selection and scrolling

`navigate.c` translates the selection and viewport routines at CODE
`88D7h..89FDh`, `8FFDh..9028h`, `90B7h..91DCh` and `92EDh..933Ah`.
Left/Right wrap at the list ends; Up/Down do not. On an incomplete final row,
Down can scroll the viewport without changing the selected entry. First/last
movement uses the normalized control values; their meaning remains contextual.

The core has no disk or screen side effects. Tests cover ten reference-derived
boundary cases, 121,200 visibility/alignment invariants and native DR C cases.
These are not a full differential execution of the original navigation loop.
Comma/Insert marking and Delete unmarking are implemented. Filename search
remains pending.

## Directory display

`dirlist.c` preserves the 12-column name conversion at CODE `0DC8h` and
pointer sorting at `20A4h`. Attribute bits are stripped, basename padding is
removed, and the extension remains space-padded. The original raw-byte test
for adding the dot is retained. Sorting is case-sensitive over the display
name; it does not regroup by extension or invent a directories-first policy.
The original sorts separate file and directory lists.

The sort preserves the original pivot/swaps but iterates its larger partition
to bound stack depth. Checks cover name fixtures, all 2,048 attribute-bit
combinations, ordering permutations and duplicate/sorted/reversed lists.
Native DR C checks cover formatting and sorting too.

Enumeration at `0E70h` uses BDOS search functions 17/18 and a DMA buffer.
Returned directory entries use bit 40h at offset 10h to identify directories;
this is the BDOS representation, not the raw FAT directory layout.

`scan.c` now enumerates one explicit drive/user into caller-owned storage,
retains the raw 32-byte entries and reports truncation separately from success.
The caller supplies the known media type: CP/M allocation bytes must never be
mistaken for directory flags. Drive and FAT mapping are unchanged; user and
caller-supplied DMA address are restored on completion, truncation and invalid
search results. The caller must supply a DMA address in its own data segment.
Search state is consumed, so searches cannot be interleaved.

Host tests cover all four DMA slots, user filtering, FAT/CP/M classification,
capacity boundaries and cleanup. The native DR C executable searches a disposable
host directory through emu2 and verifies its files are unchanged. PCE tests
exercise FAT child/parent navigation and CP/M user selection. Typed full paths and detailed metadata display remain pending.

The native callback table is assigned at runtime: DR C 1.11 produced incorrect
code-address relocations for its static aggregate initializer. The native test
covers this compiler constraint.

## Read-only browser integration

`browse.c` connects sorted display-name pointers, normalized keys, viewport
movement and cell rendering. It repaints the pane before drawing names, so
short or empty lists cannot leave stale entries. Selection is highlighted;
output failures propagate to the caller. Integration tests exercise movement,
scrolling, repaint, clipping and empty lists; DR C tests exercise key dispatch.

Column spacing is supplied explicitly. The integration fixture uses 14 cells;
this is not yet a claim that every original FM grid mode has been recovered.
`event.c` now drives the pane through the console callbacks: idle input does
not repaint, navigation repaints under screen ownership, and Escape exits with
no lock held. Failed rendering also releases ownership. Tests cover that full
sequence. Alternate terminal maps and the complete action dispatcher remain pending.

## Experimental live browser

Run `FMVIEW` without arguments on CDOS 4.1. It is an experimental
file manager, not the replacement FM.CMD. Copy, Rename and Delete modify files; Type and Print only read them.

| Control | Current behaviour |
|---|---|
| Arrows, Home/End | Move selection and scroll |
| Tab | Switch between files and menu |
| Enter in menu | Open File Directory, Subset, Drive, Type, Print, Copy, Rename, Delete or Set Up System; other actions report unavailable |
| Subset | Enter a wildcard filespec (12 characters maximum); native BDOS parsing, per-drive filter |
| Drive | Select a configured drive; Escape cancels |
| Comma / Insert | Mark the current file without moving |
| Delete | Unmark the current file; never deletes a file |
| Delete menu | One Y + Enter confirmation for marked files, or current file; other answers cancel |
| Copy menu | Copy marked/current files to a drive, new name, CP/M user or FAT directory; any key stops transfer |
| Rename menu | Prompt for each marked file, or current file; blank skips, Escape cancels remaining files |
| Print menu | Print marked files, or the current file; any key stops printing |
| F2 / Ctrl-B / Type menu | Display marked files, or the current file when none are marked |
| F9 | Show FAT directories or CP/M users 0–15 |
| F3 / F4 in directory view | Set Dir #1 / Dir #2 to the highlighted directory or user |
| F7 / F8 in file view | Navigate to Dir #1 / Dir #2 |
| F7 / F8 in Copy menu | Copy to Dir #1 / Dir #2 |
| Enter in directory view | Enter selected directory/user; `..` returns to the parent |
| Escape | Back from setup/menu/directory view; exit from files |

FM.CFG controls colours and geometry. Right/left vertical menus are tested live;
compact/horizontal layouts remain provisional. Search retains at most 256
entries and reports truncation. FAT directory mapping is process-local, and
exit restores the initial drive and CP/M user. Cancelling a picker preserves
marks and the file position, including after switching between pickers. Accepting
a directory, drive or subset clears marks. Invalid subsets leave the filter
unchanged. External launching, typed full paths and filename-search selection
remain pending. Copy destinations are described below.

The XIOS adapter locks only while painting. ESC 6 disables programmable-key
expansion while open; exit restores its previous state. Full-word version checks
use the local BDOS bridge: DR C's `__BDOS` wrapper returns only a byte.

After `make`, `make check-live` runs independent disposable PCE scenarios:
defaults, release FM.CFG, custom left-hand colours, and CP/M users/system FM.CFG.
Checks cover selection attributes, scrolling, setup/menu return, FAT child/parent
entry, cancellation, user 0/4/15, empty views and clean exit. The custom scenario
also covers subsets, drives, marks and nested picker cancellation. Data images must
remain byte-identical and the parent shell must retain its directory/user.
Each emulator exits after its scenario, with a 90-second timeout; artifacts
remain in the printed temporary directories. This is not full original-FM
parity or approval to replace the distributed binary.

`select.c` handles bounded input and mask matching; `selectio.c` adapts BDOS
parsing and the configured-drive table; `marks.c` owns display-only marks.
`tests/pickers.py` exercises the actual FMVIEW controller with a simulated disk
adapter. Selection/marking passes host, native and live FAT checks. CP/M user navigation
and configuration fallback also pass with the rebuilt isolated boot fixture.
Live tests accept `--boot-image`; the CP/M-user test also accepts `--base-image`
so isolated fixtures can be used during concurrent media rebuilds.

## Internal Type action

`viewer.c` follows CODE `3AB8h`/`3E02h`: seven-bit text, Ctrl-Z or physical EOF,
CR-driven rows, ignored LF, eight-column tabs and 78-column clipping without
wrapping. Return advances a page; another key cancels. At file end, Return
continues to the next selected file; the final file waits for any key.
Completed files are unmarked. Cancelled, unprocessed and failed files remain
marked. Read errors are distinguished from EOF, avoiding false completion.

`typeio.c` uses only FCB open/read/close and DMA selection. Every read restores
the caller's DMA; disk and keyboard calls occur outside screen ownership.
Host tests cover all byte values, paging, selection order, cancellation,
rendering/I/O failures and cleanup. Live PCE checks pass for tabs, pagination,
Ctrl-Z, completion and cancellation back to the browser, with an unchanged
data image. The viewer currently uses a fixed 24-row
screen; configuration-dependent viewer geometry still needs comparison.

## Internal Print action

`printjob.c` follows CODE `3E1Ah`/`4017h`. It conditionally attaches the current
logical printer (BDOS 161), writes through BDOS 5 and detaches with BDOS 159.
It does not invoke a spooler or change printer selection. Any key stops the
batch after the current source character; completed files are unmarked and
unfinished or failed files remain marked.

Text is seven-bit, with eight-column tabs and CR resetting the column. LF and
form feed pass through; other controls become spaces. Ctrl-Z, raw FFh and
physical EOF end input, matching the original. Each opened file gets a trailing
form feed, including on cancellation. Read errors remain distinct from EOF;
cleanup detaches only after a successful attach. Host tests cover conversion,
selection order, cancellation, errors and native BDOS call sequences. Live tests
capture printer bytes to a temporary file; no physical printer is used. The
live two-file run passes byte comparison and completion/unmarking checks.
For files without Ctrl-Z, final BDOS-record zero padding becomes spaces, as
in the original. Printer capture uses CGA: PCE VGA overlaps port 3BCh.

## Rename

`renjob.c` follows CODE `4E24h`/`4FD3h`: one uppercase name per selected file,
12-character input, blank to skip, Escape to cancel remaining prompts and
Ctrl-X to clear input. Drive prefixes and invalid names retry the same file;
rename failures retain the file and proceed to the next. Successful names are
rescanned and sorted, with remaining marks remapped by filename.

`renio.c` uses BDOS 152 and 23. It accepts concrete bare 8.3 names only and
never deletes or overwrites a destination. Wildcards, paths, passwords and
trailing tokens are rejected before the mutation call. Existing destinations
are left to BDOS's collision check; no preflight race is introduced. Host tests
cover parsing, native errors, per-file decisions and selection retention.
`tests/rename_live.py --media fat|cpm --boot-image PATH` checks disposable files,
including collision refusal, cancellation and content preservation. Both FAT
and CP/M live Rename scenarios pass. FM selects BDOS return-error mode (45)
for its own process so a collision returns to the dialog instead of aborting FM.

## Delete

`deljob.c` follows CODE `4FFEh`/`5165h`: `ERASE, are you sure (Y=yes) ? `
applies to the selected batch. Y/y followed by Enter confirms; blank, another
answer or Escape cancels without changing selections. Delete removes only
concrete files, never directories or wildcard names. Successful files disappear
after rescan; failed files remain marked and the first failure is selected.

`delio.c` calls BDOS 19 once per file using a fresh FCB. It does not clear
read-only/system attributes, retry failures or force deletion. Host tests cover
confirmation, selection mapping, protected failures and unchanged input data.
The live Rename scenarios accept `--delete` to additionally check refusal,
cancellation, confirmed removal and preservation of a read-only selected file
and unselected files on disposable FAT and CP/M disks. Both live scenarios
pass, including byte comparisons of every surviving file.

## Copy

`copyjob.c` follows CODE `4766h`: copy marked files, or the current file when
none are marked. Completed files are unmarked; the first failure or any-key
cancellation stops the batch and retains unfinished selections. The destination
menu supports A–D and the configured-drive picker. Same-drive copies require
a different filename, CP/M user area or FAT directory.

`copynam.c` implements Copy to New Name: `Copy <name> to ? `, up to 15 input
characters, optional `A:`–`P:` prefix and one concrete 8.3 filename. Blank skips
that file; Escape cancels remaining prompts. Invalid or identical destinations
retry. Successful copies leave source files unchanged and clear their marks.

Copy to Dir on CP/M media selects user 0–15. Each native source/destination
operation selects its own user; all exits restore the caller's user and DMA.
Cancelling the picker preserves source selections.

On FAT media, Copy to Dir selects a child directory or the parent entry when
available; the synthetic `.` entry denotes the current directory and is refused
as the source location. `fatdest.c` maps the destination through an unused
N:/O:/P: alias using extended BDOS open. Read-only native inspection verifies
its physical drive, media sequence and directory identity. It never replaces
an inherited alias; if none is available, copying is refused. Owned aliases
remain process-local until process termination because extended close is not
an unmap operation. The source drive mapping remains unchanged throughout.
This picker selects a destination from the current directory list; arbitrary
path input and single-drive disk swapping remain pending.

Dir #1/#2 are session bookmarks, set with F3/F4 in directory view from the
highlighted directory or CP/M user. The confirmation is `DIR #1 set to: ` or
`DIR #2 set to: ` followed by its display location. F7/F8 navigate from file
view, or copy the selected files when the Copy menu is active. Unset bookmarks
report `first set Dir #1` or `first set Dir #2`.

CP/M bookmarks capture their drive/user values. FAT bookmarks pin an owned
alias and save physical drive, media sequence and directory cluster; navigation
uses a separate working clone, so entering a child cannot change the saved
bookmark. The saved signature is checked against the kernel's current mapping,
but this does not force a media login or proactively detect disk replacement.
FAT bookmark use is supported on stable mounted media only; disk swapping
remains unsupported. Two FAT bookmarks and a working clone can occupy all
three floating aliases. An operation requiring another alias then refuses
safely rather than replacing an inherited, pinned or active source mapping.
Bookmarks are not persisted in FM.CFG.

`copyio.c` copies full 128-byte records, including Ctrl-Z and binary data.
Like the original, writable destinations are replaced without confirmation;
read-only destinations are refused. Unlike the original fixed `COPYTMP.$$$`,
unused temporary and backup names protect existing files. Commit follows
successful reads, writes and closes; failed replacement attempts restore the
old name. A failed rollback reports the retained recovery filename. No source
attributes are propagated. Host tests cover cancellation, I/O failures,
collisions, rollback and selection retention.

`tests/copy_live.py --media fat|cpm --boot-image PATH` checks disposable
FAT→CP/M and CP/M→CP/M copies. Both pass exact binary comparisons, writable
replacement, read-only refusal, same-drive refusal, selection retention and
temporary-file cleanup. The named-copy scenarios additionally exercise same-drive FAT and CP/M
destinations, invalid-name retry, skip/cancel and explicit drive prefixes.
Both named-copy scenarios pass. The CP/M scenario also passes user 0→1
copying, same-user refusal, picker cancellation and restoration of the source
user, with exact destination-byte comparison.

`tests/fatdest_live.py --boot-image PATH` passes on a disposable FAT image:
current-location refusal, picker cancellation, writable replacement with exact
binary records, read-only failure followed by batch stop, retained selections,
unchanged source files and root view after reopening FM in a fresh process.
The corresponding target is `make check-live-fatdest`. Host adapter tests
cover alias ownership and verification; the live test checks observable
mapping restoration, not internal kernel reference counts.

`tests/book_live.py --media fat|cpm --boot-image PATH` passes for both media.
It verifies F3/F4 setting, F7/F8 navigation and Copy destinations, exact binary
payloads, unchanged source files and restored shell context. The FAT scenario
also verifies refusal when aliases are exhausted and return to the saved
directory after entering a child through its navigation clone. The CP/M
scenario revisits bookmarks after an ordinary user-area change. Run these with
`make check-live-book-fat` and `make check-live-book-cpm`.

## Host preview

`make preview` produces `preview.svg` using the C layout, frame and colour
modules. It shows synthetic filenames, a selected entry and the original menu labels.
It is a synthetic preview, separate from the live FMVIEW tests. Do not use it
as parity evidence.

## Acceptance before replacement

Compare original and C version on disposable disks: initial layout, resize and
redraw, original FM.CFG, all keys and menus, CP/M users and FAT directories,
selection and sorting, command arguments, external program return, and each
file operation including cancellation and errors. User testing must approve
layout and behaviour before media changes.
