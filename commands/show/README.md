# SHOW: Concurrent DOS compatibility

Recompiled from CCP/M-86 3.1 and adapted for parity with the retained OEM
`base/show.cmd`. The reference utility reports SHOW 3.3 (12/10/84), with a
Concurrent 3.2 startup header. The imported source's SHOW 2.1 identifier is
retained in invalid-option output; this is the documented cosmetic difference.
The original binary is used as a regression oracle, not as a build input.

## Syntax and options

`SHOW {d:}{option}` accepts SPACE, DRIVE/DRIVES, USERS, LABEL and HELP.
Options can be combined; bracketed forms such as `SHOW [SPACE]` are accepted.
The historical parser dispatches on the first letter. Any L-prefixed token
therefore selects LABEL, including LOCKED; this does not implement a locked
record report. OPEN is rejected, matching 3.3, rather than printing the old
source's placeholder message.

| Option | Meaning |
| --- | --- |
| SPACE or no option | Logged drives' RO/RW status and free space in kilobytes |
| DRIVE / DRIVES | BDOS drive characteristics, including record capacity and block/directory geometry |
| USERS | Current CP/M user and file counts by active user |
| LABEL | CP/M directory label, password/stamping flags and label timestamps |
| HELP | Display the supported option list |

SPACE and DRIVE support both CP/M and DOS media. USERS and LABEL require
CP/M media; DOS disks print `This command/option requires CP/M media.`
Default SPACE listings omit N:/O:/P:, matching the OEM command. An explicitly
selected drive remains available to the original dispatch rules.

## Parity changes

- A private search buffer detects BLACK's translated DOS pseudo-label
  (20h at byte 0, 80h at byte 15). The previous DMA offset is restored.
  This prevents DOS directory entries being interpreted as CP/M users/labels.
- Implicit SPACE output matches 3.3's A:..M: drive limit.
- OPEN's inactive placeholder is removed; all L-prefixed tokens follow the
  OEM LABEL dispatch. No new OPEN/LOCKED reporting feature is claimed.
- The creation-stamping flag comes from label bit 10h, matching 3.3,
  rather than an uninitialized local variable. Access stamping uses bit 40h.

The imported DPB pointer and date handling are retained. Drive geometry is
the BDOS view, including its DOS virtual DPB, rather than a raw FAT BPB dump.
Free space uses BDOS 46's three-byte record count. Existing year formatting
handles labels dated 2000 and 2026 in the regression fixtures.

## Verification

`make check-show` runs the OEM and rebuilt commands under PCE on disposable
CP/M/FAT12 images. It checks option/default/bracketed/multiple-command forms,
DOS rejection for USERS/LABEL, explicit/default drive selection, CP/M user
counts, label presence/absence, create/access stamping and dates across 2000. CP/M free space is
calculated independently from allocation entries; FAT free space is calculated
from FAT12 entries. Captures create one-cluster logs, which are accounted for
rather than treated as a reporting difference. Drive capacities and ordinary
output are compared directly; only software identifiers and changing capture
space are normalized.

Read-only output formatting follows the original code, but this regression
does not yet force a disk into read-only mode. Very large virtual DPBs and
concurrent changes to the filesystem are outside its current coverage.
