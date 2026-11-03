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
CONCURRENT SET 4.1N retains the imported parser, attribute, protection and timestamp
logic. HELP removes unsupported MAKE/EDIT and documents ARCHIVE/F1-F4.
`make check-set` compares OEM/rebuilt execution on disposable CP/M/FAT disks,
including persisted attributes, interactive passwords and timestamp settings.

## XIOS: WMENU compact-keyboard shortcuts

Ctrl+Alt+0 (top-row zero) and Ctrl+Alt+Esc emit the existing window-manager
wake event (7Dh), the same as Ctrl+keypad-Plus. All three bindings are decoded
in `kernel/con/xbegin.lib`; WMENU waits for the existing XIOS event and needs
no binary change. Boot a rebuilt system image to enable the new binding.
No manager is loaded automatically; WMENU must already be installed.
Console shortcuts Ctrl+Alt+1..4 and Ctrl+Alt+Tab retain their existing behavior.
`make check-wmenu` exercises all three wake keys, hide, Abort, uninstalled
hotkey suppression and ordinary zero input on disposable PCE media.

Under PCE, `media/cdos86.cfg` sets `escape = "F12"`. PCE otherwise uses Esc as
its magic-key prefix: Esc is swallowed and the next key release becomes an
emulator command (for example, 0 sets CPU speed 0), so Esc/Ctrl+Alt chords
were unreliable interactively. F12 has no XT scan code and never reaches DOS.

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

## IBM XIOS graphics on EGA and VGA

The color XIOS uses the captured video BIOS for CGA-compatible modes and palettes on enhanced adapters. INT E6h selector 30 advertises native 640×350, 16-color mode when the adapter has sufficient memory. The foreground graphics owner must restore text before switching consoles.

## Recovery from the European 29-Nov-1985 kernel

Reference: `base/ccpm.sys`, SHA-256
`a5c3a5559b03194d636d5eb74b475257a249e126caaa5725a6622f43f49218b0`.
These are selective source changes recovered from the binary, not replacement
components. Existing local fixes are retained. Offsets below are relative to
its BDOS code group or XIOS/SYSDAT group, not whole-file offsets.

### BDOS and XIOS: recovered and tested

- `kernel/con/bdosif.bdo`, `retmon`: restore bit 7 of the caller's FCB drive
  byte for directory operations after copying the local FCB back. Recovered
  from BDOS `0259h`. Tests execute assembled code for ordinary/directory
  FCBs with zero, one and 36 bytes copied, including copy-boundary checks.
- `kernel/con/file3.bdo`, `check_all_media`: skip shared-chain buffers whose
  drive differs from `adrive` before testing their pending-write flag.
  Recovered from BDOS `1F0Ah`. Six assembled-code cases cover empty chains,
  clean/dirty buffers and buffers belonging to the selected/another drive.
- `kernel/con/xbegin.lib`, `entry`: reject function numbers above 38 before
  indexing the XIOS function table; return `FFFFh` in AX and BX. Recovered
  from XIOS `0C40h`. All 256 possible function bytes are exercised with
  synthetic dispatch targets, including both range boundaries.

Tests use disposable memory fixtures and stub disk dependencies. These
routine-level checks are supplemented by the PCE boot/usability suite.

### PCTMP: isolated compatibility changes recovered and tested

The original's PC-MODE stamp is 24-Sep-1985. The current batch recovers:

- `kernel/rsp3/ms1.a86`: install `INT 21h; RETF` at PSP offset `50h`.
- `kernel/rsp3/ms2.a86`: implement functions `50h` and `51h` using the existing
  `active_psp` value; these functions do not switch concurrent processes.
- `kernel/rsp3/ms2.a86`: support EXEC `4B01h` for COM/EXE load-only operation,
  returning SP, SS, IP and CS at parameter-block offsets `0Eh` through `14h`.
  Retain the original's prepared-child state rather than starting execution.

`tools/pctmp_recovery_check.py` executes the built routines: the PSP stub
and adjacent bytes; 50h/51h dispatch and six get/set cases; and 20 EXEC
control-flow cases covering COM/EXE, execute/load-only/overlay, invalid
subfunctions and failure cleanup. EXEC file I/O, allocation and loaders
are stubbed; this verifies control flow and returned parameter layout, not
end-to-end loading of an application. A separate `make check-pctmp-live`
boots disposable media and runs a DOS program that checks the PSP stub and
50h/51h services, loads real COM and MZ EXE children with 4B01h, inspects
their returned entry-point bytes, frees their memory, restores the parent
PSP/DTA and returns to the shell. This live test passes.

`make check` and `make check-historical` run these tests and
`tools/historical_check.py`. Like the RTC tests, NASM builds only disposable
test drivers; production components retain ASM86/RASM86 and LINK86.

DOS critical-error/temporary-state and FCB directory-context recovery are
now implemented and tested as described below.

The boot regression now reserves scratch space by removing HELP.HLP only
from its disposable tools-disk copy. The distributed tools image is full;
without this fixture preparation its PIP copy test fails with “DISK WRITE
NO DATA BLOCK” independently of the recovered changes. Distributed payloads
remain unchanged.

### DOS console, volume labels and allocation information

