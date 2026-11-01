# N - interactive national setup in DR C and its frozen ASM86 reference.
DRC86=drccpm_cc
LINK86=drccpm_link
RASM86=pcdev_rasm86
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/n.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:
all: n.cmd norg.cmd

# Link the maintained program and the optional read-only and save probes.
n.cmd: INPUT=n=n,nsave,nvers
nprobe.cmd: INPUT=nprobe=nprobe
nkey.cmd: INPUT=nkey=nkey,nsave
n.cmd: n.obj nsave.obj nvers.obj Makefile
nprobe.cmd: nprobe.obj Makefile
nkey.cmd: nkey.obj nsave.obj Makefile
n.cmd nprobe.cmd nkey.cmd:
	@$(LINK86) '$(INPUT)' > $(basename $@)-link.log 2>&1; result=$$?; cat $(basename $@)-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' $(basename $@)-link.log

%.obj: %.c Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE 'error|unable to open|fatal' $*.log

nvers.obj: nvers.a86 Makefile
	@$(RASM86) $< > nvers.log 2>&1; result=$$?; cat nvers.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' nvers.log

# Recreate the complete release executable, including linker metadata.
norg.h86: norg.a86 Makefile
	@$(ASM86) $< > norg.log 2>&1; result=$$?; cat norg.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' norg.log

norg.cmd: norg.h86 encodings.py Makefile
	$(GENCMD) $<
	$(PYTHON) encodings.py

check: all
	cmp norg.cmd $(REF)
	cmdinfo n.cmd

clean:
	$(RM) *.obj *.cmd *.h86 *.log *.lst *.sym
