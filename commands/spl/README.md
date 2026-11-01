# SPL.CMD

SPL is the spool queue server. PRINTMGR starts the requested DSP workers
and chains to SPL. SPL detaches its console and waits for messages. Its
C runtime accepts a command tail, but the server has no option parser.

MXSPL serializes client transactions. SPLIN carries requests and SPLOUT
returns replies. The 160-byte message has a 32-byte header and 128 bytes
of data. The server maintains eight submission records, sixteen despooler
records and a four-byte entry for each job number. INDEX.DSP holds saved
job information used during recovery and dispatch.

| Request byte (hex) | Operation |
| --- | --- |
| 00 | Start a job |
| 01 | Append data |
| 02 | Abort a job |
| 03 | Report status |
| 07 | Finish submission |
| 0A | Terminate the spooler |
| 10, 11 | Process a despooler event or status report |

The release binary contains the Digital Research C 1.11 small-model runtime.
The OEM SPOOL.C and SPOOLM.C are the PRINTMGR client sources. Its SPLDEF.H
and the DSP sources identify the message fields and request numbers used in
this disassembly. The CODE patch area containing A–D records and the XDOS
wrappers correspond to UTLASM.A86.

Run `make check-asm` to assemble [splorg.a86](splorg.a86) into `splorg.cmd`
and compare the whole 12,160-byte CMD
against the retained copy from CDOS 4.11 disk 3. All instructions are ASM86
mnemonics. The packaging step restores the release DATA growth limit and
seven equivalent register MOV encodings selected differently by ASM86.

## Reconstructed C server

[splc.c](splc.c) is a behavioral reconstruction, not recovered original source.
It uses Digital Research C **1.11**, K&R declarations, unsigned bytes and
16-bit words. [splc.h](splc.h) mirrors the relevant layouts from the surviving
DSP/PRINTMGR SPLDEF.H. Startup verifies all eight wire/disk structure sizes.
The build reuses DSP's UTLASM assembly interfaces and the installed C runtime.

The reconstructed C server is the default build and distribution payload:

```sh
make            # DRC 1.11 + RASM86 + LINK86 -> splc.cmd -> spl.cmd
make check      # C behavior checks, deployed-binary identity and ASM86 reference
make check-asm  # separate byte-identical assembly reconstruction -> splorg.cmd
make cbuild     # build the C intermediate splc.cmd only
make check-c     # paired machine-code behavioral tests under emu2
make check-live  # paired PRINTMGR/DSP workflows under CDOS in PCE
```

`all` and distribution images use the C-built `spl.cmd`; the assembly reference
build never writes that filename. The C command does not need encoding patches and is not expected to
match the original bytes. Its DATA allocation is capped at 5 KB, including
stack space, rather than the linker's default 64 KB.

| C routines | Assembly behavior |
| --- | --- |
| `splinit`, `readyin` | Queue setup, INDEX.DSP creation/recovery, stable priority insertion |
| `spstart`, `spdata`, `spfinish` | Eight concurrent submissions, record buffering, ready-job creation |
| `spabort`, `spstatus` | Submission/queued/active cancellation and saved-job enumeration |
| `spevent`, `spreport`, `spsched` | DSP completion/status messages and device dispatch |
| `spsend`, `spstop` | Stale-reply retry/drain and preserve/delete shutdown |

Compatibility details retained include the 254 job numbers plus sentinel,
A-P filename digits, one-way APPEND, six reply attempts before draining stale
SPLOUT data, 64-byte index halves, partial-close FCB flags, and final-record
byte counts without tail padding. Historical disk-error handling is retained:
full-record write errors set flag 2, while a failed final partial-record write
does not change FINISH's result. This reconstruction does not silently repair
that release behavior.

Defined deviations are bounds checks for malformed job/device requests and
diagnostics for invalid one-way messages, invalid ready/saved-device state,
incompatible layouts, and index create/open failures. The assembly's
out-of-bounds memory accesses are not reproduced.

### Validation

[tests/check.py](tests/check.py) loads the retained release and default `spl.cmd`,
including
their startup runtimes, into [the emu2 harness](tests/splcheck.asm). It compares
queue payloads, spool-record writes, index writes, deletions and retry delays.
Twenty paired scenarios cover submission, defaults, length clamping, capacity,
priority/FIFO scheduling, two devices, cancellation, DSP reports, recovery,
job-number wrap, truncated indexes, shutdown and injected errors.
Additional C-only cases check malformed-message guards. This requires Python 3,
NASM and emu2; no Python packages are needed.

[tests/live.py](tests/live.py) additionally compares eleven screens from real
PRINTMGR/DSP startup, submission, status, reset, restart and termination in PCE.
It requires the normal built system components, GENCCPM, PRINTMGR, DSP, the
system image, PCE/ROMs, mtools and cpmtools. All disk writes are to temporary
copies; printer output uses the existing null-device emulator configuration.

The default system image's 1 KB queue pool cannot start even the original SPL
in this workflow. The live test therefore generates a disposable system with
`qbufsize=800` (hex: 2 KB) and `nqcbs=20` (hex: 32). It validates that system
before booting it and does not change the repository's system configuration
or distribution images. Synthetic tests are not a substitute for testing real
printer hardware or every possible BDOS failure.
