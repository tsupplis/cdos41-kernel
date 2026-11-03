# SETENV — DR C and RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
CMDMOD=cmdmod

TOOLS=setenv.cmd
OBJECTS=start.obj setenv.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all setenv.c setenv.h hostcheck.c
	$(CMDINFO) setenv.cmd
	@python3 -c "from pathlib import Path; assert Path('setenv.cmd').read_bytes()[127] & 2, 'Expected CMD TAIL=KEEP flag'"
	$(CC) -std=gnu89 -DHOST_TEST -Wno-deprecated-non-prototype setenv.c hostcheck.c -o hostcheck
	./hostcheck

setenv.cmd: $(OBJECTS) Makefile
	@$(DRCLINK86) 'setenv=start,setenv' > setenv-link.log 2>&1; result=$$?; cat setenv-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' setenv-link.log
	@test -s $@
	$(CMDMOD) -f 1=1 $@
	$(CMDINFO) $@

start.obj: start.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@

%.obj: %.c Makefile $(wildcard *.h)
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]:])error([[:space:]:]|[0-9]|$$)|[1-9][0-9]* error\(s\) detected|fatal' $*.log
	@test -s $@

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.mp? *.lnk *.map
	$(RM) *.exe hostcheck clears.l86
