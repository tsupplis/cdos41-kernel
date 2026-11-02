# SETENV — DR C and RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=pcdev_linkexe
LINK86=$(DRCLINK86)

DRC_LIBDIR ?= $(dir $(shell command -v $(DRC86)))../share/drc86cpm
TOOLS=setenv.exe
OBJECTS=start.obj setenv.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all setenv.c setenv.h hostcheck.c
	@for f in $(TOOLS); do test -s "$$f" || { echo "error: $$f is missing or empty" >&2; exit 1; }; done
	$(CC) -std=gnu89 -DHOST_TEST -Wno-deprecated-non-prototype setenv.c hostcheck.c -o hostcheck
	./hostcheck

setenv.exe: $(OBJECTS) clears.l86 Makefile
	@$(LINK86) 'setenv=start,setenv[nop]' > setenv-link.log 2>&1; result=$$?; cat setenv-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' setenv-link.log
	@test -s $@
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a

start.obj: start.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@

# DR C emits a small-model initialization-library request even without libc.
# Stage it from the installed compiler, never from another project.
clears.l86: $(DRC_LIBDIR)/clears.l86
	cp -f "$<" "$@"

%.obj: %.c Makefile $(wildcard *.h)
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]:])error([[:space:]:]|[0-9]|$$)|[1-9][0-9]* error\(s\) detected|fatal' $*.log
	@test -s $@

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.mp? *.lnk *.map
	$(RM) *.exe hostcheck clears.l86
