# CDOS BATCH

Recompiled from the native 4.1 TMP/BATCH sources; this is not the CCP/M
BATCH reconstruction. The shell and BATCH have separate source copies of
tmpmenu.lib/tmpdir.lib and receive the same applicable local corrections.

BATCH retains DEL -> ERA.CMD, DELQ -> ERAQ.CMD and RENAME -> REN.EXE.
It implements DIR, CLS, USER and the other supported TMP built-ins.
USER omits the redundant CP/M-media note and PAUSE uses
`Press any key to continue...`. DIR accepts native slash options and CP/M
brackets, including a final omitted ]. BATCH is not a full COMMAND.COM:
IF supports EXIST/DIREXIST, case-sensitive string equality and ERRORLEVEL
thresholds, all with optional NOT. FOR supports lists, ranges and native file
snapshots. CALL runs a child BAT and resumes the caller. BATCH
expands `%NAME%` from the current console environment before dispatch.

`make check-batch-live` checks messages, CLS/DEL and an unrelated sentinel
on disposable CP/M images. `make check-dir-options` also executes a BAT
on CP/M media while DIR lists a FAT drive.

`make check-fat-batch` covers FAT-hosted scripts with four short-name case
flag combinations, CR/LF and Ctrl-Z endings, record padding, command-buffer
refills and execution of ERA.CMD from FAT. It checks deletion targets and an
unrelated sentinel. The original close-checksum failure was a FAT-to-FCB
attribute conversion bug in the kernel, corrected in `kernel/con/black.a86`;
see the root patch notes.

BATCH reads each line before echoing its prompt. Empty lines and the
Ctrl-Z/end-of-file transition do not print extra drive prompts.

## Language reference

[batch.md](../../batch.md) documents invocation, arguments, ECHO controls,
SHIFT, labels/GOTO, EXIT/status, comments, built-ins, aliases, command dispatch, case
handling, redirection and unsupported syntax. HELP LANGUAGES BATCH provides
the installed reference.

## Implementation

BATCH.CMD is built with TAIL=KEEP, preserving invocation argument case through
positional substitution and SHIFT. The build check verifies the header flag.

The identical language.lib include in commands/batch and kernel/rsp3 supplies
ECHO and conditionally assembles the BATCH-only features. RASM86 includes it
from the top-level A86 modules because nested includes are unsupported.
GOTO scans raw records with substitution disabled. SHIFT changes arguments
without changing the saved script identity. Echo state belongs to the BATCH
process and remains set when chaining to another BAT file.

Run root make check-batch-language for live regression coverage.

EXIT and normal EOF share the native return-code terminator. EXIT accepts an
optional decimal byte, writes it through BDOS 108 and terminates through BDOS
0. Normal EOF explicitly returns 0 instead of leaking a preceding child's
status. This does not add a resident-shell EXIT or change the kernel APIs.
Run root make check-batch-exit for real parent/child status verification.

Expansion is implemented in expand.lib. It takes one bounded snapshot through
PCTMP ms_func 0Ah, then handles positional arguments, literal percent signs and
named variables in a single pass. Overlong commands are skipped. Language
state and expansion buffers are allocated in tmpdir.lib before dataend, after
the native basepage and existing TMP data; includes must not allocate state
before tmpdir.lib resets the data origin. Run make check-batch-expand for live
CP/M/FAT scripts and per-console environment isolation.

IF is implemented in ifcmd.lib and runs after expansion but before the normal
command dispatcher. FAT path traversal uses native BDOS directory opens. An
initial OPEN of "." creates a private CAT/HDS through native copy-on-write;
subsequent opens reuse its sole-owner HDS. Only the eight mapping bytes are
saved/restored, leaving reference counts to BDOS. CP/M predicates use native
FCB searches. All exits restore the caller's drive, DMA and error mode.
No new kernel API or DOS service is introduced. Run make check-batch-if.

