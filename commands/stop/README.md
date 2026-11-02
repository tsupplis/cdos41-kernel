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
The retained assembly reconstruction includes unused library procedures and a
reserved sequence of additions at their original offsets.

## PL/M reconstruction

[stop.plm](stop.plm) is reconstructed source, not recovered OEM source.
It builds the default, distributed `stop.cmd` using the shared 1984
[SCD3](../help/scd3.a86) startup and BDOS interface, matching the family used
by the release. Its snapshot record layouts and heading strings follow the
assembly reconstruction. The first 256 CODE bytes match the reference apart
from relocated addresses and the serial number. The compiled command is not
byte-identical: its CODE group is 2,144 bytes versus 3,600 in the release,
and its DATA group is 3,392 bytes versus 3,408.

[stoporg.a86](stoporg.a86) builds `stoporg.cmd`, which matches the complete
7,168-byte file from cdos-4.11-2.img. ASM86 chooses different encodings for
51 instructions; `encodings.py` checks and restores those same-length
encodings without moving offsets.

`make check` compares `stoporg.cmd` byte-for-byte with the release and runs
`check-plm`. The latter checks the startup and compares the release and
default PL/M binary with synthetic kernel lists and intercepted BDOS calls
under emu2. It checks exact reports, memory accounting, version checks, input
parsing, and P_ABORT parameters. This requires the Intel crossdev tools, NASM,
emu2 and Python 3.

`make check-live` compares the release and PL/M reports under Concurrent DOS
in PCE, including a command tail, an invalid entry and Return. It uses
temporary copies of the system disk and requires PCE, mtools, the system image
and its configured ROMs. Neither test stops a real process.

Two exceptional cases intentionally differ in the PL/M build:

- With no selectable processes, a positive entry reports "Entry number too
  large" instead of issuing the release's P_ABORT request with a zero PD.
- At the 65th displayed process, the release's snapshot overlaps the abort
  block and fills its termination word with the PD offset. The PL/M snapshot
  has enough space and sends a zero termination word instead.

Both differences are tested explicitly; `stoporg.cmd` retains the original
behavior.
