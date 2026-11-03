# SYSDISK

`SYSDISK`, `SYSDISK d:`, `SYSDISK path`, and `SYSDISK [ON]`/`[OFF]`
control the console's native system search path. SYSDISK is an external
command, not a TMP or BATCH built-in. Its command file must be available
on the search path or invoked with an explicit drive.

The existing OEM SD-mode D.A86 implementation and Makefile are retained
unchanged. `SYSDISK.CMD` is distributed only on the maintenance disk.
PATH remains a separate TMP/BATCH built-in for the DOS environment.
