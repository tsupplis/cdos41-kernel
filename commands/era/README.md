# ERA and ERAQ

Both native commands build here with the local 4.1 SCD3 startup and shared
4.1 COPYRIGHT/VERMPM/VAXCMD includes. ERAQ.PLM is the unchanged OEM 4.1 source,
relocated from commands/eraq. ERA.PLM is the CCP/M source with only its public
PL/M entry renamed from PLM$START to PLM to match SCD3.

Comparing the CCP/M 3.1 and OEM 4.1 ERAQ sources found no query, directory-search,
password or delete algorithm changes. The executable source changes are entry
naming and whitespace. Shared includes update the copyright year and required-OS
wording; the minimum BDOS remains 30h. ERA receives those same build conventions.
Its per-file fallback still uses UDA searchl at 07h and dcnt at 0Ch, matching
the initial saved BDOS fields in this 4.1 kernel.

ERAQ keeps per-file confirmation; ERA keeps its wildcard/all-files confirmation
and existing error handling. No behavioral rewrite is inferred from the version
number. The ERA import review is recorded below.

## Import review

ERA's executable source tokens match the CCP/M 3.1 source after entry-name,
include-path, comment and whitespace normalization. Applying the same
normalization to CCP/M ERAQ and CDOS ERAQ also finds no algorithm changes.
The existing 4.1 startup/includes therefore complete ERA's alignment; no
functional patch is needed. ERAQ remains the unchanged native CDOS source.

The light ERA check also passed eight OEM/rebuilt command cases on disposable
CP/M/FAT media, including wildcard deletion, passwords, retry, missing files
and preservation of unrelated files. `make check-era` repeats these checks.
