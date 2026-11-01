# DOS COPY

Built from the CDOS 4.1 OEM PCCOPY.A86 source. The independent reference is
`../../base/copy.exe`, extracted from `cdos-4.11-1.img`; checksums are in
`../../base/cdos411.json`.

## 4.11 assessment: confirmed gap, not yet ported

Both executables are 29,184 bytes. Exactly 90 bytes differ:

| File offsets | Difference | Meaning |
| --- | --- | --- |
| 000Eh, 0012h | MZ SS/checksum | Original SS=06E6h, rebuild SS=06E8h; separate stack placement/header difference |
| 022Bh–022Eh, 0234h–023Ah | Serial-number text | Original serial versus source placeholder |
| 023Bh–0258h | Code patch area | 4.11 installs a backslash guard and relocated command-tail copy loop |
| 029Dh–02A1h | Original loop entry | 4.11 calls the guard, then jumps past the old loop |
| 0C30h–0C59h | Data patch area | Path-rejection diagnostic |

The code patch starts at CODE:003Bh. It scans the command tail before any
copy operation, preserves the existing plus-sign/concatenation handling,
and rejects a backslash in either source or destination. The diagnostic is
`To use a path, map to a floating drive.` It then enters the existing abort
path. Our source still has NOPs and placeholder text in the patch areas,
so it lacks this explicit rejection. This does not imply that the source
implements DOS pathname support.

An isolated assembled-code comparison tested both executables with plain
filenames, concatenation, a source path and a destination path. Only 4.11
rejected the two backslash cases. Output and abort calls were stubbed; no
files were copied or deleted. The two header differences and serial text
are distinct from this confirmed behavioral difference.

Next: port the guard as labelled, commented source; add permanent regression
coverage for ordinary names, concatenation and rejected paths; reassess the
remaining header differences. No production COPY code has been changed by
this assessment.
