# REN

Recompiled from CCP/M-86 3.1 and adapted for parity with the retained
CDOS `base/ren.cmd`. No rename algorithm change was needed.

```
REN destination=source[;password]
REN B:*.BAK=B:*.DAT
```

Existing destinations prompt for deletion with Y/N. Wildcards are processed
file by file. Incorrect passwords prompt for another password; Ctrl-C
cancels. Source and destination must belong to the same drive. Like the OEM
native REN, this command rejects DOS directory renames. The shell's RENAME
alias uses the separate DOS REN.EXE; that executable is outside this review.

`make check-ren` compares 12 cases on separate identical CP/M/FAT fixtures:
invalid input, ordinary rename, overwrite refusal/acceptance, wildcards,
directory/cross-drive rejection, inline passwords, retry and cancellation.
It checks names, attributes, sizes and fixture contents on disk, retaining
an unrelated sentinel. Allocation-cluster positions are excluded because the
two executable builds occupy different amounts of disk space.

UDA search fields remain at offsets 07h/08h/0Ch in 4.1. The Makefile now
tracks literal-include dependencies. No kernel change is required.
