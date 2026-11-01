# RMDIR: 4.11 alignment

Built from the CDOS 4.1 OEM RMDIR, PATH and DERROR assembly modules.
`../../base/rmdir.cmd` is the independent 4.11 reference. The three 4.11 diagnostics are now ported.

## Recovered differences

| Area | OEM rebuild versus 4.11 |
| --- | --- |
| Main command and pathname handling | Same instructions after data-address relocation |
| Copyright and layout | Different text; entry shifts from 003Eh to 0030h in 4.11 |
| Final `.` or `..` in a path | 4.11 adds an explanation to the rejection message |
| Removal failure without extended error | 4.11 explains that files or floating drives may prevent removal |
| Extended error AH=03h | 4.11 reports a read-only subdirectory specifically; OEM falls back to “Can't change directory” |

The complete main/PATH region (OEM CODE:003Eh–044Eh, 4.11 CODE:0030h–0440h)
is identical apart from 35 relocated data-address operands. The DERROR
routine adds a ten-byte AH=03h branch selecting “Subdirectory set to Read
Only - Can't remove” (message number 9 rather than fallback 5).
The shared error mappings otherwise remain unchanged.

Command syntax and deletion rules are unchanged. No kernel changes are needed.

`make check` verifies the complete header/data and all executable code against
4.11, allowing only the exact longer OEM copyright header, entry displacement
and consequent 14-byte code relocation. Twelve original/rebuilt routine tests
exercise extended-error messages, including AH=03h. This does not claim live
coverage of every physical filesystem error.
