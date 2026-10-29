# LOADCCPM — ASM86 Intel HEX, then headerless GENCMD COM packaging.
# all builds local outputs; check validates them; clean removes generated files.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd

TOOLS=loadccpm.com

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all
	@set -e; for f in $(TOOLS); do test -s $$f; done

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

loadccpm.com: loadccpm.h86 Makefile
	$(GENCMD) $< nhead 8080 'code[b10]'
	mv loadccpm.cmd $@
	@python3 -c "from pathlib import Path; b=Path('$@').read_bytes(); assert b[0]==0xe9, 'Expected entry JMP at COM file offset zero'"
	@test -s $@

# LOADCCPM.SUB requests Intel HEX ($fi). GENCMD applies CODE[B10] to
# Intel address records; DRI type-81 records would retain a 256-byte gap.
loadccpm.h86: loadccpm.a86 Makefile
	@$(ASM86) $< '$$fi' > loadccpm.log 2>&1; result=$$?; cat loadccpm.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' loadccpm.log
