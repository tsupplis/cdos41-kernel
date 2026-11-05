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
| UI, directory model, operations, launch | Not implemented |
| Distribution replacement | Not enabled |

## Build

Uses `drccpm_cc` and `drccpm_link`, following WINDOW and CHKDOSFS.

```
make              # FMCHECK is a configuration test, not a file manager
make check        # reference byte coverage and C parser checks
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
| `screen.c` (planned) | Frames, windows, colours, clipping and redraw |
| `keys.c` (planned) | Terminal input translated into FM actions |
| `directory.c` (planned) | Drives, users, FAT paths, sorting and selection |
| `actions.c` (planned) | Copy, rename, delete, type and print |
| `launch.c` (planned) | External tools, command shell, return to FM |
| `native.c` (planned) | BDOS interfaces and platform-dependent access |
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

## Acceptance before replacement

Compare original and C version on disposable disks: initial layout, resize and
redraw, original FM.CFG, all keys and menus, CP/M users and FAT directories,
selection and sorting, command arguments, external program return, and each
file operation including cancellation and errors. User testing must approve
layout and behaviour before media changes.
