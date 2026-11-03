# BATCH command-file language

This describes the BATCH.CMD shipped by this CDOS rebuild. It runs native
CMD programs, DOS COM/EXE programs and shell commands from a `.BAT` file.
It includes ECHO, SHIFT, labels/GOTO, EXIT, environment substitution and
file/directory and string IF extensions. It is distinct from SUBMIT's `.SUB` language
and is not a complete COMMAND.COM replacement.

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
calling script. Use CALL to run another BAT and resume afterward.
EXIT ends the BATCH process explicitly; there is no implicit `:EOF` label.

## CALL and chaining

```bat
CALL OTHER.BAT argument1 argument2
CALL B:OTHER argument1
```

CALL is BATCH-only. It runs a native child BATCH process and resumes the
caller after that process finishes. The target is one unquoted native 8.3
`[drive:]name[.BAT]`; omitting the extension means BAT. Other extensions,
wildcards, passwords, quoted target names and full FAT paths are rejected.
Use a CP/M drive or a FAT drive already mapped to the required directory.
CALL checks the named script in that drive's current directory; it does
not search ORDER, DOS PATH or the system drive for the script argument.
The BATCH.CMD interpreter itself uses ordinary native command searching.

| Form inside a BAT file | Effect |
| --- | --- |
| `OTHER.BAT args` | Chain: replace this script and arguments; never return |
| `CALL OTHER.BAT args` | Run another BATCH and then resume at the next line |
| `BATCH.CMD OTHER.BAT args` | Explicit child-interpreter invocation, without CALL's validation |

A child's `%0`–`%9`, SHIFT, script cursor, FOR state and command echo belong
to that child. The caller retains its own state, so a FOR body can CALL a
script which runs its own FOR. A child starts with command echo ON; use
`@ECHO=OFF` in it when needed. Changing its echo state does not change the
caller's. The console environment remains shared: SETENV/PATH changes are
visible when the caller expands subsequent lines.

Child EOF or bare EXIT returns status 0; `EXIT n` returns n to the caller's
ERRORLEVEL. If that child chains to another BAT, the replacement's eventual
exit returns to the original CALL. Nested calls use native process/memory
resources rather than a private script-return stack; native allocation or
launch failures report status 1. Invalid CALL syntax, a missing/unreadable
script or failure to locate BATCH.CMD also sets 1 and continues the caller.

Environment/argument and FOR substitution happen through the usual single
pass before CALL dispatch. CALL introduces no second percent-expansion pass
and no new argument grouping. `BATCH.CMD ` plus the original CALL tail must
fit the existing 127-character command limit; overflow executes no child.
CALL is supported after IF and in FOR bodies. CALL :label, EXIT /B and
GOTO :EOF are not implemented. No additional CHAIN command is needed.

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
An unmatched `%` remains literal. `%*` and `%~1` are unsupported. FOR uses `%%I` loop placeholders as described below.

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
GOTO searches raw labels without substitution. IF tests the expanded operand.

## IF file and directory tests

| Syntax | Condition |
| --- | --- |
| `IF EXIST filespec command` | At least one matching file exists |
| `IF NOT EXIST filespec command` | No matching file exists |
| `IF DIREXIST directory command` | At least one matching FAT directory exists |
| `IF NOT DIREXIST directory command` | No matching FAT directory exists |

