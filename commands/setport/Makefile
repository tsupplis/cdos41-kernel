# SETPORT — annotated CDOS 4.1 assembly reconstruction.
# setporg.a86 is the frozen reference; setport.a86 is the maintained source.
# all builds both CMDs; check validates the complete files and encoding exceptions.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
CMDINFO=cmdinfo
PYTHON=python3

TOOLS=setport.cmd setporg.cmd
REF=../../base/setport.cmd
HELP_DIR=../function/shared
HELP_SHARED=$(addprefix $(HELP_DIR)/,helpcode.lib helpdata.lib helpwork.lib)

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)

# Generate absolute groups, compact GENCMD's empty EXTRA descriptor, and append
# the documented relocation record. No code/data payload is patched.
%.cmd: %.h86 Makefile header.py
	$(GENCMD) $<
	$(PYTHON) header.py $@
	$(CMDINFO) $@

setport.h86: $(HELP_SHARED)

%.h86: %.a86 Makefile
	@EMU2_DRIVE_E="$(abspath $(HELP_DIR))" $(ASM86) $< > $*.log 2>&1; \
	  result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log
	@test -s $@

# Compare every byte, allowing only the 39 verified same-length instruction
# encodings in encodings.json. No ignored ranges and no instruction DBs.
check: $(TOOLS) check.py tests/test_check.py encodings.json $(REF)
	$(PYTHON) check.py $(REF)
	$(PYTHON) -B -m unittest discover -s tests -p 'test_check.py'

# Retain sources, the frozen invariant and documented original encodings.
clean:
	rm -f *.cmd *.h86 *.lst *.sym *.obj *.log
