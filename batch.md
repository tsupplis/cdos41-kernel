# BATCH command-file language

This describes the BATCH.CMD shipped by this CDOS rebuild. It runs native
CMD programs, DOS COM/EXE programs and shell commands from a `.BAT` file.
It includes the local ECHO, SHIFT, labels/GOTO, EXIT and environment-substitution extensions. It is distinct
from SUBMIT's `.SUB` language and is not a complete COMMAND.COM replacement.

## Starting and ending a script

```text
DEMO.BAT argument1 argument2
B:DEMO.BAT argument1 argument2
```

The extension can be omitted when the current ORDER setting finds the BAT
file. `ORDER` selects the extension search order; `SYSDISK` controls system
searching. An explicit drive or extension selects that form directly.
PCTMP can also run `STARTUP1.BAT` through `STARTUP6.BAT` for consoles 0–5.

A script runs one command per line. Use CR/LF text and terminate the last
command with a line ending. Ctrl-Z marks text EOF; record padding after it
is ignored. FAT files can also end at their recorded file length. Empty
lines do not produce extra prompts. There is no continuation-line syntax;
keep each expanded command within 127 characters.

Reaching EOF ends BATCH with status 0, irrespective of the last command's
status. Invoking another BAT file **chains** to it: the
replacement receives its own arguments and execution does not return to the
calling script. CALL and a nested script-return stack are not implemented.
EXIT ends the BATCH process explicitly; there is no implicit `:EOF` label.

## Arguments and substitution

| Form | Meaning |
| --- | --- |
| `%0` | Script name as supplied in the invocation, until shifted |
| `%1` … `%9` | Positional arguments; absent arguments expand to empty text |
| `%%` | A literal percent sign |
| `%NAME%` | Current console environment value; names match without case, undefined names expand to empty text |
| `SHIFT` | Advance the argument list: old `%1` becomes `%0`, old `%2` becomes `%1`, and so on |

Initial arguments are split on spaces, commas and exclamation marks. Use
ordinary spaces for portable scripts. Double quotes do not group arguments.
SHIFT changes the argument list, including `%0`; it does not change the
actual script file or its saved location. Repeated SHIFT after the arguments
are exhausted leaves empty arguments.

For `DEMO RED BLUE`, this script prints RED and then BLUE:

```bat
@ECHO=OFF
ECHO %1
SHIFT
ECHO %1
```

Substitution is one pass over each complete line before command dispatch and
command echo, including messages and comments. It can supply a command name
as well as arguments. Inserted values and positional arguments retain case;
percent signs inside them are never expanded again. `%10` means `%1` followed
by a literal `0`, not argument ten. `%%NAME%%` prints literal `%NAME%`.
An unmatched `%` remains literal. `%*`, `%~1` and FOR variables are unsupported.

`%NAME%` reads the owning console's shared environment, also used by PATH and
SETENV. Each line gets a fresh snapshot, so changes made by a previous command
are visible. Other consoles keep their own environments. For example:

```bat
@ECHO=OFF
SETENV DEST=B:
ECHO Copying to %DEST%
PIP %DEST%=A:*.TXT
```

BATCH remains a native CP/M program. It discovers the environment through the
owning PCTMP's read-only native `ms_func` query; it does not call INT 21h or
launch a DOS helper for expansion. Older PCTMP versions without the query
still support positional arguments and `%%`; a named expansion reports an
unavailable environment and skips that command.

Double quotes are ordinary text during expansion; they do not group BATCH
arguments or suppress substitution. A raw or expanded line longer than 127
characters is reported and skipped entirely, rather than executed truncated.
GOTO searches raw labels without substitution. IF remains unimplemented.

## ECHO and command echo

| Syntax | Effect |
| --- | --- |
| `ECHO message` | Display the message followed by CR/LF |
| `ECHO` | Display this script's current `ECHO=ON` or `ECHO=OFF` setting |
| `ECHO=ON` | Enable subsequent command/prompt echo |
| `ECHO=OFF` | Disable subsequent command/prompt echo |
| `@ECHO=ON` / `@ECHO=OFF` | Change the setting without echoing this ECHO command line |
| `@ECHO message` | Display a message without echoing its command line |

