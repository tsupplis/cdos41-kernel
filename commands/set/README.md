# SET

Recompiled from CCP/M-86 3.1 and adapted for parity with the retained
Concurrent SET 3.1 (07/09/84). The imported source identifies itself as
SET 2.1 (02/15/83); the maintained build identifies itself as SET 3.1N.
This is a source adaptation, not a byte-identical reproduction.

## Command line

```
SET filespec [RO|RW,DIR|SYS,ARCHIVE=ON|OFF,F1=ON|OFF,...,F4=ON|OFF]
SET filespec[;password] [PASSWORD=newpassword,PROTECT=READ|WRITE|DELETE|NONE]
SET d: [RO|RW]
SET d: [NAME=label.typ]
SET d: [PROTECT=ON|OFF]
SET d: [PASSWORD=password]
SET d: [DEFAULT=password]
SET d: [CREATE=ON|OFF,ACCESS=ON|OFF,UPDATE=ON|OFF]
SET [HELP]
```

Drive prefixes are optional. Commas separate options; the existing parser
also accepts its historical abbreviated keywords and multiple references.
A bare filespec or drive is not a query: SET requires an option. SHOW and
SDIR provide inspection. Use `[PASSWORD=,PROTECT=OFF]` to remove a label
password and disable drive protection, or file `[PASSWORD=,PROTECT=NONE]`
to remove a file password/protection. The historical parser requires a comma
after the empty password; `[PASSWORD=]` alone is rejected by both builds. Enable drive password protection before
assigning file/label passwords or setting a default password.

READ protects reading, writing, renaming and deletion. WRITE protects
writing, renaming and deletion. DELETE protects renaming and deletion.
The default password is copied back to the calling process, so subsequent
commands can use it. Interactive password input supports Backspace, Ctrl-X
and Ctrl-C, retaining the historical non-echoing behavior.

File attributes work through BDOS on CP/M and DOS media, including DOS
directory entries. DOS attribute translation is provided by the 4.1 kernel;
CP/M F1-F4 flags are not four additional independent FAT attribute bits.
CP/M ARCHIVE=ON means already archived, so it clears DOS's archive-needed
bit; ARCHIVE=OFF sets that bit. This matches the OEM and kernel mapping.
Labels, XFCB passwords and timestamp configuration require CP/M media.
Creation and access timestamps are mutually exclusive; enabling either
replaces the other, but requesting both together is rejected. Timestamp
activation requires an INITDIR-formatted directory.

## Differences from the imported source

The confirmed functional delta is SET 3.1's media protection. Its binary
probes BLACK's DOS pseudo-label and rejects CP/M-only operations before
reading/modifying a label or writing a label/XFCB. The source now performs
those same three checks, using a private mutable FCB and buffer and restoring
the previous DMA offset. Previously a DOS pseudo-label could cause an
irrelevant password prompt and an INITDIR error.

The option/message tables otherwise closely match. The larger version number
does not imply an entirely new command implementation. Binary inspection
also confirms the parent process offset (1Eh), UDA pointer (10h) and default
password offset (12h) used by the imported source. No kernel layout changes
are needed. Compiler/startup differences account for part of the binary delta.

The help database previously advertised `[MAKE]` and `PROTECTION=EDIT`.
Neither is supported here or by the OEM SET 3.1: those entries are removed;
DELETE is the supported protection mode. Archive and F1-F4 are documented.

## Verification

`make check-set` runs the OEM and rebuilt executables on separate identical
CP/M/FAT12 disk pairs under PCE. The test uses direct console snapshots and
checks return to the shell after each command. It compares attributes,
wildcards, DOS directory handling, media guards, labels, all four password
protection modes, malformed options and drive RO/RW transitions.

Additional runs exercise formatted-directory creation/access/update flags
and interactive password retry, Backspace, Ctrl-X, Ctrl-C, label-password
removal and default-password inheritance by a subsequent TYPE command.
Final CP/M directory records and FAT attributes are checked independently of
SET's printed messages and compared between the two builds. Only software
version identifiers and label timestamps are excluded from those comparisons.

This coverage does not establish exhaustive parity for nested DOS paths,
network drives, disk-full/write failures or concurrent directory changes.
The retained `base/set.cmd` remains the regression reference.

OEM SET 3.1 SHA-256: `e4ec4cdefafe7cd1793c3bc2fbbe5429046e87df8fd53ca720d72c5633616123`.
