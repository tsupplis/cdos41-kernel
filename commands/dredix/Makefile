# DREDIX — DR C / RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=dredix.cmd
OBJECTS=common.obj ebuf.obj ecmdblk.obj ecmdglb.obj ecmdio.obj ecmdsta.obj ed.obj ehelp.obj ekey.obj elesson.obj emem.obj epat.obj ewdv.obj ewv.obj util.obj vd.obj vk.obj wmca.obj wwcall.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all
	@set -e; for f in $(TOOLS); do $(CMDINFO) $$f; done

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

# Compile C modules with local declarations.
%.obj: %.c Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE 'error|unable to open|fatal' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

dredix.cmd: $(OBJECTS) Makefile dredix.inp
	@$(DRCLINK86) 'dredix[input]' > dredix-link.log 2>&1; result=$$?; cat dredix-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' dredix-link.log
	@test -s $@
	$(CMDINFO) $@