Echo starts ON in a new BATCH process and is retained when that process
chains to another BAT file. OFF suppresses script prompts and command lines;
it does not suppress ECHO messages, program output or errors. `ECHO=OFF`
itself is echoed if echo was ON; use `@ECHO=OFF` for a quiet first line.

The equals sign is intentional: `ECHO ON` and `ECHO OFF` print those words.
There must be no space between `@` and `ECHO`. **Only @ECHO is supported**;
`@DIR` and an arbitrary `@command` prefix are not supported.

Message case and dollar signs are preserved. Quotes in an ECHO message are
printed literally. There is no special `ECHO.` blank-line syntax. The
standalone `ECHO.CMD` with no arguments can print a blank line.

Interactive PCTMP ECHO and standalone ECHO.CMD are text-output commands;
the echo-state controls above belong only to BATCH. See [ECHO](commands/echo/README.md).

## Labels and GOTO

```bat
@ECHO=OFF
GOTO finished
ECHO This line is skipped
:finished
ECHO Complete
```

| Syntax | Effect |
| --- | --- |
| `:label` | Define a silent label line |
| `GOTO label` | Continue after the matching label |
| `GOTO :label` | The same jump, accepting a leading colon |

Labels are case-insensitive single words; use letters, digits and underscores.
Leading whitespace is permitted. Additional text after a label word does
not form part of its name. Label lines are not echoed or executed.

GOTO searches from the beginning of the current script, supporting forward
and backward jumps. The first matching label wins. The search reads raw
lines without parameter substitution and does not execute skipped commands.
A missing label prints `Label not found; BATCH stopped.` and ends BATCH.
`GOTO :EOF` has no special meaning: it requires an actual `:EOF` label.

## EXIT and return status

| Syntax | Effect |
| --- | --- |
| `EXIT` | Stop BATCH immediately with status 0 |
| `EXIT n` | Stop BATCH immediately with decimal status 0–255 |
| Normal EOF / Ctrl-Z | Stop BATCH with status 0, even after a nonzero child result |

EXIT publishes the status through native BDOS function 108 before terminating
with function 0. The native parent can read it through function 108; this does
not change DOS AH=4Dh or PCTMP's private shell status. EXIT is BATCH-only and
does not terminate the resident PCTMP. It ends the whole BATCH process; there
is no CALL stack to return through.

Signs, hexadecimal notation, values above 255 and extra operands are rejected.
Invalid EXIT syntax reports an error and continues reading the script; it
does not terminate or change the return status. Use `EXIT 0` for an explicit
successful stop. There is no implicit “return the last command's status”.

## Comments

| Form | Effect |
| --- | --- |
| `REM text` | Comment |
| `; text` | Comment line |
| `. text` | Comment line |

Leading whitespace is accepted. These are whole-line forms; there is no
inline-comment operator after an ordinary command. Normal comment lines
can be echoed when echo is ON; label lines remain silent.

## Shell commands available in BATCH

| Command | Purpose |
| --- | --- |
| `A:` … `P:` | Change the default drive |
| `USER [0..15]` | Display/change the CP/M user number |
| `DIR [filespec]` | List files; `/L`, `/W`, `/P`, `/S` and corresponding bracket forms are supported |
| `CLS` | Clear the screen |
| `PAUSE` | Display `Press any key to continue...` and wait for a key |
| `ORDER [CMD,COM,EXE,BAT]` | Display/change executable extension search order |
| `COMSIZE [kilobytes]` | Display/change DOS program memory size |
| `ADDMEM [kilobytes]` | Display/change additional DOS program memory |
| `8087 [ON\|OFF]` | Display/change DOS coprocessor policy |
| `SUSPEND [ON\|OFF]` | Display/change suspension when switching consoles |
| `PRINTER [number]` | Display/select the printer |
| `RUNMENU` | Request the linked shell menu |
| `STOP name window` | Stop the named process on the specified console/window |
| `SYS [text]` | Accepted and ignored; does not install a system disk |

ECHO, SHIFT, GOTO, EXIT, labels and comments are described above. The existing
setting commands retain their native syntax; for example `SUSPEND=ON`.
Detailed shell options are in [ccp.md](ccp.md) and HELP.

