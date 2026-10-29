# DOS REN

Reverse engineered from CDOS 4.1 `base/ren.exe`, with byte-for-byte identity.
The RASM86/LINK86 source layout and Makefile follow ERASE and PATH.
This directory produces DOS `REN.EXE`; `../ren` remains the native `REN.CMD`.

## Command line

```
REN [drive:]oldname[.ext] newname[.ext]
```

Source comes first, unlike native REN's `new=old` syntax. The command uses
native BDOS F_PARSE (152) for 8.3 names and DOS FCB rename (17h), including
the parser's wildcard handling. It does not implement DOS pathname rename
(56h). Missing/blank operands, parser errors, invalid drives and failed
rename have their original messages. The original separator table and
unused uppercase helper remain documented in the source.

## Exact reconstruction

`pcren.a86` labels every routine, branch, message and buffer. Executable
instructions are mnemonics, including the 69 NOPs in the patch reserve.
DB is used only for data. No instruction encoding exceptions are required.
The 280 executable bytes at code offsets 0080h–0197h match directly.

The single MZ relocation is the DATA segment immediate at code offset 0081h.
The entry is CS:0080h; DATA begins at paragraph 001Ah. DATA occupies 0239h
bytes and the 128-byte stack starts at paragraph 003Eh with SP=0080h.
The first byte of the data patch reserve is already zero in the OEM file.
All those details, the original serial string and zero padding are retained.

Current LINK86 places the stack at 0040h and computes a new checksum.
`header.py` verifies its output shape/checksum, then restores **only** the
OEM SS and checksum words. The OEM checksum 4ED3h is stale (whole-file word
sum 7727h); it is preserved for identity. No code/data bytes are patched,
and the build never reads the reference executable.

`make check` checks the complete 2048-byte file against a pinned SHA-256 and
`base/ren.exe`, including header, relocation, data and padding. The reference
is required only for verification. `make clean` removes generated outputs.
