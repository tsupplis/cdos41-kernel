# GENLDR — Intel PL/M-86 / RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86

TOOLS=genldr.cmd
OBJECTS=scd2.obj genldr.obj ldrbuf.obj genmsg.obj

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

# Compile PL/M sources; declarations and Makefile changes trigger recompilation.
%.obj: %.plm Makefile $(wildcard *.lit *.def *.equ *.lib *.h *.dcl *.inc *.ext)
	@$(INTEL_PLM86) $< debug 'optimize(3)' xref > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE '(^|[[:space:],])0 ERRORS' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

genldr.cmd: $(OBJECTS) Makefile
	@$(LINK86) 'genldr=scd2,genldr,ldrbuf,genmsg[dat[ori[0],add[400],max[0]]]' > genldr-link.log 2>&1; result=$$?; cat genldr-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' genldr-link.log
	$(CMDINFO) $@
