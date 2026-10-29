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

## PCTMP/BATCH: native DEL alias

DEL now expands to ERA.CMD in both kernel/rsp3/tmpdir.lib and
commands/batch/tmpdir.lib. The alias string remains eleven bytes, so the
existing fixed-slot rewrite preserves the original tail and its length.
DELQ still invokes ERAQ.CMD. ERA.CMD is included on both initial images.

## PCTMP/BATCH: common PAUSE prompt

PAUSE and DIR's /P prompt now use `Press any key to continue...`, exactly
matching CCP/M 3.1 PCTMP. Both TMP source copies are updated; key handling
is unchanged (raw BDOS 6/FD input). The old DIR-only trailing space is removed.

`make check-aliases` boots disposable PCE images, checks both pause prompts,
executes DEL from TMP and a BAT file, and verifies only the named files
were deleted. The fixtures do not modify the distribution images.

## PUT/GET/RDR: direct console input selectors

The imported shared redirection engine now recognizes BDOS 6 FDh (blocking
input) and FEh (console status), alongside FFh (input if ready). PIP checks
status then uses FDh; previously that input call bypassed GET and waited on
the keyboard. The change is confined to commands/putget/putget.lib.

`make check-redirection` boots disposable floppy images, tests multi-record PUT
capture and append, feeds a copy command to PIP through GET and RDR, checks the
copied bytes and captured output, and verifies return to the shell.

## SDIR: DOS directories and missing options

The original 4.1 binary and imported CCP/M sources both treated translated
DOS directories as 0k files. SDIR now retains the subdirectory flag from
search results through its buffered records, shows <DIR> in FULL/SIZE and
backslash markers in SHORT/SIZE, and counts directories separately. CP/M
DIR/SYS attribute filtering keeps its original meaning. The record-address
helper now uses SIZE rather than a literal 23-byte stride.

SHORT and HELP, present only in inactive source/help code, are now accepted.
SHORT shares the buffered search/sort/filter path. HELP.DAT documents these
options, ATTRIBUTES/SORT/DATE and the DOS-directory display rules.

`make check-sdir` runs the OEM and rebuilt commands on disposable CP/M/FAT12
images, compares legacy behavior and checks the intentional extensions,
including paging, NOPAGE and Ctrl-C.

## TYPE: exact DOS EOF and compatibility review

The Concurrent 3.2 reference and imported CCP/M implementation share the
file/password/record-read logic. Both formerly displayed zero padding from
a DOS file's final partial 128-byte record when no Ctrl-Z was present.
TYPE now detects the DOS open FCB flag bytes and keeps the 32-bit byte length
from FCB bytes 28..31 in a local counter. It stops at actual DOS EOF while
preserving Ctrl-Z and CP/M record semantics. Bracketed PAGE/P01..P23 paging uses physical screen rows; the old
unbracketed P/PNN syntax is intentionally rejected.

`make check-type` compares ordinary/error paths, protected-file passwords
and editing, EOF boundaries (including 65537 bytes), and paging under PCE on
disposable CP/M/FAT12 images. commands/type/README.md records the intentional
differences and coverage limits. The Concurrent 3.2 binary remains in base
as a test reference; it is not packaged in place of the rebuilt command.

## TYPE: bracketed page length

TYPE accepts [PAGE] (23 physical rows) or [PNN], with exactly two digits
01..23. Both use the same row counter, native pause prompt and Ctrl-C path.
Unbracketed P/PNN and [P] are rejected, as are zero, lengths above 23,
malformed options and extra arguments. Detailed behavior is documented in
commands/type/README.md. Regression checks cover the numeric limits,
case-insensitivity, EOF boundaries and rejection of the removed syntax.

## SHOW: 3.3 disk/user/label parity

The imported CCP/M source now matches SHOW 3.3's rejection of USERS/LABEL
on DOS media, its implicit SPACE drive limit (A:..M:), and option dispatch:
OPEN is invalid and the supported options follow the OEM dispatch. The private
media probe restores the caller's DMA offset. Creation stamping
is read from label bit 10h instead of an uninitialized local variable.

The existing DPB and Y2K fixes remain. make check-show compares the OEM and
rebuilt commands on disposable CP/M/FAT12 images and independently checks
free space, capacities, users, label timestamps and media guards. Detailed
coverage and the retained source version identifier are documented in
commands/show/README.md.

## SET: CDOS media guards and help parity

`commands/set/set.plm` matches OEM SET 3.1's CP/M-media checks before
label access and label/XFCB writes. Private search storage and DMA restoration
prevent DOS pseudo-labels being mistaken for CP/M label/password records.
SET 3.1N retains the imported parser, attribute, protection and timestamp
logic. HELP removes unsupported MAKE/EDIT and documents ARCHIVE/F1-F4.
`make check-set` compares OEM/rebuilt execution on disposable CP/M/FAT disks,
including persisted attributes, interactive passwords and timestamp settings.

## XIOS: WMENU compact-keyboard shortcut

Ctrl+Alt+Esc emits the existing window-manager wake event (7Dh), the same
as Ctrl+keypad-Plus. The original binding remains available. No manager is
loaded automatically; WMENU must already be installed. Console shortcuts
Ctrl+Alt+1..4 and Ctrl+Alt+Tab retain their existing behavior.

## SYSTAT: fixed data allocation

SYSTAT uses its statically allocated data requirement, matching the OEM
policy, rather than requesting up to 64 KiB of unnecessary DATA. The report
logic and private structure offsets are unchanged. REN also retains its
algorithm; both Makefiles now track included literals.

## WINDOW/WMENU: native CDOS interface

Public window numbers are 1..4, with zero-based XIOS indices confined to the
support layer. SETUP exports all four windows; text snapshots trim trailing
spaces. WMENU uses the native highlighted menu, arrow/Space navigation,
live-edit commit on Esc/Return and native color-arrow direction. Its status
buffer is passed as CX:DX offset:segment. These correct confirmed differences
from the initial CCP/M-derived rewrite; original binaries remain as references.
