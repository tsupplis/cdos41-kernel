# DOS REN — RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
LINK86=pcdev_linkexe

PYTHON=python3

TOOLS=ren.exe
OBJECTS=pcren.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all check.py
	$(PYTHON) check.py
	cmp ren.exe ../../base/ren.exe

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

# Restore only the documented OEM MZ SS/checksum words; code/data are untouched.
ren.exe: $(OBJECTS) Makefile header.py
	@$(LINK86) 'ren=pcren[nop]' > ren-link.log 2>&1; result=$$?; cat ren-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' ren-link.log
	@test -s $@
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a
	$(PYTHON) header.py
