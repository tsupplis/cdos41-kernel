# ECHO

`ECHO.CMD text` writes text to the native console followed by CR/LF. Dollar
signs are literal; leading spaces/tabs are skipped and an empty tail produces
a blank line. The command sets the project's KEEP_TAIL header flag to retain
case. PUT/RDR capture its native BDOS output, using the normal CP/M text
record padding (Ctrl-Z) rather than DOS byte-stream file lengths.

PCTMP and BATCH implement ECHO directly. Use an explicit `ECHO.CMD` name to
invoke the standalone command. It has no state controls: `ECHO.CMD ON` prints
ON. Only BATCH accepts `ECHO=ON/OFF` and `@ECHO`. The command uses the normal
native RASM86/LINKCMD build without a C or DOS runtime; no ECHO.EXE is built.

Run `make check` and root `make check-batch-language` for live verification.