`kernel/rsp3/ms1.a86`: reserve the buffered-input CR byte, treat DEL as
Backspace, dispatch function 01h Ctrl-C through the existing break path;
reject repeated/empty/nonmatching volume-label searches; and retrieve the
DPB through BDOS 31 before reporting allocation information, recognizing
both FAT DPB markers and excluding reserved clusters 0 and 1. A zero-capacity
input guard prevents underflow in the recovered decrement. Specified-drive allocation queries explicitly reselect `cur_dsk` afterward;
the historical binary reselected the queried drive instead. An explicit zero
high word also makes division safe for a DPB returned outside SYSDAT.

`tools/pctmp_io_check.py` executes the rebuilt routines with synthetic console
and disk dependencies: 13 console cases (capacities 0/1/2/5/255, CR bounds,
Backspace/DEL, overflow and function 01h Ctrl-C), 14 volume-label cases
(exact/wildcard/mismatch/empty/find-next, default/explicit drive), and 48
allocation cases (FAT12/FAT16/CP/M/external DPB, drive selection, selection/DPB
failures and restoration). All pass. The test runs under `make check` and
`make check-historical`. The three test groups also reject the unmodified archived-source build.

`make check-pctmp-live` additionally checks real FAT12 geometry against the
fixture's BPB, CP/M allocation reporting, current-drive preservation, exact
and mismatching label searches, find-next exhaustion, and zero/bounded DOS
console input. The rebuilt system passes these checks as well as the earlier
PSP and COM/EXE load-only checks.
The larger error/directory-context work remains separate.

### FAT extension and shared-directory ownership

Recovered from the European kernel: `black.a86` uses the volume cluster
limit at `cnpr6` instead of a FAT12-only constant; `testfile` forces directory
buffer lookup; `extendf` invalidates/reacquires directory state before updating
it, retaining the original CKS flag policy and error-11 unwind. The original
word test at CKS+1 masks only its low byte; the source expresses that as a
byte test without reading an unrelated adjacent byte.

`ms2.a86` increments an HDS reference count by the receiving CAT's owner
count when inserting a directory into an existing shared CAT. The other
inheritance paths remain unchanged.

`tools/fat_recovery_check.py` passes 79 assembled-code cases: 36 FAT12/16
boundary decisions, four forced-lookup flag cases, 30 extension cases and
nine CAT/HDS inheritance cases. Extension tests use separate code/data
segments and check fresh versus stale directory writes, CKS policies,
skipped updates, error 11, and stack balance. Inheritance tests cover one,
two and five owners, existing directories and the no-CAT path. The test is
included in `make check` and `make check-historical`.

The live DOS regression additionally grows two FAT files alternately to
32 KiB each with distinct contents and verifies both files byte-for-byte
from the resulting image. This PCE test and the full `make check` pass.
The archived-source build fails the FAT-boundary and ownership regressions.
FAT16 boundary and shared-CAT cases are routine-level tests; the live disk
stress test uses FAT12.

### DOS FCB directory context

Recover the opening-directory first cluster into DOS FCB reserved word 1Ch,
then select it while closing and restore the caller's current directory.
Reference PCTMP offsets: 31F6h (HDS access), 571Bh (open), 586Fh/58F0h
(close), 5925h (context exchange), 5D6Ch (rename sentinel). Rename supplies
FFFFh to keep its current directory. Unlike the historical binary, the
unwritten-file close path also restores the directory before purging its FCB.

### DOS critical errors and temporary state

Recover the European PCTMP DOS 2.x critical-error frame (2DD2h), logical to
physical drive mapping (4EA7h), select-error mapping and unbounded explicit
retry (4ED5h), DOS 1.x stack/register restoration (4F4Eh), and temporary
DTA/P: cleanup (4E68h). Disk operations in MS2 now use the common error
mapper. INT 21h clears DF on entry. Ignore retains the historical DOS 1.x
retry behavior; DOS 2.x ignore returns success. Abort invokes INT 22h.

Two deliberate corrections to historical cleanup: P: state toggles between
1 and 2 with XOR 3 (the binary used XOR 1 but tested for state 2), and the
borrowed handle pointer is saved rather than relying on the handler's BX.
These changes apply to abandonment of an interrupted operation when the
INT 24h handler calls disk services; they do not promise arbitrary recursive
DOS disk calls returning into the interrupted operation.

New assembled-code regression drivers test FCB capture/close context,
critical-error frames and register/stack preservation, drive/error mapping,
ignore/retry/abort, more than ten retries, and idempotent temporary-state
cleanup. BDOS failures and interrupt handlers are synthetic; physical error
injection on live disks is not part of these tests.

Termination cleanup also releases borrowed state and resets the dispatch
flag, including an INT 24h abort that bypasses the normal DOS 2.x return.

Validation: `make check` passes, including the new routine tests. The live
PCE recovery test opens an FCB in one FAT directory, changes directory, then
closes it with and without writes. It verifies the restored current directory,
the written file, and an untouched same-named file in the other directory.
The PCE boot/usability regression also passes. Critical-error fault injection
remains a routine-level fixture test, not a claim of live faulty-media coverage.

## Boot banner: 4.11 alignment status

The IBM XIOS startup banner now adds `CDOS 4.1 rebuild - 4.11 alignment in
progress`. The original platform/date and copyright lines remain intact.
This describes ongoing comparison with the 4.11 release; it does not change
the BDOS version or claim complete 4.11 parity. The README banner is unchanged.


## COPY: 4.11 path rejection

