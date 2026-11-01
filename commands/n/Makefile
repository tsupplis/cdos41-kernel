# N - assemble the labelled 8086 source and restore the release encodings.
DRC86=drccpm_cc
LINK86=drccpm_link
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/n.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: n.cmd

n.h86: n.a86 Makefile
	@$(ASM86) $< > n.log 2>&1; result=$$?; cat n.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' n.log

n.cmd: n.h86 Makefile encodings.py
	$(GENCMD) $<
	$(PYTHON) encodings.py

check: all
	cmp n.cmd $(REF)

clean:
	$(RM) nkey.obj nkey.cmd nkey.log nkey-link.log nkey.sym nprobe.obj nprobe.cmd nprobe.log nprobe-link.log probe-link.log nprobe.sym n.cmd n.h86 n.log n.lst n.sym

# Optional read-only C probe. The distribution continues to build n.cmd.
nprobe.obj nkey.obj: %.obj: %.c Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE 'error|unable to open|fatal' $*.log

nprobe.cmd nkey.cmd: %.cmd: %.obj Makefile
	@$(LINK86) $*=$* > $*-link.log 2>&1; result=$$?; cat $*-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' $*-link.log
