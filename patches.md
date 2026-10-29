# Concurrent DOS 4.1 local patches

Only changes made for this 4.1 rebuild are recorded here. This is not the
CCP/M 3.1 patch history or a catalogue of original Digital Research changes.
Original archive hashes remain in sources.json alongside modified hashes.

## DATE.EXE: short-year input

`commands/datetime/pcdate.a86` uses the native DATE.CMD pivot: 00..77 means
2000..2077 and 78..99 means 1978..1999. Explicit 19xx/20xx is retained;
short 19/20 means 2019/2020. Incomplete three-digit years are rejected.
DOS validates calendar dates and its supported year range. The regression
harness runs 54 command-line/interactive parser cases against the linked EXE,
intercepts date-setting calls and rejects the original at `1/2/00`.

## GENCCPM: byte initialization

DRC 1.11 emits zero for `char = -1`; a standalone compiler probe confirms
this independently of structure layout. In genc3.c, RTM flags are written
as three explicit FF bytes, using the existing CCP/M workaround. The old
00 FF FF entries contain an invalid waiting-process pointer. In genc5.c,
true byte settings likewise use literal FF. `tools/sysgen_check.py` checks
flag bytes, fixed system addresses and the numbered resident-process chain
before a generated CCPM.SYS can become the build output.

## PIN: per-console input queues

Under PL/M OPTIMIZE(3), updating the offset alias of a based CCB pointer
then passing ccb.vc uses the old cached CCB address. PIN consequently gave
consoles 0 and 1 VINQ000, and a background console consumed alternate keys.
`kernel/rsp1/pin.plm` reads the current console number inside DOQ instead.
The procedure boundary forces a fresh based-pointer load. No scan-code,
modifier, function-key or console-switch translation is changed.

## XIOS: enhanced-adapter cursor

`kernel/con/xinit.lib` probes the enhanced BIOS and reads text character
height from 40:85. Cursor start/end become height-2/height-1. A local
monochrome cursor variable in xcon2.lib, selected by xcon1.lib, retains the MDA default until the
probe succeeds. Original CGA/MDA/Compaq defaults remain on unsupported
BIOSes; CRTC register 9 is not read. Enhanced color adapters also disable
legacy CGA snow-avoidance waits, matching the relevant CCP/M cursor fix.

## CIO: buffered line editing and recall

Port the CCP/M Function 10 editor into `kernel/con/chario.cio`. Ctrl-A/F
move left/right, Ctrl-B toggles Home/End, Ctrl-G deletes at the cursor,
Ctrl-K deletes to the end and Ctrl-X deletes to the beginning. Backspace
and Rubout delete left. Ctrl-W recalls the last nonempty accepted line on
empty input and otherwise moves to End. Recall is separate for each console;
blank input and Ctrl-U preserve the previous line. Ctrl-U clears with the
historical #/newline echo, Ctrl-R retypes, and Ctrl-E continues on a new row.
Return accepts the entire buffer, including the suffix right of the cursor.

Left/Right, Home/End, Delete and Up are translated by xchar.lib only while
Function 10 owns the foreground console; Up is exactly Ctrl-W. Other input
retains its 4.1 PC-mode/programmed-key processing. CCB flag 40h marks editor
ownership and console.cio clears it on process termination. Cursor state
uses ten bytes on the caller's stack; 16 recall slots occupy 4 KiB in CIO's
code group. CCB, UDA and SYSDAT layouts are unchanged.

## XIOS: compact-keyboard console switching

`kernel/con/xbegin.lib` recognizes Ctrl+Alt+1..4 for consoles 0..3 and
Ctrl+Alt+Tab for cycling with wraparound. These generate the existing
console-switch events; PIN retains ownership checks and the original
Ctrl-keypad shortcuts remain available.

## PCTMP: CLS and USER output

`kernel/rsp3/tmpmenu.lib` recognizes bare CLS as a built-in command and
sends the established XIOS ESC E clear/home sequence. Explicit drive/type
names still use external command lookup. USER retains its number report
and omits the “User numbers only apply to CP/M media” note; the unused
string is removed from tmpdir.lib.

The native 4.1 SYSDISK is packaged on both media images. Its existing SD
implementation in commands/sysdisk is retained unchanged: query the system
search path, set a path, or enable/disable searching with [ON]/[OFF]. The
CCP/M 3.1 command's single-system-drive implementation is not substituted.
SYSDISK remains an external source-built command.

Build integration and carried-over unmodified tools are documented in
README.md and SOURCE-MAP.md rather than treated as runtime patches.

## Regression checks for these changes

`make check` includes 13 cases executing the actual built XIOS cursor
routine under synthetic legacy/enhanced BIOS/font-height responses.
`make check-pce` boots disposable copies with the launcher's VGA/XT profile,
types ordinary single-key DIR and PIP commands, returns from PIP, copies a
file across A:/B: and checks its bytes apart from CP/M record padding.
It also exercises insertion/deletion, control and navigation keys, recall,
full buffers, tabs, control-character widths, wrapping, per-console isolation,
all four direct shortcuts, Tab wraparound, USER output, CLS and native
SYSDISK query/[OFF]/[ON].
No released media is modified by this automated boot test.

## Command import organization

DOS DATE.EXE and its existing short-year patch/tests moved to commands/datetime;
native DATE.CMD is in commands/date. ERAQ moved unchanged into commands/era.
ERA uses the same public-entry rename and 4.1 startup/includes as the local
ERAQ; comparison of the two ERAQ versions found no algorithm changes.
Other newly requested CCP/M command imports retain their source bytes and
Makefiles. PIP3 was removed; PIP4 remains the distribution PIP. HELP.HLP is
indexed from imported CCP/M text with the emulator reporting 4.1.
