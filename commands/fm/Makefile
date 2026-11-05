# FM — staged DR C reconstruction; the distributed original stays in extra/.
# all builds core checks and experimental FMVIEW, not a replacement FM.CMD.
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
PYTHON=python3
REF=../../extra/fm.cmd
TOOLS=fmcheck.cmd fmview.cmd
OBJECTS=fmcheck.obj config.obj cfgio.obj menu.obj focus.obj select.obj selectio.obj marks.obj type.obj typeio.obj viewer.obj prtext.obj printjob.obj printio.obj renjob.obj renio.obj deljob.obj delio.obj copyjob.obj copyio.obj copynam.obj book.obj fatdest.obj fatloc.obj spawn.obj launch.obj runjob.obj extjob.obj screen.obj layout.obj frame.obj keys.obj navigate.obj dirlist.obj scan.obj native.obj browse.obj conio.obj event.obj term.obj fmxios.obj

.PHONY: all check check-c check-ref reference clean
.DELETE_ON_ERROR:
# DR C/LINK86 wrappers share scratch files, even for distinct object targets.
.NOTPARALLEL:

all: $(TOOLS)

fmcheck.cmd: $(OBJECTS) fmcheck.inp Makefile
	@$(DRCLINK86) 'fmcheck[input]' > fmcheck-link.log 2>&1; result=$$?; cat fmcheck-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' fmcheck-link.log
	$(CMDINFO) $@

fmview.cmd: fmview.obj $(filter-out fmcheck.obj,$(OBJECTS)) fmview.inp Makefile
	@$(DRCLINK86) 'fmview[input]' > fmview-link.log 2>&1; result=$$?; cat fmview-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' fmview-link.log
	$(CMDINFO) $@

%.obj: %.c fm.h menu.h screen.h layout.h frame.h keys.h navigate.h dirlist.h scan.h browse.h conio.h event.h term.h focus.h select.h marks.h type.h typeio.h viewer.h prtext.h printjob.h renjob.h renio.h deljob.h delio.h copyjob.h copyio.h copynam.h book.h fatdest.h Makefile
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
	$(PYTHON) -B tests/pce.py
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
	$(PYTHON) -B tests/delio.py
	$(PYTHON) -B tests/deljob.py
	$(PYTHON) -B tests/copyio.py
	$(PYTHON) -B tests/copyjob.py
	$(PYTHON) -B tests/copynam.py
	$(PYTHON) -B tests/fatdest.py
	$(PYTHON) -B tests/spawn.py
	$(PYTHON) -B tests/runjob.py
	$(PYTHON) -B tests/extjob.py
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
# .NOTPARALLEL serializes builds and live targets. After building, independent
# test scripts may be explicitly launched together on disposable machines.
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
	$(PYTHON) -B tests/rename_live.py --media fat --delete --boot-image ../../media/cdos86.img

check-live-rename-cpm: all
	$(PYTHON) -B tests/rename_live.py --media cpm --delete --boot-image ../../media/cdos86.img

.PHONY: check-live-copy-fat check-live-copy-cpm
check-live: check-live-copy-fat check-live-copy-cpm

check-live-copy-fat: all
	$(PYTHON) -B tests/copy_live.py --media fat --boot-image ../../media/cdos86.img

check-live-copy-cpm: all
	$(PYTHON) -B tests/copy_live.py --media cpm --boot-image ../../media/cdos86.img

.PHONY: check-live-copynam-fat check-live-copynam-cpm
check-live: check-live-copynam-fat check-live-copynam-cpm

check-live-copynam-fat: all
	$(PYTHON) -B tests/copynam_live.py --media fat --boot-image ../../media/cdos86.img

check-live-copynam-cpm: all
	$(PYTHON) -B tests/copynam_live.py --media cpm --boot-image ../../media/cdos86.img

.PHONY: check-live-fatdest
check-live: check-live-fatdest

check-live-fatdest: all
	$(PYTHON) -B tests/fatdest_live.py --boot-image ../../media/cdos86.img

.PHONY: check-live-book-fat check-live-book-cpm
check-live: check-live-book-fat check-live-book-cpm

check-live-book-fat: all
	$(PYTHON) -B tests/book_live.py --media fat --boot-image ../../media/cdos86.img

check-live-book-cpm: all
	$(PYTHON) -B tests/book_live.py --media cpm --boot-image ../../media/cdos86.img

.PHONY: check-live-run
check-live: check-live-run
check-live-run: all
	$(PYTHON) -B tests/run_live.py --boot-image ../../media/cdos86.img
