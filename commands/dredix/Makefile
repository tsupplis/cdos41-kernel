# DREDIX — local command build.
# all builds the declared tools; check validates them; clean removes generated files.
.PHONY: all check clean

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
RM=rm -f

TOOLS=dredix.cmd

all: $(TOOLS)

dredix.cmd: common.obj ebuf.obj ecmdblk.obj ecmdglb.obj ecmdio.obj ecmdsta.obj ed.obj ehelp.obj \
 ekey.obj elesson.obj emem.obj epat.obj ewdv.obj ewv.obj util.obj vd.obj vk.obj wmca.obj \
 wwcall.obj Makefile dredix.inp
	$(DRCLINK86) 'dredix[input]'
	$(CMDINFO) $@

util.obj: util.a86 Makefile
	$(RASM86) $<

wmca.obj: wmca.a86 Makefile
	$(RASM86) $<

wwcall.obj: wwcall.a86 Makefile
	$(RASM86) $<

%.obj: %.c Makefile $(wildcard *.h)
	$(DRC86) -o$@ $<

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.loc *.mp? *.lnk *.map

# Structural validation; byte comparisons or runtime checks are separate where available.
check: all
	@set -e; for file in $(TOOLS); do $(CMDINFO) $$file; done
