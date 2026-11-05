# FM — staged DR C reconstruction; the distributed original stays in extra/.
# all builds the configuration regression tool, not a replacement FM.CMD.
DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
PYTHON=python3
REF=../../extra/fm.cmd
TOOLS=fmcheck.cmd
OBJECTS=fmcheck.obj config.obj menu.obj screen.obj

.PHONY: all check check-c check-ref reference clean
.DELETE_ON_ERROR:

all: $(TOOLS)

fmcheck.cmd: $(OBJECTS) Makefile
	@$(DRCLINK86) fmcheck=fmcheck,config,menu,screen > fmcheck-link.log 2>&1; result=$$?; cat fmcheck-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' fmcheck-link.log
	$(CMDINFO) $@

%.obj: %.c fm.h menu.h screen.h Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]:])error([[:space:]:]|[0-9]|$$)|[1-9][0-9]* error\(s\) detected|fatal' $*.log
	@test -s $@

# Explicit regeneration keeps the reviewed reference listing under version control.
reference: disassemble.py symbols.json $(REF)
	$(PYTHON) -B disassemble.py

check-ref: fmorg.dis disassemble.py symbols.json $(REF)
	$(PYTHON) -B disassemble.py --check

check-c: all
	$(CC) -DHOST_TEST -std=c89 -Wno-deprecated-non-prototype config.c menu.c screen.c fmcheck.c -o fmcheck-host
	./fmcheck-host
	$(PYTHON) -B tests/config.py
	$(PYTHON) -B tests/menu.py
	$(PYTHON) -B tests/native.py

check: check-ref check-c

clean:
	$(RM) *.cmd *.obj *.h86 *.lst *.sym *.log *.lin *.prn *.mp? *.lnk *.map fmcheck-host
