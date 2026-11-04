# CHKDOSFS

FAT filesystem checker being recreated in C from Digital Research CHKDSK 1.0
(20-Mar-86), supplied with DOS Plus. The original explicitly accepts Concurrent
DOS as well as DOS Plus. The intended output is `CHKDOSFS.CMD`, complementing
`CHKCPMFS.CMD` for CP/M filesystems.

**Status: first-pass reference disassembly; no C replacement built yet.**
The original has not yet been exercised against this project's kernel.
Nothing from this directory is included in the distribution.

| File | Purpose |
|---|---|
| `reference/chkdsk.cmd` | Frozen analysis input, checked against `../../dosplus/chkdsk.cmd` |
| `chkdosorg.dis` | Complete annotated instruction/data listing with original byte columns |
| `symbols.json` | Routine names, global names, inline-data boundaries and review notes |
| `disassemble.py` | Reproducible listing and byte-coverage checks |
| `analysis.md` | Recovered interface, algorithm, kernel dependencies and C-port boundaries |

`make` generates the reference listing using NDISASM as a decoder. `make check`
compares the frozen input byte-for-byte with `../../dosplus/chkdsk.cmd`, then
checks its SHA-256, complete byte coverage and direct branch targets.
It does **not** establish assembler rebuild equivalence or functional parity.
There is no NASM production build and no disguised instruction byte arrays.

The C build will follow the DRI C / RASM-86 pattern of `commands/chset`.
The disassembly remains a reference, rather than a second maintained executable.
