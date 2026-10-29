# EDITMENU — DR C / RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=editmenu.cmd
OBJECTS=fdraw.obj iosubs.obj medattr.obj medfld.obj medmain.obj medscr.obj medscr1.obj medscr2.obj medscr3.obj medscr4.obj menuio.obj menusub.obj scrsubs.obj wmsubs.obj wwcallm.obj

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

editmenu.cmd: $(OBJECTS) Makefile editmenu.inp
	@$(DRCLINK86) 'editmenu[input]' > editmenu-link.log 2>&1; result=$$?; cat editmenu-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' editmenu-link.log
	@test -s $@
	$(CMDINFO) $@

# Preserve C symbol spelling, as requested by the original $nc option.
menuio.obj: menuio.a86 Makefile
	@$(RASM86) $< '$$nc' > menuio.log 2>&1; result=$$?; cat menuio.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' menuio.log
