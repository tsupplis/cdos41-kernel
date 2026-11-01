# REDOS - assemble Intel HEX and package a flat DOS COM as in REDOS.SUB.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
REF=../../base/redos.com

.PHONY: all check clean
.DELETE_ON_ERROR:

all: redos.com

redos.h86: redos.a86 Makefile
	@$(ASM86) $< '$$fi' > redos.log 2>&1; result=$$?; cat redos.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' redos.log

redos.com: redos.h86 Makefile
	$(GENCMD) $< nhead 8080 'code[b10]'
	mv redos.cmd $@

check: all
	cmp redos.com $(REF)

clean:
	$(RM) redos.com redos.cmd redos.h86 redos.log redos.lst redos.sym