Ported the release COPY command-tail guard into labelled RASM86 source.
Backslashes in source/destination are rejected with “To use a path, map to a
floating drive.” before any file operation. Rejection exits directly through
CCPRET, avoiding ABORT's temporary-file deletion. Concatenation is preserved.

`commands/copy/check.py` checks the whole executable against 4.11, allowing
only the exact serial text, stack-segment and checksum differences, and runs
18 original/rebuilt tail-preparation cases with output/exit stubs. No live
file-copy coverage is claimed by these routine tests. See the command README.

The SDIR regression now uses the separately retained 4.11 release reference,
not the older CCP/M 2.0 base binary. Its 27 paired cases confirm the documented
directory, year-format and SHORT/HELP improvements; no SDIR code was changed.
RMDIR's diagnostic differences are assessed in its README but not yet ported.


## RMDIR and LOADCCPM: 4.11 alignment

RMDIR now explains forbidden dot paths, failed removals caused by files or
floating drives, and read-only directories (extended error 03h). Command
syntax and deletion logic are unchanged. Whole-code/data comparison and
12 original/rebuilt error-mapping tests are part of its `make check`.

LOADCCPM now preserves INT 1Fh and the existing AT INT 41h parameter-table
offset during vector restoration, as 4.11 does. Release messages are also
aligned. Its complete COM file matches the independent 4.11 original.

SDIR's seven additional path tests confirm matching rejection of explicit
backslash paths and correct filename/wildcard/SIZE operation in a current FAT
subdirectory. No SDIR production changes were necessary.


## WINDOW/WMENU: repaint existing contents after colour changes

Restored the 4.11 colour operation omitted from the C rewrite: repaint all
24x80 backing-image attribute bytes under the per-console mutex and redraw
immediately. Full foreground screens are synchronized first; text, cursor
and status line are preserved. The current intensity/blink bits survive a
foreground/background change. Both commands use the shared implementation.

Regression coverage now compares actual text and colour bytes against the
original for CARDDECK, full/background windows and interactive WMENU colour
editing, rather than checking only stored colour settings. Syntax is unchanged.


## 4.11 command alignment

BATCH now attaches the console before freeing drives and restores priority 200
before processing the next command. With just these changes, a rebuild of the
unmodified OEM sources matches the release except for four serial characters.
The maintained command retains the existing prompt, USER, alias and DIR changes.

CHSET now compares empty option fields as byte values. SHARED=ON previously
failed on its first occurrence. The paired regression checks updates, duplicate
rejection and the resulting CMD header bytes. PRINTMGR uses the 4.11 default of
60 printed lines on a 66-line form and reports that default in help. PIP's
interactive banner identifies the maintained 4.1N version.

DSKMAINT now embeds the released 360 KB DOS bootstrap. The full sector matches
4.11. A floppy formatted by the rebuilt utility cold-boots both original and
locally generated systems linked for segment 0060h. See the DSKMAINT README.

### National keyboard banks

The IBM PC XIOS initializes the IRQ1 translation pointers from the five
release keyboard modes. The default index remains zero (US eight-bit).
Indices 1 and 3 select the national bank through mode bit 1. Plain, Shift, Control and shifted keypad translation use the
selected pointers. The national bank starts with the UK release maps.
The setup directory publishes these maps in slots 3–5.

### National printer translation

The XIOS list-output entry now applies the 4.11 per-printer state machine
before dispatching to the physical port. Five device records retain their
own model, escape continuation, parameter count and character-set state.
All five default to transparent output. Slot 10 exposes the five records to N. Capturing the device number and output byte at the physical
dispatch gave identical streams for all six release models with keyboard
layouts 0 and 3, including extended characters and ESC sequences.

### National keyboard input and virtual-console output

The XIOS now applies the 4.11 national input and printable-output tables
as a pair. Alt scan-code overrides suppress one subsequent UK seven-bit
screen substitution. Caps Lock uses the national case pairs, and the
dead-key path handles composition, deferred keys and the error bell.
The compact-keyboard console shortcuts retain their tagged event path.

A release comparison exercised every byte under the five layouts and
each of the four accent indices. In UK seven-bit mode a scan override
followed by two writes of 23h produced virtual-screen words 5E23h and
5E9Ch with attribute 5Eh. N configures these hooks through the national directory.

### National setup directory and status line

The IBM PC XIOS publishes the JW signature at DATA + 0C3Ch and the
24-word directory used by N.CMD. Its 21 populated slots point to the
keyboard maps, printer records, translation data and saved selections.
The status line uses the release Prn= field to leave space for the
two-character country code and the seven/eight-bit indicator.

### Native program return code (BDOS 108)

A native CMD can read its 16-bit return code with CL=108 and DX=FFFFh, or
set it with any other DX value. Ordinary process creation clears the word.
A disk CMD chain transfers the value and the parent relationship before
scheduling its replacement. On exit the surviving parent receives the
completed child's word. If multiple children finish, the latest delivery
wins. The implementation uses the existing PD word at offset 2Ch.

Ctrl-C termination returns FFFEh. Fatal BDOS disk errors return FFFDh.
The DOS child-status call and the private shell return-code service keep
their existing interfaces. Run `make check-retcode` for the PCE regression.

## PCTMP country information and modification timestamps

These are local API extensions beyond stock Concurrent DOS 4.1.

