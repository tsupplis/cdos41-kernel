# FM — C reconstruction

Experimental reconstruction of `extra/fm.cmd`. The original remains the
version shipped on the disks. Promote a replacement only after comparative
user testing of layout, configuration, keys and file operations.

| Component | Status |
|---|---|
| Original CMD container | All 73,856 bytes covered and checked against SHA-256 |
| First-pass disassembly | 23,716 reachable instructions; 3,486 CODE bytes still unclassified |
| ASM86 reconstruction | Not yet implemented; the listing is not assembler source |
| Configuration parser | First C module; native and host regression target |
| Menu metadata | 28 entries recovered; labels, commands and selection bounds checked |
| UI cores | Layout, frames, colours, key translation and navigation tested separately; native integration pending |
| Directory display | Formatting, sorting and bounded BDOS search tested; interactive integration pending |
| Operations, launch | Not implemented |
| Distribution replacement | Not enabled |

## Build

Uses `drccpm_cc` and `drccpm_link`, following WINDOW and CHKDOSFS.

```
make              # FMCHECK tests reconstructed cores; not a file manager
make check        # reference byte coverage, host and native core checks
make reference    # explicitly regenerate the reviewed reference listing
make clean
```

The executable is `fmcheck.cmd`; there is deliberately no replacement
`fm.cmd` yet. `disassemble.py` uses NDISASM only as a decoder, not an assembler.
No parent build or media recipe is changed.

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
| `config.c` (started) | Configuration keywords and numeric assignments |
| `menu.c` (started) | Ordered file/setup menu descriptors |
| `layout.c` (started) | All five menu positions and expanded bottom menu |
| `screen.c` (started) | Cursor protocol and output sink; native transactions pending |
| `frame.c` | Border cells and original colour translation |
| `keys.c` | Terminal remapping and key normalization |
| `navigate.c` | Selection and viewport movement; event-loop integration pending |
| `dirlist.c` | Original display-name formatting and sorting |
| `scan.c` | Bounded read-only search with injected BDOS operations |
| `actions.c` (planned) | Copy, rename, delete, type and print |
| `launch.c` (planned) | External tools, command shell, return to FM |
| `native.c` (started) | Native BDOS search callbacks; console backend pending |
| `fm.c` (planned) | Application state and event loop |

Keep all original layouts, prompts and bindings traceable to the reference.
Do not mix raw keys with file-operation logic, or terminal output with disk
access. Start with a read-only browser; destructive actions follow their
own comparative tests.

## Configuration compatibility

The supplied `extra/fm.cfg` describes lookup on the system drive, user 0
(FAT root directory). Preserve the original file unchanged. Native lookup,
line handling and defaults are still to be integrated and verified.

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
are assigned as bytes. No range clamp is invented. Whole-file handling and
interactions between settings are not yet claimed compatible.

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

This is not yet a native rendering backend. The original wraps output through
CODE `6E01h`/`6DECh` and uses a console lock at `6FB3h`; replacing these with
unprotected character writes would miss concurrency behaviour. The native
sink must handle that transaction before a live preview is enabled. The C border renderer and colour mapping are now recovered and tested against
the original DATA tables (512 colour cases and six border comparisons). Native
console output, resizing and repaint integration remain.

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
Actual input acquisition, terminal-table discovery and context-sensitive actions
still need integration; this is not an interactive file manager yet.

## Selection and scrolling

`navigate.c` translates the selection and viewport routines at CODE
`88D7h..89FDh`, `8FFDh..9028h`, `90B7h..91DCh` and `92EDh..933Ah`.
Left/Right wrap at the list ends; Up/Down do not. On an incomplete final row,
Down can scroll the viewport without changing the selected entry. First/last
movement uses the normalized control values; their meaning remains contextual.

The core has no disk or screen side effects. Tests cover ten reference-derived
boundary cases, 121,200 visibility/alignment invariants and native DR C cases.
These are not a full differential execution of the original navigation loop.
Marking, filename search and event-loop integration remain pending.

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
host directory through emu2 and verifies its files are unchanged. This is not
yet a live CDOS FAT-directory test. Media detection, paths, metadata interpretation
and integration into the browser remain pending.

The native callback table is assigned at runtime: DR C 1.11 produced incorrect
code-address relocations for its static aggregate initializer. The native test
covers this compiler constraint.

## Host preview

`make preview` produces `preview.svg` using the C layout, frame and colour
modules. It shows the default blank file pane and original menu labels.
It is not a running FM: directory contents, selection, key legend and native
console transactions are not yet integrated. Do not use it as parity evidence.

## Acceptance before replacement

Compare original and C version on disposable disks: initial layout, resize and
redraw, original FM.CFG, all keys and menus, CP/M users and FAT directories,
selection and sorting, command arguments, external program return, and each
file operation including cancellation and errors. User testing must approve
layout and behaviour before media changes.
