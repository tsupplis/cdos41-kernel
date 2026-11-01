# N — local command build.
# all builds the declared tools; check validates them; clean removes generated files.
.PHONY: all check clean

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
RM=rm -f
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/n.cmd

TOOLS=n.cmd norg.cmd

all: $(TOOLS)

n.cmd: n.obj nsave.obj nvers.obj Makefile
	$(DRCLINK86) n=n,nsave,nvers
	$(CMDINFO) $@

nprobe.cmd: nprobe.obj Makefile
	$(DRCLINK86) nprobe=nprobe
	$(CMDINFO) $@

nkey.cmd: nkey.obj nsave.obj Makefile
	$(DRCLINK86) nkey=nkey,nsave
	$(CMDINFO) $@

norg.cmd: norg.h86 encodings.py Makefile
	$(GENCMD) $<
	$(PYTHON) encodings.py

nvers.obj: nvers.a86 Makefile
	$(RASM86) $<

# Recreate the complete release executable, including linker metadata.
norg.h86: norg.a86 Makefile
	$(ASM86) $<

%.obj: %.c Makefile $(wildcard *.h)
	$(DRC86) -o$@ $<

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.loc *.mp? *.lnk *.map

# Structural validation; byte comparisons or runtime checks are separate where available.
check: all
	@set -e; for file in $(TOOLS); do $(CMDINFO) $$file; done
	cmp norg.cmd $(REF)
