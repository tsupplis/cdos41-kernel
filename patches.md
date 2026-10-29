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

## TMP/BATCH: DIR spellings and message consistency

The 4.1 shell and BATCH accept CP/M bracketed DIR flags as aliases for native
/L /W /P /S. Combined bracket flags and a final omitted ] are accepted.
System filtering applies to CP/M SYS files and DOS hidden/system files.
BATCH now shares the shell's CLS built-in and omits the redundant USER media
note; its PAUSE prompt already matches the shell. Native ERA/DEL behavior is
retained. The DIR regression runs a CP/M-hosted BAT against DOS media.

## Maintained help and editor data

HELP documents packaged commands, TMP built-ins/aliases and actual system
RSPs, using original 4.1 documentation plus reviewed local/import behavior.
Unavailable old CCP/M topics are removed; every packaged HELP.HLP is rebuilt.
DREDIX's HELP.EDX/LSN.EDX live beside its sources and remain on its image.
The LETTER.TXT sample is removed from base and distribution inputs.

## FAT files: FCB attribute boundary

In `kernel/con/black.a86`, `copydir` used `JA` after comparing the filename
index with 4, so it copied five attribute bits instead of the documented
four. FAT short-name case flag bit 3 (used by mtools for lowercase names)
therefore became FCB f5', an interface flag. CLOSE strips interface flags
before validating the checksum, producing a Close Checksum Error even for
an unchanged file. Change the branch to `JAE`, matching the reverse attribute
conversion and keeping f5'-f8' out of stored filename attributes. This is a
one-byte opcode change, with no code-size or address changes; checksum
validation remains enabled.

`make check-fat-batch` runs twelve disposable FAT cases across case flags
00/08/10/18, CR/LF or Ctrl-Z EOF, record padding and multiple buffer reads.
Each script also runs a FAT-hosted ERA.CMD and preserves an unrelated file.

## FAT names: case-insensitive matching and modern case metadata

`kernel/con/black.a86` now compares ASCII letters in FAT short names without
case and returns uppercase names through the CP/M FCB interface. Exact names
and `?` wildcards share this path, including OPEN, CLOSE, ERA and RENAME.
Only a-z are folded: punctuation remains distinct. Existing directory name
bytes are not rewritten merely by reading or searching them.

FAT directory byte 12 bits 3/4 are modern lowercase-name/extension flags.
The extension flag previously appeared as CP/M F4. Copying a CMD to CP/M
could persist that accidental attribute; launching it then enabled F4's
FCB compatibility modes, including F2 partial closes. PIP accumulated open
entries and eventually reported OPEN FILE LIMIT EXCEEDED.

FAT now exports/writes only the nonconflicting legacy F1-F3 bits. F4 is not
recognized or set on FAT; SET preserves both case flags. F1-F4 on genuine
CP/M media retain their existing semantics. This deliberately replaces the
old FAT F4 interpretation, which cannot be distinguished from the modern
lowercase-extension flag. It extends the earlier FCB attribute-boundary fix.

For CMD files already copied to CP/M with accidental F4, clear that stored
attribute once, for example `SET D:PIP.CMD [F4=OFF]`, or copy the file again
under the corrected kernel. Do not indiscriminately clear genuine legacy
compatibility attributes on unrelated programs.

`make check-fat-case` uses disposable CP/M/FAT images. It exercises 40 files
with physical uppercase/lowercase names and NT flags 00/08/10/18, runs PIP
from FAT and after import to CP/M, compares copied contents, checks exact
and wildcard ERA and punctuation sentinels, and verifies CP/M F4 remains
available while FAT case flags survive SET. The user's 117-file hard-disk
transfer is also checked separately on a disposable copy.

## XIOS: BIOS INT 1Ah RTC, following CCP/M

`kernel/con/xrtc.lib` is copied unchanged from the maintained CCP/M project,
with no sibling build dependency. Startup reads BIOS date/time/date (AH=04h,
02h, 04h) before replacing vectors, validates BCD/calendar/time values, and
retries a date rollover at most three times. Valid values initialize the
software clock; missing or unsupported services leave its defaults intact.
The conversion uses CP/M day 1 = 1978-01-01, the 16-bit day range, and full
Gregorian century rules.

XIOS slot 25 and the BDOS 104 hook follow the CCP/M implementation. Successful
DOS INT 21h date/time setters also call the same XIOS entry because CDOS's
PC-MODE updates TOD directly. Write-back uses AH=05h/03h and preserves the
BIOS daylight-saving flag; failed writes do not discard the software clock.
BIOS calls occur at initialization or in process context, never in IRQ0.

The old AT-only direct-CMOS clock import, including its two-digit-year
arithmetic, is replaced. AT recognition and CMOS floppy-drive detection stay
in place. The alternate OEM XIOS under `kernel/xios` remains separate; this
patch applies to the default SQUID XIOS used by the distribution images.

`make check-rtc` executes the actual built XIOS code with a synthetic INT 1Ah
handler: valid dates, 2000/2100 century boundaries, range/BCD rejection,
absent and unsupported services, stable/unstable rollover reads, write-back
and date-write failure, and preserved startup registers/flags. No real clock
is changed. The check is also included in `make check`.
