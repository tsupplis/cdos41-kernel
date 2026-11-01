# SETENV — local command build.
# all builds the declared tools; check validates them; clean removes generated files.
.PHONY: all check clean

RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=pcdev_linkexe
RM=rm -f

DRC_LIBDIR ?= $(dir $(shell command -v $(DRC86)))../share/drc86cpm
TOOLS=setenv.exe

all: $(TOOLS)

setenv.exe: start.obj setenv.obj clears.l86 Makefile
	$(DRCLINK86) 'setenv=start,setenv[nop]'
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a

start.obj: start.a86 Makefile
	$(RASM86) $<

# DR C emits a small-model initialization-library request even without libc.
# Stage it from the installed compiler, never from another project.
clears.l86:
	cp $(DRC_LIBDIR)/clears.l86 $@

%.obj: %.c Makefile $(wildcard *.h)
	$(DRC86) -o$@ $<

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.loc *.mp? *.lnk *.map
	$(RM) *.exe hostcheck clears.l86

check: all
	@test -s setenv.exe
	$${CC:-cc} -std=gnu89 -DHOST_TEST -Wno-deprecated-non-prototype setenv.c hostcheck.c -o hostcheck
	./hostcheck
