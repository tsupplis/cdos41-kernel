# PATH — RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
LINK86=pcdev_linkexe
PYTHON=python3

TOOLS=path.exe
OBJECTS=pathx.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all check.py ../../base/path.exe
	@for f in $(TOOLS); do test -s "$$f" || { echo "error: $$f is missing or empty" >&2; exit 1; }; done
	$(PYTHON) check.py

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	$(RM) *.mp? *.lnk *.map *.exe *.com

path.exe: $(OBJECTS) Makefile
	@$(LINK86) 'path=pathx' > path-link.log 2>&1; result=$$?; cat path-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' path-link.log
	@test -s $@
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a
