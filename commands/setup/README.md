# SETUP.CMD

SETUP customizes the IBM PC/XT XIOS. Run it from a local console. F1 opens
the current topic in HELP.HLP. Escape at the main menu exits. F10 opens the
update menu, where F3 selects a drive and F5 writes its CCPM.SYS. The new
settings take effect when that system next boots.

| Main menu key | Setting |
| --- | --- |
| F3 | Save current programmable function keys or serial settings |
| F4 | MDisk size and starting segment |
| F5 | Diskette head step time |
| F6 | Verify after diskette writes |
| F7 | Serial port assignment to printer or terminal |
| F8 | Maximum memory per process, 064–999 KiB |
| F9 | Color monitor scroll mode |

The command-tail table recognizes `/PARAM`, `/MDISK`, `/HEAD`, `/VERIFY`,
`/SERIAL` and `/MEMORY` to enter their menus directly. `/PFKSAVE` and
`/PORTSAV` preselect the corresponding save flag and enter the main menu.
The comparison uses the supplied tail length and uppercase bytes. A prefix
selects the first matching entry. An unmatched tail falls through to the
main menu.

## Relationship to CCP/M SETUP

The two programs share the function-key menu design, MDisk arithmetic,
diskette timing and verification logic, and console drawing routines.
The CCP/M version updates a configuration sector. CDOS opens CCPM.SYS,
uses its header to locate the configuration, checks the 16-byte
`Setup Buffer ==>` signature, then replaces the 512-byte configuration
block. The CDOS program also has serial-console assignment, a per-process
memory limit, scroll modes and a linked HELP reader. The utility displays
version 4.1 on the 4.11 release disk.

## Rebuilding the release

`setup.a86` is the maintained disassembly and `setuporg.a86` is the frozen
reconstruction. Run `make check` to assemble both with ASM86 and compare
each complete CMD against the reference from CDOS 4.11 disk 2 (16,256 bytes).
The maintained source shares its reconstructed HELP code, initialized data
and workspace with SETPORT in `../function/shared/`. The Makefile maps that
directory to the assembler's E: drive. These shared files are not a compiled
copy of the archived HELP PL/M source.

CODE contains SETUP through 0A94h and embedded HELP from 0AA0h. The nine
menu dispatch tables are symbolic words. Two instructions at 0202h and
0207h have an explicit 2Eh CS prefix followed by a mnemonic MOV. Combining
the override and MOV in ASM86 selects a longer displacement. In HELP,
ASM86 selects 39 equivalent encodings. Each is annotated in the source.
`pack.py` checks and restores those encodings, restores the linker's DATA
maximum, compacts the group descriptors and emits the two CODE-to-DATA
relocations at 0B03h and 0B10h. The build reads the reference only for
the final comparison.
