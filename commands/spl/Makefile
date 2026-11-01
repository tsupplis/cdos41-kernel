# SPL - assemble the labelled 8086 source and restore the release encodings.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/spl.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: spl.cmd

spl.h86: spl.a86 Makefile
	@$(ASM86) $< > spl.log 2>&1; result=$$?; cat spl.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' spl.log

spl.cmd: spl.h86 Makefile encodings.py
	$(GENCMD) $<
	$(PYTHON) encodings.py

check: all
	cmp spl.cmd $(REF)

clean:
	$(RM) spl.cmd spl.h86 spl.log spl.lst spl.sym
