# Concurrent DOS 4.1 command dispatch

Current PC-MODE build, based on `kernel/rsp3/tmpmenu.lib`, `tmpdir.lib`
and `kernel/sysgen/Makefile`. Alias targets require the named external file. The named aliases also apply
to BATCH.CMD; its separate TMP source copies implement the same rewrites.

| Command / input | Kind | Action / target |
| --- | --- | --- |
| `A:` ... `P:` | TMP | Select the default drive. |
| `USER [0..15]` | TMP | Display or change the CP/M user number. |
| `DIR [filespec]` | TMP | Built-in directory listing; `/L` long, `/W` wide, `/P` pause, `/S` system files only. |
| `CLS` | TMP, local addition | Clear the screen and home the cursor. |
| `ORDER [CMD,COM,EXE,BAT]` | TMP | Display or set executable-extension search order. |
| `COMSIZE [kilobytes]` | TMP | Display or set the DOS program memory size. |
| `ADDMEM [kilobytes]` | TMP | Display or set additional DOS program memory. |
| `8087 [ON\|OFF]` | TMP | Display or change DOS 8087 use; enabling requires an installed coprocessor. |
| `SUSPEND [ON\|OFF]` | TMP | Display or change DOS suspension when its console is switched away. |
| `PRINTER [number]` | TMP | Display or select the printer/list device. |
| `PAUSE` | TMP | Display `Press any key to continue...` and wait for a key. |
| `REM [text]` | TMP | Ignore the rest of the line. |
| `SYS [text]` | TMP | Accepted and ignored; this handler performs no system-disk operation. |
| `RUNMENU` | TMP/menu interface | Activate the linked menu manager. |
| `STOP name window` | TMP | Abort the named process on the specified one-based window/console number. |
| `STOP` without arguments | Alias | `STOP.CMD`. |
| `CD` | Alias | `CHDIR.CMD`; preserve the remaining arguments. |
| `MD` | Alias | `MKDIR.CMD`; preserve the remaining arguments. |
| `RD` | Alias | `RMDIR.CMD`; preserve the remaining arguments. |
| `DEL` | Alias | `ERA.CMD`; preserve the remaining arguments. |
| `DELQ` | Alias | `ERAQ.CMD`; preserve the remaining arguments. |
| `RENAME` | Alias | `REN.EXE`; preserve the remaining arguments. |
| Escape on an otherwise empty line | Conditional alias | Substitute the configured VCCP command when the CCP/VCCP interface is active. |
| A line beginning with `;` or `.` | TMP | Comment; skip the line. |
| `P_CLI` (BDOS 150) | Kernel CLI | Dispatch an RSP queue or load `.CMD`; DOS `.COM`/`.EXE` uses the separate PC-MODE `ms_p_cli` service 1, and `.BAT` uses BATCH. |
| An unqualified resident command name | RSP dispatch | Try a named queue before disk lookup; an explicit drive or extension bypasses this route. |
| `PCTmp0` ... `PCTmp5` | System RSPs | Resident shell instances, rather than command aliases. |
| `PIN`, `CLOCK`, `CONFIDD` | System RSPs | Keyboard input, timekeeping and configuration services; no standalone utility-command RSPs are selected by this sysgen. |
