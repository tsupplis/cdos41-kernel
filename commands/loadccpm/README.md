# LOADCCPM

DOS-hosted loader for CCPM.SYS, rebuilt from OEM assembly and aligned with
4.11. `make check` pins the independent reference hash and compares every
byte of the 1,536-byte COM file. Production tools remain ASM86/GENCMD.

## Interface

`LOADCCPM` loads CCPM.SYS from the root of the current DOS drive.
`LOADCCPM ASK` asks for confirmation first. These forms are unchanged.
The 4.11 prompt identifies support for standard fixed disks, and the loader
prints “Loading Concurrent PC DOS .....” before loading.

## Recovered 4.11 differences

Besides release identification and messages, the vector-restoration routine
copies 62 words instead of 64: INT 00h through 1Eh are restored, preserving
INT 1Fh. On AT machines it leaves the existing INT 41h hard-disk parameter
table offset intact instead of forcing E411h. The original AT segment write
and ROM checks remain as in 4.11. These are hardware-related changes, not
new command-line options.

The rebuilt file is now byte-identical, including both vector changes and
padding. This proves release equivalence; it is not a new claim that the
historical ROM-dependent loader supports arbitrary BIOS implementations.
