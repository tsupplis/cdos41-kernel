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

The full reference is the 7,168-byte file from cdos-4.11-2.img. All executable
instructions are mnemonics in stop.a86. ASM86 chooses a different direction
encoding for some register MOV/XOR operations and the accumulator form for
two CMP instructions. encodings.py checks and restores exactly 51
same-length instruction encodings. No offsets move. Header, data, stack
reserve and file padding are included in the final `make check` comparison.
