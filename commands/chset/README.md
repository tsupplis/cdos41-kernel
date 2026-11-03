# CHSET

Native DR C/RASM86 utility for CMD header settings: 8087, SHARED, SUSPEND,
MPMLOCK and the local TAIL extension. The existing CHSET build is retained.

```
CHSET program.cmd
CHSET program.cmd [TAIL=KEEP]
CHSET program.cmd [TAIL=UPPER]
```

TAIL=KEEP sets bit 1 (02h) of header byte 7Fh. TAIL=UPPER clears it, retaining
the normal uppercase native command tail. The loader still parses filenames
and builds default FCBs normally; this setting only changes the tail delivered
to the program. Other header bits and directory attributes are unchanged.
Querying all fields includes TAIL; the settings buffer accommodates the extra
field. KEEP is a project extension and needs the patched native CLI. The stock
loader has no case-preservation control. See root `make check-cmdtail`.
