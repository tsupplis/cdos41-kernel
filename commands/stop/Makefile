# STOP - assemble the labelled 8086 source and restore the release encodings.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/stop.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: stop.cmd

stop.h86: stop.a86 Makefile
	@$(ASM86) $< > stop.log 2>&1; result=$$?; cat stop.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' stop.log

stop.cmd: stop.h86 Makefile encodings.py
	$(GENCMD) $<
	$(PYTHON) encodings.py

check: all
	cmp stop.cmd $(REF)

clean:
	$(RM) stop.cmd stop.h86 stop.log stop.lst stop.sym
