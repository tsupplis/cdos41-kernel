# HELP database

`help.dat` is the maintained reference for commands packaged by this project
and the selected 4.1 PCTMP shell. It combines relevant original 4.1 material
from `base/help.hlp` with the maintained CCP/M import documentation and local
usability changes. The original binary database remains an archival reference;
all distribution disks now use the rebuilt `commands/help/help.hlp`.

The command catalogue distinguishes shell built-ins, aliases, external CMD
and DOS programs, and resident system services. Obsolete unavailable tools
are removed. Native 4.1 topics cover ORDER, COMSIZE, ADDMEM, 8087, SUSPEND,
directories, menus, backup/restore and the OEM utilities. Local topics retain
paging, password/media behavior, new console keys and window corrections.
Some guides are intentionally concise to fit the existing 320 KB tools disk;
the complete original operating reference remains in base/help.hlp.

`make check-help` validates topic coverage against media inputs and built-ins,
removed topics, every generated index pointer and the editor/data cleanup.
The native HELP indexer builds help.hlp from the saved CRLF source.
