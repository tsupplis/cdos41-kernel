# FM — staged DR C reconstruction; the distributed original stays in extra/.
# all builds core checks and experimental FMVIEW, not a replacement FM.CMD.
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
PYTHON=python3
REF=../../extra/fm.cmd
TOOLS=fmcheck.cmd fmview.cmd
OBJECTS=fmcheck.obj config.obj cfgio.obj menu.obj focus.obj select.obj selectio.obj marks.obj type.obj typeio.obj viewer.obj prtext.obj printjob.obj printio.obj renjob.obj renio.obj screen.obj layout.obj frame.obj keys.obj navigate.obj dirlist.obj scan.obj native.obj browse.obj conio.obj event.obj term.obj fmxios.obj

.PHONY: all check check-c check-ref reference clean
.DELETE_ON_ERROR:

all: $(TOOLS)

fmcheck.cmd: $(OBJECTS) fmcheck.inp Makefile
	@$(DRCLINK86) 'fmcheck[input]' > fmcheck-link.log 2>&1; result=$$?; cat fmcheck-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' fmcheck-link.log
	$(CMDINFO) $@

fmview.cmd: fmview.obj $(filter-out fmcheck.obj,$(OBJECTS)) fmview.inp Makefile
	@$(DRCLINK86) 'fmview[input]' > fmview-link.log 2>&1; result=$$?; cat fmview-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' fmview-link.log
	$(CMDINFO) $@

%.obj: %.c fm.h menu.h screen.h layout.h frame.h keys.h navigate.h dirlist.h scan.h browse.h conio.h event.h term.h focus.h select.h marks.h type.h typeio.h viewer.h prtext.h printjob.h renjob.h renio.h Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]:])error([[:space:]:]|[0-9]|$$)|[1-9][0-9]* error\(s\) detected|fatal' $*.log
	@test -s $@

%.obj: %.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@

# Explicit regeneration keeps the reviewed reference listing under version control.
reference: disassemble.py symbols.json $(REF)
	$(PYTHON) -B disassemble.py

check-ref: fmorg.dis disassemble.py symbols.json $(REF)
	$(PYTHON) -B disassemble.py --check

check-c: all
	$(CC) -DHOST_TEST -std=c89 -Wno-deprecated-non-prototype config.c menu.c screen.c layout.c frame.c keys.c navigate.c dirlist.c scan.c browse.c conio.c event.c fmcheck.c -o fmcheck-host
	./fmcheck-host
	$(PYTHON) -B tests/config.py
	$(PYTHON) -B tests/cfgio.py
	$(PYTHON) -B tests/menu.py
	$(PYTHON) -B tests/focus.py
	$(PYTHON) -B tests/selection.py
	$(PYTHON) -B tests/marks.py
	$(PYTHON) -B tests/pickers.py
	$(PYTHON) -B tests/type.py
	$(PYTHON) -B tests/viewer.py
	$(PYTHON) -B tests/prtext.py
	$(PYTHON) -B tests/printjob.py
	$(PYTHON) -B tests/renio.py
	$(PYTHON) -B tests/renjob.py
	$(PYTHON) -B tests/layout.py
	$(PYTHON) -B tests/frame.py
	$(PYTHON) -B tests/keys.py
	$(PYTHON) -B tests/navigate.py
	$(PYTHON) -B tests/directory.py
	$(PYTHON) -B tests/scan.py
	$(PYTHON) -B tests/enter.py
	$(PYTHON) -B tests/browse.py
	$(PYTHON) -B tests/conio.py
	$(PYTHON) -B tests/term.py
	$(PYTHON) -B tests/native.py

check: check-ref check-c

clean:
	$(RM) *.cmd *.obj *.h86 *.lst *.sym *.log *.lin *.prn *.mp? *.lnk *.map fmcheck-host preview.svg

.PHONY: preview
preview:
	$(PYTHON) -B tests/preview.py

.PHONY: check-live check-live-default check-live-release check-live-custom check-live-users
# Build first, then use make -j4 check-live for independent disposable machines.
check-live: check-live-default check-live-release check-live-custom check-live-users

check-live-default: all
	$(PYTHON) -B tests/live.py

check-live-release: all
	$(PYTHON) -B tests/live.py --config release

check-live-custom: all
	$(PYTHON) -B tests/live.py --config custom --selection --type --print

check-live-users: all
	$(PYTHON) -B tests/users.py

.PHONY: check-live-rename-fat check-live-rename-cpm
check-live: check-live-rename-fat check-live-rename-cpm

check-live-rename-fat: all
	$(PYTHON) -B tests/rename_live.py --media fat --boot-image ../../media/cdos86.img

check-live-rename-cpm: all
	$(PYTHON) -B tests/rename_live.py --media cpm --boot-image ../../media/cdos86.img
