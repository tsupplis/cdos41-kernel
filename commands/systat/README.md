# SYSTAT

Recompiled from CCP/M-86 3.1 and adapted for parity with the retained CDOS
SYSTAT. The OEM binary still contains its Concurrent CP/M-86 2.0 banner;
the review found no new report or command option requiring a logic rewrite.

Use bare SYSTAT for its menu, or `[H]` help, `[O]` overview, `[P]` all
processes, `[U]` user processes, `[Q]` queues, `[C]` consoles and `[M]`
memory. Add C and an optional one/two-digit hexadecimal interval for
continuous display, for example `SYSTAT [P C 01]`. A key stops it.

SYSTAT reads private SYSDAT/PD/CCB/queue/memory structures. Its old `sd.slr`
field is the shared-code list at 70h, called SCL by 4.1. It must not be
redirected to 4.1's unrelated synchronization-list root SLR at 96h. The
consumed field offsets and 2Ch console-block stride remain compatible.

The build now requests fixed DATA, matching the OEM allocation policy,
rather than an unnecessary extra allocation up to 64 KiB. All working arrays
are statically allocated. Literal includes and the Makefile are build
dependencies. The report algorithms and kernel are unchanged.

`make check-systat` exercises all seven reports, an invalid option and two
continuous displays under CDOS. OEM/rebuilt text is compared, with dynamic
memory-descriptor counts excluded. Memory display must contain both the
running SYSTAT and free partitions; its precise program footprint depends
on compiler/link layout. Shared-code entries and heavily populated tables
are not exhaustively exercised by this fixture.
