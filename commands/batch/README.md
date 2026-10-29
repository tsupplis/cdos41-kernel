# CDOS BATCH

Recompiled from the native 4.1 TMP/BATCH sources; this is not the CCP/M
BATCH reconstruction. The shell and BATCH have separate source copies of
tmpmenu.lib/tmpdir.lib and receive the same applicable local corrections.

BATCH retains DEL -> ERA.CMD, DELQ -> ERAQ.CMD and RENAME -> REN.EXE.
It implements DIR, CLS, USER and the other supported TMP built-ins.
USER omits the redundant CP/M-media note and PAUSE uses
`Press any key to continue...`. DIR accepts native slash options and CP/M
brackets, including a final omitted ]. BATCH is not a full COMMAND.COM:
IF/GOTO/FOR/ECHO/SHIFT are not implemented.

`make check-batch-live` checks messages, CLS/DEL and an unrelated sentinel
on disposable CP/M images. `make check-dir-options` also executes a BAT
on CP/M media while DIR lists a FAT drive.

`make check-fat-batch` covers FAT-hosted scripts with four short-name case
flag combinations, CR/LF and Ctrl-Z endings, record padding, command-buffer
refills and execution of ERA.CMD from FAT. It checks deletion targets and an
unrelated sentinel. The original close-checksum failure was a FAT-to-FCB
attribute conversion bug in the kernel, corrected in `kernel/con/black.a86`;
see the root patch notes.
