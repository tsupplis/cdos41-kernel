# TYPE: Concurrent DOS compatibility

The retained `base/type.cmd` identifies itself as Concurrent 3.2 (1984).
The maintained version is recompiled from CCP/M-86 3.1 and adapted for
parity. The core parse/open/password/record-read logic is shared; startup,
compiler layout and OS-requirement messages differ. Byte identity is not a
goal. The older binary remains an executable reference for regression tests.

## Syntax and text handling

- `TYPE filespec` displays one file. Wildcards are rejected.
- `TYPE filespec;password` supplies the file password inline.
- `TYPE filespec [PNN]` selects 01..23 physical rows, using exactly two digits.
- `TYPE filespec [PAGE]` pauses after 23 physical rows, including tabs/wraps.
  The trailing option is case-insensitive. Ctrl-C at that prompt stops output.

Both versions stop text at the first Ctrl-Z, or when BDOS record reads end.
CR and LF are ordinary output bytes; the last line needs no newline. File
bytes pass through BDOS console output. CP/M files remain record-oriented:
without Ctrl-Z, the file's complete final 128-byte record is displayed.

The old program also displays the zero padding returned after the last byte
of a DOS file without Ctrl-Z. The adapted version recognizes BLACK's DOS FCB
flag bytes (16/17) after open and copies the exact 32-bit size from bytes
28..31. A local remaining-byte counter stops output at the actual DOS EOF.
Ctrl-Z still ends text earlier. This is an intentional correction, not a
change to CP/M record semantics. Tests include an unaligned 65537-byte file.

## Password and open behavior

Both versions parse the file with BDOS 152, request read-only access with the
same FCB flag and interpret open errors the same way. Missing passwords
(error 7) prompt once, uppercase typed characters, support Backspace,
Ctrl-X and Ctrl-C, then retry the open once. A second incorrect password
ends the command rather than beginning another prompt cycle.

Both deliberately omit an explicit file close, matching the historical TYPE
source's warning about that path. Kernel process termination releases the
file. No new password or open-error policy is introduced.

## Paging differences

`[PAGE]` uses 23 physical rows; `[PNN]` selects 01..23, with exactly two
digits. Both count tabs and wrapping, use `Press any key to continue...`,
and read a non-echoing key through BDOS 6/FDh. Ctrl-C stops output; EOF at an
exact page boundary needs no key. Options are trailing and case-insensitive.

The old binary's unbracketed P/PNN counted linefeeds and silently read a key.
Those forms are deliberately rejected now. `[P]`, `[P00]`, `[P24]`, `[P99]`,
`[P1]`, malformed options and extra arguments are invalid. Use `[P10]`, for
example, for ten-row pages. These syntax/display changes are intentional.

## Verification

`make check-type` boots disposable CP/M/FAT12 floppies under PCE and compares
both commands via RDR captures. It covers empty files, CR-only/LF-only and
unterminated lines, embedded Ctrl-Z, control bytes, record boundaries, missing
files, wildcards, directory-open errors, inline passwords, rejection of old paging syntax,
PAGE/wrapping/exact page boundaries/Ctrl-C, and the DOS 16-bit size boundary.
Protected-file fixtures use SET on a disposable CP/M disk to enable password
protection and check correct/incorrect passwords and editing keys.

DOS byte-length EOF and bracketed paging are intentional differences.
Explicit nested DOS paths and concurrent modification of a displayed file
are not covered by this regression.
