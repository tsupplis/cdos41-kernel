# Concurrent DOS 4.1 system generation

`make` stages the seven CON components and PIN, CLOCK, PCTMP and CONFID in
a fresh temporary directory, then runs the locally rebuilt GENCCPM 4.1.
Only a completed output becomes CCPM.SYS; unrelated RSPs cannot leak in.
The response file sets system/temp drives to A:, disables command logging,
uses the initial memory partition list and places the kernel at 6000h.
This leaves room for this larger 4.1 kernel below the 640 KB boundary.

`diskbuffers` uses the wildcard profile: four directory buffers and two
data buffers per configurable drive, with per-process limits of four and
two. The wildcard dialog asks the hashing question even though the SQUID
DPHs have fixed hash information. This differs from the 3.1 response file.
The OS label is PC-MODE Personality. GENCCPM's transcript is sysgen.log.

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
