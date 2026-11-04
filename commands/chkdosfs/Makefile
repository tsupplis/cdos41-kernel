# CHKDOSFS — native DR C and RASM86 build.
# all builds CHKDOSFS.CMD; check validates it; clean removes generated outputs.
DRC86=drccpm_cc
RASM86=pcdev_rasm86
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
TOOLS=chkdosfs.cmd
OBJECTS=chkdosfs.obj fat.obj check.obj native.obj os.obj

.PHONY: all check check-c check-ref clean
.DELETE_ON_ERROR:
all: $(TOOLS)
check: all check-c check-ref
	$(CMDINFO) chkdosfs.cmd

chkdosfs.cmd: $(OBJECTS) Makefile
	@$(DRCLINK86) chkdosfs=chkdosfs,fat,check,native,os > chkdosfs-link.log 2>&1; result=$$?; cat chkdosfs-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' chkdosfs-link.log
	$(CMDINFO) $@

%.obj: %.c Makefile chkdosfs.h
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]:])error([[:space:]:]|[0-9]|$$)|[1-9][0-9]* error\(s\) detected|fatal' $*.log
	@test -s $@
%.obj: %.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@
clean:
	$(RM) *.cmd *.obj *.h86 *.hex *.lst *.sym *.log *.lin *.prn *.mp? *.lnk *.map

PYTHON=python3
REF=../../dosplus/chkdsk.cmd

check-c: all
	$(PYTHON) tests/check.py

# The frozen disassembly input remains byte-identical to the DOS Plus original.
# The C implementation is behavioural; no binary identity is claimed for it.
check-ref:
	cmp reference/chkdsk.cmd $(REF)
	$(PYTHON) disassemble.py --check
