# CDOS BATCH

Recompiled from the native 4.1 TMP/BATCH sources; this is not the CCP/M
BATCH reconstruction. The shell and BATCH have separate source copies of
tmpmenu.lib/tmpdir.lib and receive the same applicable local corrections.

BATCH retains DEL -> ERA.CMD, DELQ -> ERAQ.CMD and RENAME -> REN.EXE.
It implements DIR, CLS, USER and the other supported TMP built-ins.
USER omits the redundant CP/M-media note and PAUSE uses
`Press any key to continue...`. DIR accepts native slash options and CP/M
brackets, including a final omitted ]. BATCH is not a full COMMAND.COM:
IF supports EXIST/DIREXIST with optional NOT; comparisons, FOR and CALL remain
unimplemented. BATCH expands `%NAME%` from the current
console environment before command dispatch.

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
