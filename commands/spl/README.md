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

Run `make check` to assemble SPL and compare the whole 12,160-byte CMD
against the retained copy from CDOS 4.11 disk 3. All instructions are ASM86
mnemonics. The packaging step restores the release DATA growth limit and
seven equivalent register MOV encodings selected differently by ASM86.