AH=38h returns the complete DOS 2.x US country record with ASCIIZ fields and
zero-filled reserved bytes. Invalid selectors and the unsupported set request
return AX=2 with carry set.

AH=57h validates handles and dates/times, preserves FAT two-second precision,
and propagates failed writes. CP/M uses minute-resolution update stamps and
rejects disks without enabled, available update stamps. Successful updates
refresh the shared handle cache. Creation/access stamps are preserved.
The DOS adapter and BDOS 116 share a tagged DMA format. The first two
little-endian words are 3854h and FEDDh. On FAT the remaining words are
packed DOS time and date. On CP/M the remaining four bytes are the native
update day word and BCD hour/minute bytes. FEDDh cannot be a valid BCD
hour/minute pair.
Legacy untagged native timestamp requests retain their original semantics.

The normal check runs assembled handler regressions for FAT/CP/M conversion,
failed lookup, invalid date/time, failed disk writes, cache updates and DTA/
drive restoration. CP/M tests cover missing file, disabled stamps, missing
SFCB and legacy requests. The live PCTMP target also boots disposable media
to verify country fields and timestamp write/set/duplicate/close/reopen on
FAT and timestamp-enabled CP/M.

## DOS readiness, break checking, errors, verification and commit

These additions extend stock 4.1. IOCTL 44h validates handles and follows
handle duplication. Subfunction 00h describes the actual target; 06h/07h
report input/output readiness using file position/length or native console,
AUX and assigned-printer status. Unsupported subfunctions return error 1.

33h enables extended Ctrl-C checks at DOS entry, preserving application
registers for INT 23h. Polling enables interrupts and dispatches before
checking input so PIN can deliver keys. Ordinary input and pending extended
key tails are preserved. Raw 06h/07h, the control call itself, error queries,
internal DOS calls and INT 24h reentry are excluded. Existing console checks
remain active independently of the extended setting.

59h/BX=0 returns the last DOS error and its class/action/locus. State belongs
to each console's PCTMP data segment. Successful calls and repeated queries
retain it. The physical-error bridge records the DOS error before INT 24h;
critical-error details survive conversion to a general handle error.

2Eh/AL=0 or 1 and 54h control/query an additional system-wide verification
setting through direct XIOS function 39, CH=0/1 or FFh for query. Buffered
writes drain before a setting change. Floppy writes use the existing FDC
verification cycle. Hard-disk writes use the existing read-back comparison
and error/retry handling. Boot-time floppy and per-volume hard-disk verify
options remain additive. This direct XIOS entry is a local API extension.

68h commits disk handles through partial native close, byte-count update
and buffer flush while retaining the handle, shared position, opening
directory and lock. A retained partial-close FCB receives a fresh checksum.
The original close path discarded the FCB after the attribute update and
therefore did not need to reuse it. Commit preserves that valid FCB across
the byte-count update. BDOS 30 with both F5' and F6' now retains the open
lock during that update; this combined-flag behaviour is a local extension.
Partial-close, attribute and flush errors are reported. Device and invalid
handles return DOS error 6.

Regressions exercise assembled handlers with synthetic devices and error
injection, including hard-disk read-back mismatches. Disposable PCE tests
cover the APIs on FAT and CP/M, continued I/O after commit, exact byte counts
after reopen, and live Ctrl-C delivery to an application's INT 23h handler.

## DOS redirection foundation and EXEC handle ownership

PCTMP counts every handle reference, including standard devices and files
assigned to handles 0-4. Close flushes the last disk reference before freeing
its handle. Forced duplication checks the destination range and handles
self/alias duplication without changing counts. A failed destination close
leaves both bindings intact. Duplication requires a free handle number,
independently of whether another FCB is available.

A root DOS launch initializes its standard table and PSP identity. EXEC
saves the parent's handle mapping in its PSP and adds one reference per
inherited slot. Child termination releases its own references, including
redirected standard streams, and restores the parent mapping. Inheritance
is rejected before loading if byte-sized reference counts would overflow.

EXEC 4B00h stores the parent's register and DTA frame on its own stack,
using PSP:2Eh for saved SS:SP. Each nesting level owns its frame. The return
continuation restores the parent stack, registers, DTA and termination
vector. Children inherit terminate, Ctrl-C and critical-error vectors.
Direct abort continuations restore application vectors and release the
interrupted child's handles before resuming the parent. Ctrl-C uses return
type 1 and critical abort uses type 2.

The read adapter previously accepted a last requested byte index equal to
the file's byte length. Requesting exactly size+1 bytes could return a padding
byte. The comparison now requires the byte length to exceed that index.
This correction applies to DOS FCB and handle reads on both media types.

GET/PUT/RDR integration and stream-call routing are described below.

## DOS console streams and GET/PUT/RDR launch integration

This is a local extension beyond the original CDOS 4.1/4.11 interface. The
implementation is confined to PCTMP (`kernel/rsp3/ms1.a86`, `ms2.a86`) and
the shared launcher in `commands/putget`. No sibling project or external
runtime participates in either build or execution.

### Responsibility and dependency direction

GET/PUT/RDR parse their existing bracket syntax, resolve the child using
PCTMP ORDER and submit a stream configuration before calling the existing
private DOS loader. They do not install their native INT E0 interceptor for
DOS children. PCTMP copies and normalizes filenames, opens files in the
launched process, binds standard handles and owns subsequent I/O and cleanup.
The kernel retains no command buffer, code pointer or callback into the CMD.
MS1/MS2 cross-calls are internal to the existing PCTMP link unit; neither
module starts a helper command. Native CMD redirection retains its own
existing hook and record-oriented behavior.

