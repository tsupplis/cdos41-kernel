# SETENV — DR C / RASM86, linked as DOS EXE with a PSP-aware startup.
# all builds local outputs; check validates editing; clean removes generated files.
DRC86=drccpm_cc
RASM86=pcdev_rasm86
LINK86=pcdev_linkexe
DRC_LIBDIR ?= $(dir $(shell command -v $(DRC86)))../share/drc86cpm
TOOLS=setenv.exe
OBJECTS=start.obj setenv.obj

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)

setenv.exe: $(OBJECTS) clears.l86 Makefile
	@$(LINK86) 'setenv=start,setenv[nop]' > setenv-link.log 2>&1; result=$$?; cat setenv-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' setenv-link.log
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a

%.obj: %.c setenv.h Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -iE 'error|unable to open' $*.log

%.obj: %.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qE 'Number of errors: +0\.' $*.log

check: all
	@test -s setenv.exe
	$${CC:-cc} -std=gnu89 -DHOST_TEST -Wno-deprecated-non-prototype setenv.c hostcheck.c -o hostcheck
	./hostcheck

clean:
	$(RM) *.cmd *.exe *.obj hostcheck *.lst *.sym *.map *.log clears.l86

# DR C emits a small-model initialization-library request even without libc.
# Stage it from the installed compiler, never from another project.
clears.l86:
	cp $(DRC_LIBDIR)/clears.l86 $@
