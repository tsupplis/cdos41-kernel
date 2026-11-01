# PRINTMGR — local command build.
# all builds the declared tools; check validates them; clean removes generated files.
.PHONY: all check clean

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
RM=rm -f

TOOLS=printmgr.cmd

all: $(TOOLS)

printmgr.cmd: spool.obj spoolm.obj utlasm.obj sncheck.obj Makefile
	$(DRCLINK86) 'printmgr=spool,spoolm,utlasm,sncheck'
	$(CMDINFO) $@

utlasm.obj: utlasm.a86 Makefile
	$(RASM86) $<

%.obj: %.c Makefile $(wildcard *.h)
	$(DRC86) -o$@ $<

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.loc *.mp? *.lnk *.map

# Structural validation; byte comparisons or runtime checks are separate where available.
check: all
	@set -e; for file in $(TOOLS); do $(CMDINFO) $$file; done
