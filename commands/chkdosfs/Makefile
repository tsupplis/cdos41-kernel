# CHKDOSFS — reference analysis for the C recreation.
# No runnable replacement is built or distributed at this stage.
PYTHON ?= python3
REF=../../dosplus/chkdsk.cmd

.PHONY: all check check-ref clean
all: chkdosorg.dis

chkdosorg.dis: reference/chkdsk.cmd symbols.json disassemble.py Makefile
	$(PYTHON) disassemble.py

# Checks complete original-byte coverage, decoded branch boundaries and freshness.
# This is NOT an assembler round-trip or a functional parity check.
check: all check-ref
	$(PYTHON) disassemble.py --check

# Compare the frozen analysis input with the canonical DOS Plus original.
# A compiled reference does not exist yet; this is not check-asm.
check-ref: reference/chkdsk.cmd $(REF)
	cmp reference/chkdsk.cmd $(REF)

clean:
	rm -f *.obj *.cmd *.h86 *.sym *.lin *.lst *.prn *.log *.map
