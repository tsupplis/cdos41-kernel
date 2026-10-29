# Initial Concurrent DOS 4.1 media

`make` packages two physical-CHS 320 KB floppy images using local build
outputs. Build from the project root first; media rules package artifacts.

- `cdos86.img`: CCPM.SYS, a minimal comment-only STARTUP.0, BATCH.CMD and
  the 4.1 PIP build installed as PIP.CMD.
- `cdostools.img`: ASM86, GENCMD, SUBMIT, GENCCPM, BATCH and PIP; no kernel.

The filesystem is generated with mkfs.cpm; no binary base disk or sibling
project is read. `diskdefs` matches the SQUID double-sided 320 KB DPB.
The unchanged local cpm86twist.py handles reversed head-1 track numbering.

`make check` extracts and compares the packaged kernel/tools, and verifies
both complete reserved tracks against the source-built boot track.

`make test` launches PCE through `./cdos86`, using `cdos86.cfg`, matching
CCP/M's media launcher pattern. Drive A: is cdos86.img and B: is cdostools.img.
The default adapter is VGA; `./cdos86 cga` selects the CGA profile. CPU,
ROM search path, terminal options and locking follow the CCP/M template;
only the media names and two-drive selection differ. PCE and its ROMs are
installed runtime prerequisites, not inputs from the sibling project.

The initial image has been reported booting by the user. Build/media checks
pass; the QEMU VGA profile is not an automated boot-validation target.
HDMAINT is not required for this floppy boot and remains pending.

The packaging follows the CCP/M project's sequence: `base.img` is the empty
filesystem template in physical CHS order; `cdos86base.img` installs the
source-built reserved track; each final image is untwisted, populated, and
twisted back. Here `base.img` is generated locally rather than checked in.
Both base images are generated artifacts removed by `make clean`.