String equality uses pointer/length spans in the already expanded command,
without filesystem calls or scratch operand copies. Quotes delimit whitespace
and protect embedded ==, but remain in the bytewise comparison. The command
tail is copied only after a true result, then redispatched without another
expansion. Empty operands use ""; unterminated quotes and malformed syntax
skip the line. make check-batch-strings covers the linked parser and live
CP/M/FAT scripts; make check also runs the linked-instruction cases.

Expansion keeps a BATCH-only side map of zero-length substitutions ending a
source token. String IF rejects an unquoted missing operand on either side;
it cannot silently consume the first command word as the RHS. No sentinel
bytes enter ordinary command text. True nested IF shifts the side map with
the removed prefix. Quoted empty values and literal suffixes remain valid.

ERRORLEVEL caches completed external-program results after console reacquisition
and before translator cleanup. A pending-launch byte distinguishes native CMD
(BDOS 108) from DOS COM/EXE (read-only PCTMP selector 0Bh); it is not set for
RSPs or built-ins. DOS termination type is excluded, while native word results
remain unsigned. Successful launches replace the cache; rejected launches set
1. Earlier parse/search errors preserve it. The parser accepts decimal 0–255
and shares NOT, syntax recovery and iterative dispatch with the other IF forms.
The DOS query does not consume AH=4Dh, and root DOS handle initialization clears
stale status before a new root program runs. No INT 21h call is added to BATCH.

`python3 tools/batch_status_check.py` (from the project root) validates actual
native and DOS termination on disposable CP/M/FAT script media. The linked-byte
`tools/batch_string_unit_check.py` also covers threshold boundaries and malformed
syntax. See the root `batch.md` for the complete language contract.

FOR lives in `forcmd.lib`, with BATCH-only data appended in `tmpdir.lib`.
`batch_for` recognizes a fully expanded line after IF stripping. `for_next`
feeds generated commands to the existing read/echo/dispatch path without
reading another BAT record or expanding the text again. Signed ranges test
the endpoint before increment to avoid 16-bit wraparound. Quoted list items
remain quoted; a separate body metadata map retains missing-operand checks.

FILES uses `condition_probe`'s existing native BDOS directory traversal and
cleanup, with a narrowly scoped collection callback at `condition_found`.
It saves all regular-file names before executing any body, deduplicates CP/M
extents and restores drive/DMA/error mode and FAT mapping first. The snapshot
is bounded to 4096 bytes; failure prevents partial loop execution. This adds
no DOS interrupt dependency, resident FOR parser or kernel API. GOTO and BAT
replacement cancel the loop; nesting is diagnosed rather than overwriting it.

`tools/batch_for_unit_check.py` executes the linked expansion/parser/renderer
bytes; `tools/batch_for_check.py` validates real CP/M/FAT enumeration, IF/child
search isolation, native/DOS bodies, status and loop termination on copied
images. Run both through the root `make check-batch-for` target.

CALL resides in `callcmd.lib`. After IF/FOR processing it validates one
native non-wildcard BAT filespec through BDOS 152 and `condition_probe`, then
atomically constructs `BATCH.CMD ` plus the original tail. There is no second
expansion pass. The existing native CMD loader and console-reattachment path
perform execution and BDOS 108 status capture. A small `call_pending` marker
also detects interpreter lookup failures before P_CLI is reached. Invalid or
failed CALL sets ERRORLEVEL 1; ordinary bare BAT chaining remains unchanged.

Each level has a native process and independent script/argument/SHIFT/FOR/echo
state; the PCTMP environment stays shared. EOF/EXIT terminates that child and
resumes its caller. The initial implementation accepts `[drive:]name[.BAT]`
in CP/M or mapped FAT directories, with no full-path or label-subroutine syntax.
See root `batch.md` for precise search, echo and command-length contracts.
`make check-batch-call` checks production wrapper bytes and disposable native
emulator runs, including nesting, child chains, DOS execution and loop return.
