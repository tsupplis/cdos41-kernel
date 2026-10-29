# DATETIME — RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
LINK86=pcdev_linkexe

TOOLS=date.exe time.exe
OBJECTS=pcdate.obj pctime.obj

.PHONY: all check clean check-date
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all
	@set -e; for f in $(TOOLS); do test -s $$f; done

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

date.exe: pcdate.obj Makefile
	@$(LINK86) 'date=pcdate[nop]' > date-link.log 2>&1; result=$$?; cat date-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' date-link.log
	@test -s $@
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a

# Exercise the linked DOS image with a synthetic clock interface.
check: check-date
check-date: date.exe tests/datecheck.asm ../../tools/date_check.py
	python3 ../../tools/date_check.py

time.exe: pctime.obj Makefile
	@$(LINK86) 'time=pctime[nop]' > time-link.log 2>&1; result=$$?; cat time-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' time-link.log
	@test -s $@
	@test "$$(od -An -tx1 -N2 $@ | tr -d ' \n')" = 4d5a

.PHONY: check-time
check: check-time
check-time: time.exe tests/timecheck.asm ../../tools/time_check.py
	python3 ../../tools/time_check.py
