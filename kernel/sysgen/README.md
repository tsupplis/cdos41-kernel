# Concurrent DOS 4.1 system generation

`make` stages the seven CON components and PIN, CLOCK, PCTMP and CONFID in
a fresh temporary directory, then runs the locally rebuilt GENCCPM 4.1.
Only a completed output becomes CCPM.SYS; unrelated RSPs cannot leak in.
The response file sets system/temp drives to A:, disables command logging,
uses the initial memory partition list and places the kernel at 6000h.
This leaves room for this larger 4.1 kernel below the 640 KB boundary.

`diskbuffers` creates one shared pool: 16 directory buffers and eight data
buffers, with per-process limits of four and two. A: owns the pool; the
wildcard assigns all other configurable drives to share A:'s buffers.
GENCCPM reads numbers in hexadecimal, so the response writes `10` for sixteen.
The explicit A: dialog skips hashing because SQUID fixes that field; the
wildcard still asks it. The final `no` answers that wildcard question.
The OS label is Enhanced Capability. GENCCPM's transcript is sysgen.log.

`make check` validates the fixed-address CODE/DATA headers and the system
memory boundary. The DATA file group contains separately segmented RSPs
and can exceed 64 KB; the older 3.1 check imposing a 64 KB group limit is
not applicable here. Live boot validation belongs to the media check.

GENCCPM applies the existing CCP/M workaround for DRC 1.11's `char = -1`
miscompilation. It emits each RTM flag as FF FF FF and uses literal FF for
true byte settings. The old output was 00 FF FF, an invalid waiter pointer.
`tools/sysgen_check.py` rejects that table before accepting CCPM.SYS and
also checks the resident-process chain and conventional-memory bounds.
Original/current hashes for these source changes are retained in sources.json.

## Console allocation and footprint

The default kernel has four PC virtual consoles (0..3), four PCTMP instances
and one PIN instance. `kernel/con/consoles.def` supplies the shared XIOS/CIO
counts. Two serial UART AUX/printer ports remain available. Serial-terminal
consoles are a separate allocation: set `num_serial_cons` to 2 to restore the
OEM terminal profile (PCTMP0..5 and PIN0..2), then rebuild the kernel and media.
The supported settings are 0 and 2; the default is 0.

CIO reserves one 256-byte recall slot per configured console, rather than
sixteen slots for the entire console-number range. With current sources the
standard four-console SYS with shared buffers is 168,064 bytes, down from
197,120 bytes: 29,056 bytes recovered. Console/recall allocation accounts for
18,304 bytes; replacing nine private disk-buffer pools with the shared pool
recovers another 10,752 stored bytes, plus runtime data-buffer memory.
CONFIDD is still included; its optional-driver footprint is a separate review.

`tools/console_footprint_check.py`, included in root `make check`, checks the
assembled XIOS counts, UART AUX allocation, generated resident-process copies,
recall storage and all 256 byte console IDs against the production selector.
Eight assembled UART-startup cases also cover present/missing ports and
requested terminal modes, checking that ordinary AUX ports remain available.
It also rejects separate per-drive buffer pools or incorrect pool counts
and process limits. The reviewed standard SYS file budget is 166 KiB
(182 KiB with two serial
terminals). A future budget increase requires reviewing and documenting its
resident cost. File bytes and the runtime memory boundary are distinct:
GENCCPM also reserves XIOS disk buffers beyond the stored SYS image.

## Adjusting the shared buffer pool

The default 16 directory/eight data buffers doubles the original 4.11 shared
pool (eight/four), providing headroom for four active PC consoles. Edit the
four numeric lines following `diskbuffers` and `a:` in `genccpm.in`:

| Setting | Response value | Decimal value |
| --- | --- | --- |
| Total shared directory buffers | `10` | 16 |
| Maximum directory buffers per process | `4` | 4 |
| Total shared data buffers | `8` | 8 |
| Maximum data buffers per process | `2` | 2 |

All four numbers are hexadecimal: `10` means sixteen and `20` means thirty-two.
Keep each process maximum between one and its pool total. Leave the following
`*:` / `a:` / `a:` / `no` lines intact: they make the remaining drives share
A:'s pool instead of allocating another pool per drive. Drive letters are
pool references here, not a limit on the number of usable drives.

Rebuild with root `make`, then run `make check`. The footprint check reads the
selected pool counts and limits from this response file and verifies the
actual DPH/BCB chains. Directory buffers increase both stored SYS size and
resident memory; data-buffer contents are reserved at runtime, outside the
stored image. If a deliberate increase exceeds the reviewed SYS size budget,
review the resulting footprint and update the budget in
`tools/console_footprint_check.py` and this document together.
