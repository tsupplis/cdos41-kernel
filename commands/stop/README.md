# STOP.CMD

Running `STOP` at the shell invokes STOP.CMD. It lists processes and memory
usage, then asks for an entry number. Return exits. A positive entry number
selects the recorded process for BDOS P_ABORT. The row marked ** is entry zero.
Calling the external program explicitly with a nonempty command tail displays
the report and exits. The shell's `STOP name window` is a separate TMP command.

STOP snapshots free memory, shared code and the process thread list while
interrupts are disabled. It merges adjoining free memory extents, records
program names and console numbers, then enables interrupts before displaying
the report. Its abort request uses the selected PD offset, console and name.
The retained binary includes unused library procedures and a reserved sequence
of additions. They are kept at their original offsets.

The default `stop.cmd` is reconstructed assembly, not recovered OEM source.
It matches the complete 7,168-byte file from cdos-4.11-2.img. ASM86 chooses
different encodings for 51 instructions; encodings.py checks and restores
those same-length encodings without moving offsets.

## PL/M reconstruction

`stop_plm.plm` is a separate, reconstructed PL/M implementation, not the
original source. It reuses SYSTAT's `scd.a86` startup and BDOS interface.
`make stop_plm.cmd` builds this alternative; it is not byte-identical and is
not the default or the version packaged in the distribution.

`make check` verifies the default file byte-for-byte and runs `check-plm`.
The latter compares the release and PL/M binaries with synthetic kernel
lists and intercepted BDOS calls under emu2. It checks exact reports,
memory accounting, version checks, input parsing, and P_ABORT parameters.
No actual process is stopped. This requires the Intel crossdev tools, NASM,
emu2 and Python 3; it is not a live Concurrent DOS system test.

Two exceptional cases intentionally differ in the PL/M alternative:

- With no selectable processes, a positive entry reports "Entry number too
  large" instead of issuing the release's P_ABORT request with a zero PD.
- At the 65th displayed process, the release's snapshot overlaps the abort
  block and fills its termination word with the PD offset. The PL/M snapshot
  has enough space and sends a zero termination word instead.

Both differences are tested explicitly; the default release-equivalent
binary retains the original behavior.
