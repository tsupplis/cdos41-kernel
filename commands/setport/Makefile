# SETPORT — annotated CDOS 4.1 assembly reconstruction.
# setporg.a86 is the frozen reference; setport.a86 is the maintained source.
# all builds both CMDs; check validates the complete files and encoding exceptions.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
CMDINFO=cmdinfo
PYTHON=python3

TOOLS=setport.cmd setporg.cmd
REF=../../base/setport.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)

# Generate absolute groups, compact GENCMD's empty EXTRA descriptor, and append
# the documented relocation record. No code/data payload is patched.
%.cmd: %.h86 Makefile header.py
	$(GENCMD) $<
	$(PYTHON) header.py $@
	$(CMDINFO) $@

%.h86: %.a86 Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

# Compare every byte, allowing only the 39 verified same-length instruction
# encodings in encodings.json. No ignored ranges and no instruction DBs.
check: $(TOOLS) check.py encodings.json
	$(PYTHON) check.py $(REF)

# Retain sources, the frozen invariant and documented original encodings.
clean:
	rm -f *.cmd *.h86 *.lst *.sym *.obj *.log
