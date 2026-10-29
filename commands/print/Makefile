RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=print.cmd
MODULES=main sqprint cpmif cpyucase cpmerr crlf fileopen firstch getdrv getnum gettail issysfil itoa nextfcb okver parse putfname readsect reverse tlex valid
OBJECTS=$(addsuffix .obj,$(MODULES))
HEADERS=portab.h cpmfunc.h utildef.h

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)

print.cmd: $(OBJECTS) sqlink.inp Makefile
	@$(DRCLINK86) 'sqlink[input]' > print-link.log 2>&1; result=$$?; cat print-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' print-link.log
	@test -s $@
	cmdinfo $@

cpmif.obj: cpmif.a86
	@$(RASM86) $< > cpmif.log 2>&1; result=$$?; cat cpmif.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' cpmif.log

%.obj: %.c $(HEADERS)
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE 'error|unable to open|fatal' $*.log

clean:
	rm -f $(OBJECTS) print.cmd $(addsuffix .lst,$(MODULES)) $(addsuffix .sym,$(MODULES)) print.map print.sym *.log

check: all
	cmdinfo print.cmd
