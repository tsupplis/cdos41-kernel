# INITDIR — DR PL/I-86 / RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
PLI86=drplicpm_pc
PLILINK86=drplicpm_link
PLIOBJFIX=drpli_objfix

TOOLS=initdir.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)

# Build/header validation; the 3.1 media boot harness is not applicable here.
check: all
	cmdinfo $(TOOLS)

initdir.cmd: initdir.obj initdira.obj diomod.obj Makefile
	$(PLILINK86) initdir [locals],initdira,diomod
	cmdinfo $@

# Recompile after declarations or the object converter change. Old converted
# objects cannot recover the reserved DATA storage removed by a faulty tool.
initdir.obj: initdir.pli initdira.dcl diomod.dcl Makefile $(shell command -v $(PLIOBJFIX))
	$(PLI86) $< \$$dl
	$(PLIOBJFIX) $@

diomod.obj: diomod.a86 Makefile
	$(RASM86) $<

initdira.obj: initdira.a86 Makefile
	$(RASM86) $<

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn
	rm -f *.loc *.mp? *.lnk
