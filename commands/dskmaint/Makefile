# DSKMAINT — Intel PL/M-86 / RASM86 / ASM86 / Intel ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

CMDINFO=cmdinfo
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86

TOOLS=dskmaint.cmd
OBJECTS=squiddm1.obj squiddm2.obj squiddm3.obj display.obj system.obj pccrt.obj screen.obj help1.obj help2.obj func10.obj

.PHONY: all check clean check-boot
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

# Assemble absolute groups for GENCMD.
%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com dosboot.raw dosboot.bin dskmaint.raw dskraw.inp

help1.obj: help1.a86 Makefile
	$(INTEL_ASM86) $<

# GENCMD supplies the CODE group header. Keep its temporary image distinct
# from runnable commands and extract the same 512 bytes the OEM SID step used.
dosboot.raw: dosboot.h86 Makefile
	$(GENCMD) $<
	mv dosboot.cmd $@

dosboot.bin: dosboot.raw Makefile
	python3 -c "from pathlib import Path; b=Path('$<').read_bytes(); assert b[0]==1 and int.from_bytes(b[1:3],'little')==32; Path('$@').write_bytes(b[128:640])"

# LINK86's input file avoids the 128-byte DOS command-tail limit.
dskraw.inp: dskmaint.in Makefile
	python3 -c "from pathlib import Path; p=Path('dskmaint.in').read_bytes(); assert p.startswith(b'dskmaint ='); Path('$@').write_bytes(p.replace(b'dskmaint =',b'dskraw =',1))"

dskmaint.raw: $(OBJECTS) dskraw.inp Makefile
	@$(LINK86) 'dskraw[input]' > dskmaint-link.log 2>&1; result=$$?; cat dskmaint-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal|NO FILE' dskmaint-link.log
	mv dskraw.cmd $@
	$(CMDINFO) $@

dskmaint.cmd: dskmaint.raw dosboot.bin embed_boot.py Makefile
	python3 embed_boot.py
	$(CMDINFO) $@

check: check-boot
check-boot: dskmaint.cmd
	python3 embed_boot.py --check
	python3 check_release.py