### Private interface and lifetime

PCTMP private selector FFh returns AX=5244h and DX=1. Historical translators
safely reject FFh; callers must confirm both words before using selector 9.
The private table bound is now an entry count rather than its byte length,
preventing calls beyond the table.

Selector 9 takes caller DS:DX pointing to six words: version (1), flags,
input FCB offset/segment, output FCB offset/segment. Flags are 0001h=input,
0002h=output, 0004h=append, 0008h=echo input, 0010h=echo output. Zero return
means accepted; a nonzero return rejects the configuration. DX=0 cancels
the caller's pending configuration. Parsed 8.3 FCBs become resident,
explicit-drive, NUL-terminated filenames. Wildcards, path separators and
identical input/output names are rejected. This interface does not add
path syntax to the tools' existing FCB parser.

The pending request records the requesting native process descriptor. Only
that process's private function-1 launch consumes it. Filenames and flags
are then copied into active per-console state, and the pending lease is
cleared. Setup runs after DOS vectors are installed and before the target
starts, acquiring native file ownership in the launched process. Failed
loading clears the active configuration. Setup failure reports on handle 2
and takes ordinary process cleanup. The wrapper cancels unused configuration
and uses the existing attach/cleanup sequence after launch.

### DOS I/O behavior

INT 21h AH=01h/02h,06h/07h/08h/09h,0Ah/0Bh and the selected function of 0Ch
route applicable standard input/output through handles 0/1. The selector
applies only to public DOS console calls, not internal native BDOS calls or
INT 24h handling. Status checks inspect file position and size without
consuming data. Closed or inaccessible redirected handles cannot silently
fall back to the keyboard or screen.

Legacy byte I/O uses PCTMP's native record cache directly, avoiding recursive
DOS dispatch. Native DMA state is restored after each operation. The cache-hit
path now explicitly returns success; previously a stale return byte could
be mistaken for a read error. Logical EOF follows the stored byte length,
including the corrected size+1 boundary described above.

AH=0Ah returns a count of zero at EOF. CR/LF line input consumes the LF of a
preceding CR only when the same HCB and byte position still match; intervening
raw reads or seeks preserve their exact bytes. AH=3Fh/40h remain binary:
NUL and Ctrl-Z are ordinary bytes, and EOF returns a zero read count.

Output overwrite uses create/truncate. Append opens an existing file and
seeks to its true byte length, creating only when the file is absent. Echo
flags live on the shared HCB and survive duplication and EXEC inheritance.
Echo goes straight to the native console backend, bypassing redirected stdout
so it cannot feed back into the output file. Readiness and EOF do not echo;
block reads/writes echo only the bytes actually transferred.

Handle 2 remains the console unless an application redirects it explicitly.
BIOS video, direct screen writes and explicitly opened CON devices remain
outside these standard streams. Shell `<`, `>` and `|` parsing is not added.
EOF-aware legacy callers must still honor their API's EOF convention; a
program that retries input forever can still loop at EOF.

### Assembler data references and loader boundary

Shared data externals must be declared in DSEG. Declaring them while CSEG is
active makes RASM86 infer CS overrides even when the definition is resident
data. The packet's caller segment and active flags exposed this in live tests;
the shared break/error/critical-context declarations were audited and moved
alongside the existing data externals. A separate-code/data regression guards
the packet boundary, since a flat test image alone can mask this error.
ASM86 command-side numeric memory operands use register-indirect addressing,
matching the existing loader-discovery convention.

The initial redirection EXE regression used a sector-aligned header.
The historical loader limitation it exposed is corrected in the PCTMP exact
header-positioning change below; it was independent of stream routing.

### Verification

The assembled handle regression covers forced duplication, self/alias cases,
failed close, reference overflow, nested PSP ownership and exact EOF boundaries.
It also exercises critical-abort continuation, vector/DTA/register restoration
and release of child-only files. Disposable PCE tests cover nested EXEC and
Ctrl-C return, legacy and block stream calls, binary data, append, echo,
COM/EXE launch and return to the shell. Native PUT/GET/RDR regression is retained.
Run `make check-redirection` for native and DOS stream cases,
`make check-pctmp-live` for DOS/EXEC live checks, and `make check-historical`
for assembled routines, including the separate-segment packet test.
The live hardware critical-error path is not claimed by these tests: its
cleanup continuation is tested directly in the assembled regression.

### Distribution and regression fixtures

`cdostools.img` carries GET/PUT/RDR and the other general utilities.
`cdosdev.img` separates the assemblers, debugger, conversion/generation tools,
ED and SUBMIT, with PIP on both disks. Both remain 320-KiB data disks, and
`make dist` packages all eight images. This leaves room for the larger tools
without changing the boot or filesystem format.

Native redirection tests launch the wrappers explicitly from B:, where the
tools disk installs them. Console fixtures initialize the newly introduced
stream state. Timestamp fixtures initialize the real RSP DATA group and keep
it separate from code, including the calendar tables; modifying code layout
must not alter their simulated data. None of these fixture changes weakens
byte comparisons or error checks.

## PCTMP: exact EXE header positioning

