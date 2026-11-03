# Concurrent DOS 4.1 command dispatch

This table identifies each command implementation and the routes that invoke
**that implementation**. PATH, SETENV, ECHO, DIR and SYSDISK are listed as standalone
external commands. Other external names appear only as shell-alias targets.
The complete BAT language is documented in [batch.md](batch.md).

| Implementation | Meaning |
| --- | --- |
| TMP | Built into the interactive PCTMP command processor |
| BATCH | Implemented by BATCH.CMD while processing a BAT file |
| RSP | A standalone resident command accepting requests through an RSP queue |
| EXTERNAL | A program loaded from disk |

`CMDLINE` means the interactive PCTMP prompt; `BATCH` means a line in a BAT
file. `P_CLI` is native BDOS 150; `MS_P_CLI` is PCTMP's private DOS loader,
ms_func selector 1. The API columns describe direct invocation: neither API
parses the shell's built-ins or aliases. Launching BATCH.CMD to execute a
script is an indirect route, not direct API support for each script command.
See [api.md](api.md#pctmp-private-far-call-interface) for the DOS-loader packet.

## Built-ins and command-file language

| Command or variation | Implementation | Can be called from | Behavior |
| --- | --- | --- | --- |
| `A:` … `P:` | TMP, BATCH | CMDLINE, BATCH | Select the default drive |
| `USER` | TMP, BATCH | CMDLINE, BATCH | Display the CP/M user number |
| `USER 0` … `USER 15` | TMP, BATCH | CMDLINE, BATCH | Change the CP/M user number |
| `DIR [filespec]` | TMP, BATCH | CMDLINE, BATCH | Built-in directory listing |
| `DIR [filespec] /L` or `[L]` | TMP, BATCH | CMDLINE, BATCH | Long listing |
| `DIR [filespec] /W` or `[W]` | TMP, BATCH | CMDLINE, BATCH | Wide listing |
| `DIR [filespec] /P` or `[P]` | TMP, BATCH | CMDLINE, BATCH | Pause after a screenful |
| `DIR [filespec] /S` or `[S]` | TMP, BATCH | CMDLINE, BATCH | System files only |
| `ECHO text` | TMP, BATCH | CMDLINE, BATCH | Print literal text, preserving case and dollar signs |
| `ECHO` without text, interactively | TMP | CMDLINE | Print a blank line |
| `ECHO` without text, in a BAT file | BATCH | BATCH | Display the script's echo setting |
| `ECHO=ON`, `ECHO=OFF` | BATCH | BATCH | Change command/prompt echo for this script |
| `@ECHO text`, `@ECHO`, `@ECHO=ON`, `@ECHO=OFF` | BATCH | BATCH | Execute the ECHO form without echoing its command line; no general `@command` prefix |
| `CLS` | TMP, BATCH | CMDLINE, BATCH | Clear the screen and home the cursor |
| `ORDER` | TMP, BATCH | CMDLINE, BATCH | Display the executable-extension search order |
| `ORDER=ext1[,ext2...]` | TMP, BATCH | CMDLINE, BATCH | Set up to four extensions from CMD, COM, EXE and BAT |
| `COMSIZE`, `COMSIZE=kilobytes` | TMP, BATCH | CMDLINE, BATCH | Display or set minimum DOS-program memory allocation |
| `ADDMEM`, `ADDMEM=kilobytes` | TMP, BATCH | CMDLINE, BATCH | Display or set additional DOS-program memory allocation |
| `8087`, `8087=ON\|OFF` | TMP, BATCH | CMDLINE, BATCH | Display/change DOS coprocessor policy; ON requires an installed 8087 |
| `SUSPEND`, `SUSPEND=ON\|OFF` | TMP, BATCH | CMDLINE, BATCH | Display/change whether DOS execution suspends when its console is switched away |
| `PRINTER`, `PRINTER=number` | TMP, BATCH | CMDLINE, BATCH | Display or select the list/printer device |
| `PAUSE` | TMP, BATCH | CMDLINE, BATCH | Print `Press any key to continue...` and wait for a key |
| `REM [text]` | TMP, BATCH | CMDLINE, BATCH | Ignore the rest of the line |
| A line beginning with `;` or `.` | TMP, BATCH | CMDLINE, BATCH | Comment |
| `SYS [text]` | TMP, BATCH | CMDLINE, BATCH | Accepted and ignored; no system-disk operation |
| `RUNMENU` | TMP; BATCH forwards to TMP | CMDLINE, BATCH | Activate the linked menu manager |
| `STOP name window` | TMP, BATCH | CMDLINE, BATCH | Stop the named process on the one-based window/console number |
| `SHIFT` | BATCH | BATCH | Advance positional arguments: old `%1` becomes `%0` |
| `:label` | BATCH | BATCH | Define a silent jump target |
| `GOTO label`, `GOTO :label` | BATCH | BATCH | Find the first matching label, ignoring case |
| `EXIT`, `EXIT n` | BATCH | BATCH | End BATCH with native BDOS 108 status 0 or decimal n (0–255); normal EOF also returns 0 |
| `%0` … `%9`, `%%` | BATCH | BATCH | Substitute positional arguments or a literal percent before dispatch |
| `%NAME%` | BATCH | BATCH | Substitute a current-console environment value before dispatch; no interactive expansion |

Built-in DIR options can be combined. The closing `]` is optional. External
DIR.CMD has its own options below; its `[S]` behavior differs.

`ECHO ON` and `ECHO OFF` print those words; they do not change state. Interactive
`ECHO=ON/OFF` prints ordinary message text rather than setting an echo mode.
Explicit drive/extension forms bypass the shell's DIR dispatch. Use `DIR.CMD`
and `ECHO.CMD` to select the external programs unambiguously.

## Shell aliases

These rewrites belong to TMP/BATCH, not to P_CLI or MS_P_CLI. The target file
must be available. An API may separately launch a target using the appropriate
loader, but that does not implement the alias itself.

| Command or variation | Implementation | Can be called from | Behavior |
| --- | --- | --- | --- |
| `CD [arguments]` | TMP, BATCH | CMDLINE, BATCH | Rewrite to CHDIR.CMD, preserving arguments |
| `MD [arguments]` | TMP, BATCH | CMDLINE, BATCH | Rewrite to MKDIR.CMD, preserving arguments |
| `RD [arguments]` | TMP, BATCH | CMDLINE, BATCH | Rewrite to RMDIR.CMD, preserving arguments |
| `DEL [arguments]` | TMP, BATCH | CMDLINE, BATCH | Rewrite to ERA.CMD, preserving arguments |
| `DELQ [arguments]` | TMP, BATCH | CMDLINE, BATCH | Rewrite to ERAQ.CMD, preserving arguments |
| `RENAME [arguments]` | TMP, BATCH | CMDLINE, BATCH | Rewrite to REN.EXE, preserving arguments |
| `STOP` without arguments | TMP, BATCH | CMDLINE, BATCH | Select STOP.CMD rather than the built-in STOP handler |
| Escape on an empty interactive line | TMP | CMDLINE | Select the configured VCCP command when that interface is active |

## Selected external commands

| Command or variation | Implementation | Can be called from | Behavior |
| --- | --- | --- | --- |
| `PATH`, `PATH.EXE` | EXTERNAL (DOS EXE) | CMDLINE, BATCH, MS_P_CLI | Display or change the DOS environment's PATH; not a PCTMP/BATCH built-in |
| `SYSDISK`, `SYSDISK.CMD` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Display this window's native system search drive/path |
| `SYSDISK d:` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Select the system search drive |
| `SYSDISK {d:}subdir{\subdir...}` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Select a DOS/FAT system search subdirectory |
| `SYSDISK [ON]`, `SYSDISK [OFF]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Enable or disable native system searching |
| `SETENV`, `SETENV.CMD` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | List the current console's environment |
| `SETENV NAME` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Display one variable, ignoring name case |
| `SETENV NAME=value` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Add/replace; names are stored uppercase, values preserve case/spaces |
| `SETENV NAME=` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Remove a variable |
| `SETENV [HELP]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Display native-style usage; `/?` is not a help switch |
| `ECHO.CMD [text]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Print text and CR/LF; an empty tail prints a blank line; no echo-state controls |
| `DIR.CMD [filespec ...]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Standalone native directory listing; distinct from the shell's DIR |
| `DIR.CMD [filespec ...] [S]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Include system files as well as ordinary directory files |
| `DIR.CMD [filespec ...] [P]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Enable paging |
| `DIR.CMD [filespec ...] [Gn]` | EXTERNAL (native CMD) | CMDLINE, BATCH, P_CLI | Select CP/M user n (0–15) for listing |

Native CMD programs use P_CLI; PATH.EXE uses MS_P_CLI. P_CLI does not launch
DOS EXEs, and MS_P_CLI does not execute native CMDs or BAT files. The shell and
BATCH select the appropriate loader; their availability does not imply that
the two APIs are interchangeable. Neither API provides shell filename-search
and alias behavior merely by accepting the same command text.

## Current gaps and agreed direction

- **PATH:** the current build still produces PATH.EXE. The requested replacement
  is native PATH.CMD, with `PATH` and `PATH=...` accepted by TMP/BATCH and routed
  to that one implementation. The explicit external file will then use P_CLI,
  not MS_P_CLI. That conversion and dispatch change are not implemented yet;
  the table above records the current executable.
- **User/drive shorthand:** the current shell recognizes only bare `A:` … `P:`.
  `1C:`, `2C:` and other user-prefixed forms are not implemented. Use `USER 1`
  followed by `C:` today. Proposed shorthand accepts users 0–15 and drives
  A–P in both TMP and BATCH, validates both before changing context and leaves
  the previous context intact on failure. A user number is a CP/M user area,
  not a FAT subdirectory.
- **SYSDISK:** already implemented as an external native CMD, not a TMP/BATCH
  built-in. It controls native system searching; PATH controls the DOS
  environment. They are separate facilities, both listed above.

## RSP implementation in this build

The CCP/M-86 project includes DIR.RSP. **This CDOS project does not:**
`commands/dir/dir.plm` selects a CMD build and `kernel/sysgen/Makefile` selects
only PIN, CLOCK, PCTMP and CONFID RSP modules. Its interactive DIR is compiled
into PCTMP through tmpdir.lib; BATCH has a separate compiled copy. DIR.CMD is
the standalone alternative. No standalone command RSPs are selected by this sysgen. PCTmp0 … PCTmp5 are
resident shell instances; their built-ins are classified **TMP** above, not
standalone RSP commands. PIN, CLOCK and CONFIDD are system services, not
interactive utility commands.

P_CLI can dispatch an unqualified command to a matching RSP queue before trying
a CMD file. An explicit drive or extension bypasses that queue route. This
kernel mechanism does not make every PCTMP built-in callable through P_CLI.

The implementation references are `kernel/rsp3/tmpmenu.lib`, `tmpdir.lib`,
`language.lib`, the corresponding `commands/batch/` sources, native
`kernel/con/command.sup`, and the RSP list in `kernel/sysgen/Makefile`.
