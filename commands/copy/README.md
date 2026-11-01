# DOS COPY

Recompiled from CDOS 4.1 OEM PCCOPY.A86 and adapted for parity with 4.11.
The independent reference is `../../base/copy.exe`, extracted from
`cdos-4.11-1.img`; its checksum is pinned by `check.py`.

## 4.11 alignment

The recovered, labelled command-tail routine in the original patch area
rejects a backslash in either source or destination before copying files.
It prints `To use a path, map to a floating drive.` and exits directly through
CCPRET. It deliberately does not call ABORT, which deletes a temporary file.
Plain names, drive prefixes and plus-sign concatenation retain their behavior.
Like 4.11, the routine scans the complete 128-byte tail buffer.

The code begins at CODE:003Bh; the old loop entry at CODE:009Dh calls it.
The message occupies DATA:0000h. Remaining patch reserves and the unreachable
old loop instructions are retained to preserve the historical layout.
Instructions are written as assembly, with data declarations only for data.

## Verification

`make check` builds COPY and compares the complete 29,184-byte executable
against the pinned 4.11 reference. All code and data match except source serial
text. The only other permitted differences are LINK86's exact stack placement
(SS=06E8h instead of 06E6h) and recalculated MZ checksum. Both 128-byte stacks
fit inside the checked zero-filled reserve. No arbitrary byte masks are used.

Eighteen isolated original/rebuilt routine tests cover empty and ordinary
tails, concatenation, floating-drive names, /V, and source/destination paths.
They check the prepared tail, concatenation flag, rejection and direct exit,
and reject accidental use of file-deleting cleanup. Output and exit are
stubbed; these tests do not perform filesystem copies. The disposable test
driver uses NASM/emu2; production COPY continues to use RASM86/LINK86.
