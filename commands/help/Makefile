# HELP — Intel PL/M-86 / RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86

TOOLS=help.cmd
DATA=help.hlp
OBJECTS=scd3.obj help3.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS) $(DATA)
check: all
	@set -e; for f in $(TOOLS); do cmdinfo $$f; done

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

# Compile PL/M sources; declarations and Makefile changes trigger recompilation.
%.obj: %.plm Makefile $(wildcard *.lit *.ext)
	@$(INTEL_PLM86) $< debug 'optimize(3)' xref > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE '(^|[[:space:],])0 ERRORS' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f help.hlp *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

help.cmd: $(OBJECTS) Makefile
	@$(LINK86) 'help=scd3,help3[data[origin[0],max[0],add[200]]]' > help-link.log 2>&1; result=$$?; cat help-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' help-link.log
	@test -s $@
	cmdinfo $@

# Same native HELP [C] indexer and temporary-text workflow as CCP/M.
help.hlp: help.cmd help.dat Makefile
	@set -e; tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	cp help.cmd help.dat "$$tmp/"; \
	unix2dos "$$tmp/help.dat"; \
	(cd "$$tmp" && EMU2_CPM_VER=4.1 emu2 help.cmd '[C]'); \
	cp "$$tmp/help.hlp" $@
	@test -s $@