Keywords and filesystem matching ignore case. `EXIST` checks files on CP/M
or FAT, including empty, hidden and system files; directories do not satisfy
it. `DIREXIST` checks FAT directories; CP/M user areas are not directories.
Use native drive/filespec forms such as `A:*.TXT`, or full FAT paths such as
`B:\TOOLS\FILE.CMD`. Relative paths start at that drive's current directory;
a leading `\` starts at its root. `/` is also accepted as a path separator.
`.` and `..` work; the parent of FAT root remains root. A bare `B:` denotes
its current directory. A trailing separator denotes a directory, not a file.

Paths use short 8.3 components. `*` and `?` are supported in the final
component, including directory tests; intermediate components must name a
single directory. Operands containing spaces or quotes are unsupported.

```bat
@ECHO=OFF
IF EXIST A:CONFIG.DAT ECHO Configuration found
IF NOT EXIST B:\SAVE\REPORT.TXT ECHO No saved report
IF DIREXIST B:\TOOLS ECHO Tools directory found
IF EXIST %INPUT% GOTO PROCESS
IF NOT DIREXIST %DEST% EXIT 1
```

Variable/positional substitution happens once, before testing. A true test
executes the rest of that line through the ordinary command paths: shell
built-ins, aliases, drive changes and external programs remain available.
Conditional commands are not expanded again. Nested IF tests are supported
on one line; a false outer test skips the rest. There is no ELSE, block
syntax. String comparisons and return-status tests are described below.

Evaluation restores the original drive, DMA, error mode and directory mapping
before executing or skipping the command. It does not borrow N:/O:/P: as a
scratch drive. Missing files/directories yield false; malformed syntax or a
drive/I/O failure reports an error and skips the command even with NOT.
The whole expanded line still has the 127-character limit.

## IF string comparisons

```bat
IF [NOT] left==right command
IF [NOT] "left text" == "right text" command
IF "%NAME%"=="" ECHO NAME is empty or undefined
IF "%NAME%TOTO"=="TOTO" ECHO NAME is empty or undefined
```

Comparison is case-sensitive and byte-for-byte: `abc==ABC` and `01==1` are
false. There is no numeric conversion, wildcard matching, ordering operator
or `/I` flag. IF and NOT keywords still ignore case. Spaces or tabs may
surround `==`; whitespace inside quoted operands is significant. `==` inside
quotes is literal operand text, not the operator.

Double quotes protect spaces but remain part of the compared text, following
DOS-style literal comparison. `"abc"=="abc"` is true; `"abc"==abc` is false.
Use `""` for an empty operand and quote substituted values on both sides.
An unquoted leading EXIST/DIREXIST followed by whitespace selects the file
predicate; quoting the operand avoids interpreting a value as a keyword.

Substitution occurs before parsing, even inside quotes and next to literal
text. In `IF "%NAME%TOTO"=="TOTO" command`, an empty or undefined NAME makes
both operands `"TOTO"`; NAME=ABC makes the left operand `"ABCTOTO"`. Inserted
percent signs are not expanded again. Substitution is textual: quote characters
in a value participate in parsing; there is no escape/unescape operation.

A true comparison executes its remaining command through the same dispatcher
as file predicates. NOT reverses the result. File and string conditions can
be nested on one line. Missing `==`, unbalanced quotes, missing operands or a
missing command report a syntax error and skip the line, without changing
files, directory mappings or return status. Normal EOF still returns zero;
use EXIT for an explicit result.

A zero-length substitution used as an unquoted whole operand is an error on
either side. The following both report syntax errors when MISSING is undefined
or empty; the command word is never consumed as a substitute right operand:

```bat
IF %MISSING% == VALUE ECHO never executed
IF VALUE == %MISSING% ECHO never executed
```

Use `IF "%MISSING%"=="" command` to test an empty value. A literal suffix,
such as `%MISSING%TOTO`, supplies a nonempty operand and remains valid. These
rules also apply after removing an outer true IF and to missing `%0`–`%9`.

This quote handling applies to comparison operands only. It does not change
positional argument splitting or add quoted filenames to EXIST/DIREXIST.
ELSE and blocks remain unimplemented.

## IF ERRORLEVEL

```bat
IF [NOT] ERRORLEVEL n command
```

True when the last external program's status is **at least** decimal `n`
(0–255); NOT tests whether it is below `n`. Test several thresholds from
highest to lowest when selecting one result. Signs, quoted numbers, values
above 255, a missing threshold or a missing command are syntax errors.

```bat
MYTOOL.CMD
IF ERRORLEVEL 7 ECHO Status is at least seven
IF NOT ERRORLEVEL 1 ECHO Success
```

The status starts at zero for each BATCH invocation. Native CMD programs
supply their full unsigned BDOS 108 word; DOS COM/EXE programs supply the
low-byte exit code from INT 21h/4Ch (or 31h). A root DOS launch starts at
zero, so an INT 20h exit does not reuse an earlier program's result.
Built-ins, RSP dispatch, comments, labels, IF tests and GOTO preserve the
cached status. Replacing the current script with another BAT file preserves
it too. A rejected native/DOS launch sets it to 1. Errors reported before
launch, such as an unknown command, leave it unchanged.

Variable substitution and nested IF work as for the other conditions.
Testing never consumes the status. EXIT and normal end-of-file retain their
separate rules: `EXIT n` returns n; bare EXIT and EOF return zero, regardless
of the last program's status. This feature requires the matching rebuilt
PCTMP, whose read-only native query leaves DOS AH=4Dh untouched.

## FOR iteration

```bat
FOR %%I IN (A, B, "%VAL%", "AA AA") DO ECHO %%I
FOR %%I IN (1..10) DO ECHO %%I
FOR %%I IN (FILES C:\*.COM) DO ECHO %%I
```

The outer `FOR %%I IN (...) DO command` follows DOS batch spelling. Choose
one letter (`A`–`Z` or `a`–`z`); its case matters, so `%%i` and `%%I` are
different variables. Only BATCH implements FOR. Write the doubled percent
in the BAT file; ordinary expansion produces the internal single-percent
placeholder. The loop variable is not an environment variable.

| Set form | Iteration |
| --- | --- |
| `(A, B, "AA AA")` | Discrete items separated by commas, spaces or tabs outside double quotes |
| `(A..B)` | Inclusive signed decimal integer range, from -32768 to 32767; counts up or down by one |
| `(FILES filespec)` | Snapshot of regular files matching one native CP/M/FAT filespec |

Quoted list items retain their quotes in the substituted value, as with DOS
FOR. `"A,B"` and `"A)B"` are each one item; `""` is one quoted empty item.
An empty set performs no iterations. A numeric range must be the sole,
unquoted item; quote `"1..10"` to iterate over that literal text instead.
Leading signs/zeros are accepted in ranges and output is canonical decimal.
Wildcards in an ordinary list remain literal; use FILES for file searching.
FILES is special only when followed by whitespace and its filespec; quote
`"FILES"` when using it as a list item.

FILES accepts native CP/M drive/filespecs and full or relative FAT paths,
including dot and parent components. Wildcards are allowed in the final
component. Directory entries and volume labels are excluded; empty, hidden
and system files are included. Returned values keep the supplied drive/path
prefix and use an 8.3 basename. CP/M extents do not produce duplicate items.
No matches performs no iterations. Search order is native directory order.

All matches are collected before the body runs, so IF or external programs
cannot disturb the search cursor. The NUL-separated snapshot is bounded to
4096 bytes; a search failure or overflow skips the entire FOR. This is not
a recursive search. Use an absolute path if the body changes directories
and later iterations must still refer to the original location.

Environment and positional arguments are expanded once over the original
FOR line, including its body. Each iteration then replaces occurrences of
that loop variable without another environment/argument expansion pass.
Values containing percent signs are not rescanned. Body commands use the
ordinary dispatcher: IF, ECHO, drive changes, native CMD and DOS programs all
work, and ERRORLEVEL reflects each completed external program normally.
Generated commands retain the 127-character limit; overflow stops the loop.

This first implementation supports one active FOR. A nested FOR is diagnosed
and skipped while the outer loop continues. A valid GOTO leaves the loop;
BAT replacement abandons it; EXIT terminates BATCH with its normal rules.
There are no multiline bodies, blocks, /F parser or custom steps. A called
child BATCH can have its own independent FOR.
FOR does not automatically set or clear ERRORLEVEL.

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
is no private CALL stack: when launched by CALL, the native parent resumes
and receives the status.

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
| IF ELSE / blocks | Not implemented; file/directory and string conditions are supported |
| Nested FOR, FOR /F, multiline bodies | Not implemented; single-line lists, ranges and FILES searches are supported |
| CALL :label, EXIT /B, GOTO :EOF | Not implemented; CALL runs a separate BAT process, and bare BAT invocation chains |
| Interactive `%NAME%` expansion | Not implemented in PCTMP; supported in BATCH only |
| Quoted argument grouping and general escaping | Not implemented by BATCH; individual programs can parse their own arguments |
| General `@command` suppression | Intentionally restricted to @ECHO |
| PROMPT | Not implemented |
| Interactive EXIT | Not implemented; EXIT is deliberately BATCH-only |
| DOS redirection operators and pipelines | Not implemented; use GET/PUT/RDR for external programs |

An ordinary command error is not a structured language exception. Use explicit
IF ERRORLEVEL tests for status branching; errors do not automatically stop a script.
Missing GOTO labels and fatal script-read failures stop BATCH.

Build/source notes are in [commands/batch/README.md](commands/batch/README.md).
`make check-batch-exit` tests explicit/default status, invalid operands and
chaining against a real parent's BDOS 108.
`make check-batch-language` tests ECHO controls, SHIFT, forward/backward GOTO,
record boundaries, FAT/CP/M scripts and standalone ECHO redirection.

`make check-batch-if` checks file/directory conditions, full FAT paths, command
dispatch and preservation of directory mappings on disposable images.

`make check-batch-strings` runs linked-instruction comparison tests and native
CP/M/FAT scripts, including empty/value concatenation, quotes, case, nested
predicates, normal command dispatch and EXIT status.
