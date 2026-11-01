# INITDIR

Built from the CDOS 4.1 OEM PL/I sources. The independent release reference
is `../../base/initdir.cmd`, extracted from `cdos-4.11-4.img`; image and
file checksums are recorded in `../../base/cdos411.json`.

## 4.11 assessment

Closed: no command-logic change is needed. All 36,992 bytes match except
file offsets 8A55h–8A56h: the original contains 0000h and our PL/I runtime
contains FFFFh. This is DATA:3C25h, the runtime stack-limit word, not code.

Entry at CODE:0005h calls runtime initialization at 1EB8h. On first entry,
the runtime computes DATA:3C32h + 0400h and writes DATA:3C25h at CODE:1EEBh,
then installs SS:SP and returns to INITDIR. The alternate allocation-error
path terminates startup. The initial 0000h/FFFFh value therefore does not
change the command's normal execution. The read at CODE:2608h belongs to
runtime stack-space accounting, after initialization.

`make check` pins the reference checksum and compares the complete file,
allowing only these two exact values at that word. It also verifies the
entry and initialization instructions supporting the exception. No bytes
are patched or broad ranges ignored. This is binary/runtime equivalence
validation, not a fresh destructive disk-stamping test.