| Alias | External command |
| --- | --- |
| `CD` / `MD` / `RD` | CHDIR.CMD / MKDIR.CMD / RMDIR.CMD |
| `DEL` / `DELQ` | ERA.CMD / ERAQ.CMD |
| `RENAME` | REN.EXE |
| `STOP` without arguments | STOP.CMD |

Alias targets and other external commands must be available on the selected
search path. Unqualified resident commands can also dispatch through their
native command queues. An explicit filename/extension requests the disk form.

PATH is a true BATCH/PCTMP built-in. `PATH` displays the DOS
environment PATH; `PATH=value` or `PATH value` sets it, preserving case.
`PATH=` or `PATH ;` clears it; no external PATH file is needed.
SYSDISK.CMD controls native system searching, accepting a drive/path or
`[ON]`/`[OFF]`. It is external and must be available on the command search
path or invoked with an explicit drive. It is supplied on maintenance media.
`nD:` selects CP/M user 0–15 and drive A–P together; DIR `/Gn` or `[Gn]`
uses that user only for its listing. SET changes file/disk attributes,
while SETENV.CMD edits environment variables.

## Case handling and redirection

Command and label recognition ignores ASCII letter case. Script text is
read without blanket uppercasing, so literal ECHO messages retain their case.
The native loader separately controls the invocation arguments delivered to
BATCH and other CMD files: normal `TAIL=UPPER` uppercases them; `TAIL=KEEP`
preserves them. BATCH.CMD is built with KEEP, so positional arguments retain
their supplied case through substitution and SHIFT. This is independent of whether
a script is stored on a FAT volume using lowercase name flags.

The shipped **BATCH.CMD, ECHO.CMD, PUT.CMD, GET.CMD, RDR.CMD, SETENV.CMD and PATH.CMD** use TAIL=KEEP.
KEEP preserves argument text; it does not make filenames or wrapper options
case-sensitive. A native child still follows its own TAIL setting. DOS
COM/EXE tails do not use this native CMD-header flag. See
[CHSET](commands/chset/README.md) and [PUT/GET/RDR](commands/putget/README.md).

```bat
PUT [LIST.TXT] SDIR.CMD *.CMD
GET [KEYS.IN] PIP.CMD
RDR [KEYS.IN,SESSION.TXT] PIP.CMD
PUT [MESSAGE.TXT] ECHO.CMD Hello
```

These use the CP/M-Plus GET/PUT/RDR pattern, extended to DOS programs. The
standalone command form matters: shell built-ins, BIOS/direct video and
explicit CON access are outside this redirection interface. BATCH does not
parse `<`, `>`, `>>`, pipes, `&` command lists or parenthesized blocks.
Native text capture uses CP/M record padding; DOS stream capture retains
its byte-length semantics.

## Not implemented

| Feature | Status |
| --- | --- |
| IF / IF NOT, EXIST, DIREXIST, string comparisons | Not implemented |
| IF ERRORLEVEL | Not implemented; no conditional status test or stop-on-error language switch |
| FOR | Not implemented |
| CALL and return to a calling BAT | Not implemented; bare BAT invocation chains |
| Interactive `%NAME%` expansion | Not implemented in PCTMP; supported in BATCH only |
| Quoted argument grouping and general escaping | Not implemented by BATCH; individual programs can parse their own arguments |
| General `@command` suppression | Intentionally restricted to @ECHO |
| PROMPT | Not implemented |
| Interactive EXIT | Not implemented; EXIT is deliberately BATCH-only |
| DOS redirection operators and pipelines | Not implemented; use GET/PUT/RDR for external programs |

An ordinary command error is not a structured language exception. There is
no IF-based recovery or automatic success/failure branching. Missing GOTO
labels and fatal script-read failures stop BATCH.

Build/source notes are in [commands/batch/README.md](commands/batch/README.md).
`make check-batch-exit` tests explicit/default status, invalid operands and
chaining against a real parent's BDOS 108.
`make check-batch-language` tests ECHO controls, SHIFT, forward/backward GOTO,
record boundaries, FAT/CP/M scripts and standalone ECHO redirection.