This is the same EXE-loader defect documented for DOS Plus 1.2 in the
[Seasip DOS Plus EXE-loader analysis](https://www.seasip.info/Cpm/dosplus_exe.html).
The historical calculation converts header paragraphs to bytes, divides by
512 and multiplies by four. It therefore discards a partial 512-byte page.
Changing the divisor alone fixes record-aligned headers but still fails on
headers such as 96 bytes. MZ header sizes are paragraphs, so the full reader
must also handle an image starting inside a 128-byte CP/M record.

`kernel/rsp3/ms1.a86` now computes the exact declared image length with
32-bit arithmetic, checks the fixed MZ header and nonempty image bounds, and
reads from `header_paragraphs / 8`, skipping
`(header_paragraphs & 7) * 16` bytes of the first record. Each read goes through
128 bytes of per-console DATA scratch. Only image bytes are copied to the
child: record padding never extends a copy beyond the paragraph-rounded
allocation. EOF before the remaining image is loaded takes normal loader
failure/cleanup. The original header buffer stays intact for relocation.
The existing final-page conventions are retained.

This is the root/private-function-1 PCTMP loader. DOS EXEC already uses
paragraph-sized FCB records and is not rerouted through this reader. No BDOS,
XIOS, command helper or sibling-project dependency is added.

Both independent projects contain the same local `tools/exe_header_check.py`
and `kernel/rsp3/tests/exe_header.asm` fixtures. `make check-exe` exercises
32/48/64/80/96/112/128/144/256/512/528/65552-byte headers, a >64-KiB image,
both full-final-page conventions, relocation, nonzero CS:IP, final image bytes,
malformed/truncated input, and COM execution after errors. NASM is used only
for disposable test programs; production assembly tools remain unchanged.

The reported DOS version is unchanged. Fixing MZ loading does not establish
full DOS 2.11 API compatibility.

Verification: all 18 EXE cases and six COM recovery runs pass on CDOS and
CCP/M independently. CDOS also passes the 32-byte-header FAT EXE with
redirection, append/echo and stderr isolation. Existing assembled DOS, EXEC
and critical-error regressions pass; every packaged payload, boot track
and image size verifies. Allocation arithmetic checks image plus loader,
MINALLOC and ADDMEM for overflow before requesting memory.

## DOS 2.x: complete version returns and CON raw/cooked handle I/O

PCTMP `ms2.a86` function 30h still reports DOS 2.0 (AX=0002h), but now
initializes the remaining version-query outputs: BH=FFh is the generic OEM
value, and BL:CX=0 is the unspecified serial number. BX/CX no longer contain
arbitrary caller inputs. Other saved registers remain intact. This does not
change the native CDOS version or claim DOS 2.11 compatibility.

IOCTL 4401h now sets/clears the raw-mode bit for an open CON handle. DH must
be zero. Only DL bit 5 is writable; device identity and readiness bits remain
derived. Invalid handles return 6; files, non-CON devices and nonzero DH
return 1. IOCTL 4400h reflects the selected mode. IOCTL remains partial:
control-string operations and raw-mode setters for other devices are absent.
CON matching checks its complete name, distinguishing COM1; COM1 readiness
uses the same native AUX status path as AUX.

The internal raw bit belongs to the existing six-byte HCB. Duplicate handles
and EXEC inheritance therefore share it without a new table or changed HCB
layout. New root DOS launches clear the standard handles' raw bits. Freshly
opened handles also start cooked. Switching mode does not discard an existing
cooked input line; raw reads bypass that buffer until cooked mode resumes.

AH=3Fh raw CON reads use PCTMP's native keyboard/extended-key state directly:
no echo, line editing, Ctrl-Z EOF, or Ctrl-C filtering. They return the requested
byte count. AH=40h raw CON writes use the existing native BDOS 50/BIOS 4 raw
console bridge, so FDh/FEh/FFh are output bytes rather than BDOS 6 selectors.
Raw reads/writes do not change native DMA. Zero-length character-device calls
return immediately without opening a device or waiting for input. The existing
cooked path is retained, and DOS legacy character calls retain their own
semantics; the mode extension applies to handle I/O.

Extended BREAK polling bypasses raw CON handle reads/writes even with BREAK
checking enabled; other DOS calls retain their existing checks. No global
console mode, BDOS change, XIOS change or helper command is required. Native
console rendering still interprets its normal display controls.

`tools/dos_console_check.py` executes the assembled routines with separate
code/data segments: version registers, mode validation, complete device names,
zero and bounded transfers, control/high bytes, buffer guards and BREAK routing.
`tools/dos_console_live_check.py` drives disposable PCE media through real
keys: raw Ctrl-C/Z/Backspace/CR, an extended arrow key, no echo, FDh-FFh output,
cooked editing after reset, DUP/EXEC sharing, and cooked defaults in the next
program. The source fixtures are in `kernel/rsp3/tests/dos_raw*.asm`.

## Extended EGA/VGA modes and drawing (issue #22)

The local XIOS `egvideo.lib` adds native 60h/70h/80h/90h/A0h for BIOS
0Dh/0Eh/11h/12h/13h; existing 50h remains BIOS 10h. Native function 30,
`ESC a`, DOS mode setting and DOS mode query use the same mapping. EGA
0Dh/0Eh work with 64 KB; mode 10h retains the >=128 KB check. A separate
INT 10h/1A00h VGA display-combination probe gates 11h/12h/13h, so an EGA
with 256 KB is not mistaken for VGA. Capability selector 30 returns bit 0
for mode 10h, bit 1 for 0Dh/0Eh and bit 2 for the VGA modes and DAC.

Graphics drawing uses captured video firmware through the existing XIOS
private stack and PIC guard. Planar drawing calls the captured ROM vector,
never the DOS-intercepted INT 10h. Its register results are captured before
restoring XIOS registers. There is no new component dependency or call back
from XIOS into PCTMP; each project contains its own helper and build inputs.

The graphics owner can use cursor, character read/write, TTY, scroll,
pixel read/write, EGA palette entry writes, VGA palette entry reads and VGA DAC entry services. Pixel
coordinates, page zero, scroll rectangle order/bounds and palette fields
are checked before firmware entry. Mode 13h is the firmware-configured
chain-4 byte-per-pixel mode, with a separate A000h byte backend. It restores
sequencer map masks, graphics-controller state and their index selectors
after each access. Its full 8-bit colour is retained, unlike the
planar bit-7 XOR convention. VGA DAC entries 0–255 use 6-bit RGB components.
The extended packet ABI is documented in `api.md`; legacy native simple
selectors and text/CGA paths remain separate. Text restoration reloads the
ROM text mode/font before redrawing the console. No saved graphics contexts,
EGA monochrome 0Fh, VESA, arbitrary pages or font-loading API is introduced.

`make check-graphics` runs assembled-XIOS validation with synthetic ROM
results, then disposable PCE VGA, EGA and CGA graphics runs. NASM builds only these
host-side test fixtures; production assembly still uses ASM86.

The CGA regression also exposed stale BIOS mode metadata when the native
XIOS programs a physical CGA directly. The ROM pixel writer then treats
640x200 mode 6 as the wrong pixel packing. Legacy text/graphics mode changes
now synchronize BDA mode, column count, page size and page-zero offset;
text restoration updates the same fields. CGA drawing stays on its existing
backend; this does not route CGA through the enhanced planar driver.

Original EGA ROM graphics teletype can issue nested INT 10h calls. The
existing masked firmware guard now saves the live INT 10h vector on its
private stack, temporarily points it at captured firmware, and restores
the intercepted vector before restoring the PIC mask. Nested ROM services
therefore stay in the ROM instead of reentering PCTMP and overwriting its
per-console interrupt frame. The native-only build has no PCTMP vector to
replace. The graphics live fixture checks teletype drawing and cursor advance.

Validation: 177 assembled-XIOS cases; live PCE VGA/EGA/CGA graphics,
including teletype; kernel regressions and every packaged image payload.

## DOS 37h: get/set switch character

`ms2.a86` implements AL=0 (query in DL) and AL=1 (set from DL),
returning AL=0 on success. All other selectors, including device-availability
selectors 2/3, return AL=FFh with carry clear and leave state/DX unchanged.
The default is `/`; all byte values are accepted, matching DOS 2.0’s setter.
The existing alignment byte beside the break setting holds the value, so the
PCTMP DATA size and following field offsets do not change. State is per
console, shared across EXEC and subsequent root launches on that console.
The native shell and command-specific option grammars are unchanged.

BDOS 110 is implemented in CIO, but it controls the string terminator used
by native BDOS 9. It is not a DOS switch-character service. DOS 37h does not
call or modify it. No BDOS, XIOS, pathname parser or EXEC changes are needed.

`make check-dos-switch` tests the assembled handler with distinct CODE/DATA:
all 256 byte values, all unsupported selectors, caller fields/status and
console isolation. Disposable PCE tests check registers, the native output
delimiter, EXEC child changes seen by its parent, and the next root launch.

## DOS allocation information: unsigned drive validation

INT 21h/1Ch shared its selector with 1Bh and the allocation stage of 36h.
DEC DL followed by JNS treated invalid input codes 81h–FFh as “current drive”.
The selector now tests zero explicitly, accepts native drive codes 1–16
(A:–P:), and rejects larger unsigned values before calling BDOS or changing
native process drive state. 1Ch returns AL=FFh and 36h returns AX=FFFFh on
these errors. Selection/DPB failures retain their existing handling.

Normal results are preserved. FAT12/FAT16 geometry and the actual FAT-buffer
pointer remain unchanged, including the media-descriptor byte at offset zero.
The native FAT loader fills that buffer on login; replacing the pointer with
a synthetic descriptor is unnecessary and would reduce legacy FAT access.
CP/M media still provides allocation geometry without a DOS FAT contract.
1Bh/1Ch are therefore recorded as Implemented with the media distinction in
the API limits column; 36h remains Implemented with its invalid-drive bug fixed.
The FAT12/FAT16 DPB marker comment and synthetic fixture labels are corrected;
the existing marker comparison and geometry calculations are unchanged.

The standard assembled regression covers all 256 selector values with
successful/failed selection (512 cases), plus the 36h-to-1Ch path through
a synthetic software-interrupt bridge. Existing FAT12/FAT16/CP/M/external-DPB
cases retain their geometry, pointer and drive-restoration assertions.
`make check-dos-allocation` also boots disposable PCE CP/M/FAT media and checks
1Bh/1Ch/36h against the FAT BPB and actual descriptor byte, unchanged FAT
pointer, invalid-drive returns and preservation of the current drive.

### TREE and the small BATCH language (issues #26 and #25)

TREE.CMD is a new native C command using the existing DR C/RASM86 toolchain.
It follows the DOS Plus TREE interface and SDIR's FAT-entry guard. Separate
regular-file and directory searches collect immediate logical byte counts and
walk directories in disk order. Child searches rescan parents instead of
retaining BDOS search state across descent. Mappings remain process-private;
CP/M disks are rejected. TREE is on the tools disk with rebuilt HELP text.

PCTMP and BATCH process ECHO before filename parsing, retaining case and literal
$ characters. The shared language.lib has identical local copies, with BATCH
features conditionally assembled; no cross-project dependency is introduced.
Only BATCH accepts ECHO=ON/OFF and @ECHO. Restricting state changes to scripts is
intentional. @DIR and arbitrary @command prefixes remain unsupported.

BATCH reads/classifies each line before prompt/command echo. Labels are silent;
SHIFT moves the argument buffer without replacing script identity. GOTO scans
raw records from the start with substitution disabled, so skipped lines neither
execute nor expand parameters. Missing labels terminate this BAT normally after
an error. No CALL stack, IF, FOR or environment expansion is introduced.

ECHO.CMD uses a native RASM86/LINKCMD build without a runtime. Its BDOS
console calls work with GET/PUT/RDR; KEEP_TAIL preserves case. The standalone
command is on the tools disk; no ECHO.EXE is distributed. PAUSE remains a
PCTMP/BATCH built-in, with no redundant standalone command.
HELP LANGUAGES BATCH documents the script-only features; check-tree and
check-batch-language exercise disposable PCE media.

### Opt-in native CMD command-tail case preservation

The native CLI previously uppercased every disk-loaded CMD tail, so a DOS
child launched through PUT/GET/RDR received altered arguments. The wrappers
could not restore the original case after their own launch.

A local CMD-header extension assigns byte 7Fh bit 1 (02h) to KEEP_TAIL. The
loader already retains the header flag byte in lod_lbyte. command.sup copies
that byte to CH before selecting the child's base-page DS, then counts the
tail in CL while conditionally skipping only ASCII a-z conversion. Ordinary
unmarked commands retain their historical uppercase tails. Filename parsing,
default FCB generation, directory attributes and DOS APIs are unchanged.
The local pre-change cmdh.def and known DRI flag descriptions assign no
meaning to bit 1; none of the 60 retained CMD reference binaries examined in
CDOS/CCP/M/CP/M base directories has it set. This is explicitly a project
extension, not a promise about every third-party loader or format checker.
Reference: https://www.seasip.info/Cpm/cmdfile.html

CHSET adds TAIL=KEEP/UPPER, stored as a fifth settings field. Its bit-pattern
table and all record/query bounds are extended, and the settings display
buffer grows to 128 bytes. Existing settings leave the new bit unchanged.
Host CMDMOD uses the version-agnostic `-f bit=0|1` operation; `-f 1=1`
changes only this flag, retaining the remaining file bytes exactly. BATCH/ECHO/PUT/GET/RDR set KEEP
in their local builds; cpmtools directory-attribute commands are not involved.
Wrapper option parsers already accept upper/lowercase A/E/EI/EO. BDOS filename
parsing is still case-insensitive; DOS child argument text is not normalized.
Unmarked native children launched by the wrappers are still uppercased by
P_CLI. Unpatched stock kernels retain their previous behaviour.

CMDMOD has separate raw-bit and unchanged-payload tests in its own project.
make check-cmdtail verifies the marked CMDs opt in and exercises
all 256 header-flag combinations against 127 non-NUL bytes through the actual
assembled CLI conversion loop. Disposable PCE tests exercise CHSET toggles,
native opt-in/default behaviour and all three wrappers with DOS COM/EXE,
mixed-case filenames/extensions/options and append. No TREE/ECHO/BATCH logic
is changed by this workstream.

The HELP index checker follows the native dollar-sentinel terminator rather
than assuming a 2 KB index; the expanded LANGUAGES entries cross that old bound.
Live help checks read the nested ECHO, SHIFT and GOTO topics. The existing
CHKCPMFS command also gains its missing help topic so packaged-command coverage
remains complete.

BATCH.CMD opts into KEEP for its own incoming argument list. Its command and
label recognition remains case-insensitive; substitution and SHIFT retain the
argument bytes. Live BATCH tests use mixed-case arguments from both FAT and
CP/M scripts. The README marks the shipped KEEP binaries, and batch.md is the
complete implemented-language reference included in the release archive.

### BATCH EXIT and default return status

EXIT is a BATCH-only command. EXIT without an operand returns 0; an explicit
unsigned decimal 0-255 is written through existing native BDOS 108 before
BDOS 0 terminates the process. Invalid values/signs/hex/extra operands report
an error without terminating. Normal script EOF/Ctrl-Z, missing-label and
script-disappeared paths explicitly return 0 instead of leaking the previous
child status. Kernel-fatal and Ctrl-C termination paths are unchanged.

The PCTMP assembly condition excludes EXIT entirely: its rebuilt binary is
unchanged. There is no new kernel API or DOS return-code conversion. A native
parent fixture verifies explicit/bare EXIT, EOF after a child returns 77,
invalid syntax and chain replacement through real BDOS 108, including repeat
reads. Documentation is in batch.md and HELP LANGUAGES BATCH EXIT.
