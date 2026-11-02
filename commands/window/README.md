# WINDOW and WMENU

Shared C implementation for CCP/M 3.1 and CDOS 4.1, checked against the
retained CDOS OEM WINDOW/WMENU. This is a source rewrite, not a byte-identical
disassembly. Both commands build in this directory.

```
make -C commands/window
make -C commands/window check
make check-window
make check-wmenu
```

## Public interface

BDOS 12 selects the OS-native public numbering: CCP/M uses **N=0..3** and
CDOS uses **N=1..4**. Both map to XIOS indices 0..3 internally.

```
WINDOW VIEW
WINDOW TOP N=2
WINDOW FULL N=1
WINDOW CHANGE N=1 PR=4,PC=5,NR=10,NC=40,VR=1,VC=1,TR=ROW,D=COLOR,FG=WHITE,BG=BLUE
WINDOW WRITE N=1 TYPE=WINDOW,FILE=B:WINDOW1.TXT
WINDOW WRITE N=1 TYPE=CONSOLE,FILE=B:CONSOLE1.TXT
WINDOW WRITE N=1 TYPE=SETUP,FILE=B:WSETUP.SUB
```

Coordinates are one-based. CHANGE parses and validates its fields before
modifying XIOS state; extents are clipped to the screen. WINDOW snapshots
capture the visible virtual-screen rectangle; CONSOLE captures all 24 rows.
Both trim trailing spaces per row, as the OEM does. SETUP saves commands for
**all four windows**, even though the command still requires a valid N.
Record padding follows Ctrl-Z; bytes beyond that text EOF are not significant.

## WMENU

Install WMENU once, then press **Ctrl+Alt+0** (top-row zero) or
**Ctrl+Alt+Esc** to open its menu. Ctrl+keypad-Plus remains available.
These global shortcuts are decoded by the XIOS keyboard handler, not by
WMENU; use a system image built with the corresponding XIOS changes.
The manager detaches and waits through the existing XIOS services; it is
not a DOS TSR.

The highlighted main menu uses arrows or Space to select Place, Size,
Scroll, Tracking, Display, Color, Write or Abort; Return opens the selection.
Digits 1..4 select a window. Esc hides the main menu without unloading it.

Geometry uses arrows. Tracking/Display use Up/Down or Space. Color uses
Left/Right to choose foreground/background and Up/Down to change it.
Esc or Return leaves these editing submenus with changes in effect.
Write defaults to `A:WINDOWn.TXT` on the current drive, permits a replacement
filename and output-type selection, and writes on Return; Esc cancels.
Abort followed by Return unregisters the manager and exits.

The status-line ABI passes the buffer offset in CX and its segment in DX.
Reversing these arguments was responsible for the trial rewrite's blank menu.
The bridge, gateway and data pointers retain the existing XIOS ABI; no
kernel data layout is changed.

## Modules and verification

`command.c` handles command/field parsing. `win.c` handles shared state,
XIOS services and exports. `wmenu.c` implements the manager. `xios.a86`
provides the C/far-memory bridge; `format.c` supplies small-model formatting.
`hostcheck.c` checks parsing/service dispatch against simulated data;
`livetest.c` exercises GLASS geometry/colors/TOP against the real XIOS and
restores the original state. These test programs are not distribution tools.

`make check-window` runs OEM and rebuilt commands on disposable CDOS/FAT
images. It checks VIEW, CDOS 1..4 bounds, geometry/colors, all three export modes,
GLASS, installation/duplicate detection, highlighted menu navigation,
committed Size/Color/Tracking edits, Write cancellation and manager exit.
Setup files and meaningful text before Ctrl-Z are compared. OEM bytes after
Ctrl-Z can contain stale runtime-buffer data and are deliberately ignored.
`make check-wmenu` checks all three wake shortcuts, hide and clean exit,
that hotkeys do not leak when no manager is installed, and plain zero input.

This establishes the exercised command/menu paths, not exhaustive equivalence
for every filename-editing sequence, video adapter, asynchronous switch or
error path. Original programs remain in `base/` for further comparisons.

## Immediate colour repaint

The 4.11 colour operation changes both the current output attribute and every
existing attribute byte in the 24x80 virtual console. The rewrite initially
changed only the former, leaving old characters and blank cells unchanged
until rewritten or cleared. Shared WINDOW/WMENU code now repaints the backing
image under the original per-console mutex, synchronizes a full foreground
console first, and asks XIOS to redraw the rectangle. Characters and cursor
are preserved; the status line is excluded. Existing intensity/blink bits in
the current attribute are preserved when foreground/background change.

`tools/window_color_check.py` compares actual character **and attribute** bytes
against 4.11 for all four CARDDECK stages, a full-screen colour change and a
background-console change, without clearing between operations. The WMENU
comparison also checks the screen attributes after an interactive colour edit.
This fixes an omitted repaint operation; no command-line syntax changes.

`make -C commands/window check` in either project compiles the same host
checks, including both BDOS identities and public numbering ranges.

The linker can append an unnecessary zero record after the declared CODE/DATA
groups. `trim.py` validates this simple CMD layout and removes only zero bytes
beyond the last required 128-byte record. This avoids an extra 2 KB allocation
for WMENU on the tools floppy without changing any loaded code or data.
