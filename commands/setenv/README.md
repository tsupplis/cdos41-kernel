# SETENV

New DOS EXE for Concurrent DOS, built with DR C and RASM86. Its Makefile
uses the existing compiler and DOS LINK86 wrappers. The small-model compiler
initialization library is staged from the installed toolchain, not another
project; DRC_LIBDIR can override that location.

```
SETENV
SETENV NAME
SETENV NAME=value
SETENV NAME=
SETENV /?
```

List all variables, display one, add/replace, or delete respectively. Names
are case-insensitive and stored uppercase; values retain case and spaces.
No percent-variable expansion or quoting language is added. The command tail
limits one assignment to 127 characters. Changes affect the calling console's
DOS environment and persist until reboot. They are not saved to disk.

The kernel reserves 1024 bytes per PCTMP, 896 more than the original 128.
COMSPEC, PATH and OS defaults remain unchanged. PATH.EXE and DOS programs use
this same environment through PSP:002Ch. Native CMD command tails are
uppercased by the shell, so this command is
an EXE to retain mixed-case values. Its startup saves the DOS PSP and reads
the environment segment at PSP:002Ch. It verifies the complete PATH-style
`Environ Size =` header before accessing the block, accepting capacities from
2 to 1024 bytes. It works with the original 128-byte block within that limit.

Edits are assembled in a separate buffer. Invalid blocks and insufficient
space cause no writes. This is a per-console shared environment, not a private
copy for each program. Concurrent writers on the same console are not locked.

`make check` builds the DOS command and tests addition, case-insensitive
replacement/deletion, exact-fit capacity, overflow and malformed blocks with
the host compiler. Root `make check-setenv` runs the emulator test for the PSP bridge,
mixed-case persistence, deletion, more than 128 bytes and DOS PATH interoperability.
