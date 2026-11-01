# HDMAINT — RASM86 / ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.
# The recovered flat LBDOS and loader bundle rebuild the OEM command.

CMDINFO=cmdinfo
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd

TOOLS=hdmaint.cmd
OBJECTS=lbdos3.obj
IMAGES=pcboot1.h86 cpmboot2.h86 cpmboot3.h86 hsetup.h86 label.h86 pcboot2.h86 pcboot3.h86

.PHONY: all check clean check-fat
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all check-fat
	@set -e; for f in $(TOOLS); do $(CMDINFO) $$f; done
	cmp hdmaint.cmd ../../base/hdmaint.cmd
	@python3 -c "from pathlib import Path; assert sorted(p.name for p in Path('.').glob('*.cmd')) == ['hdmaint.cmd'], 'Partial CMD artifact left in HDMAINT build'"

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

# Assemble absolute groups for GENCMD.
%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com *.bin *.raw

# Recreate the original SID loader insertion with checked boundaries.
# GENCMD/LINK86 force .CMD filenames; rename them within each recipe.
# Headerless loader fragments use .bin; the unfilled command uses .raw.
LOADERS=pcboot1.bin cpmboot2.bin hsetup.bin label.bin cpmlod.bin pcboot2.bin pcboot3.bin
hdmaint.cmd: h70.raw $(LOADERS) rebuild.py
	python3 rebuild.py assemble
	$(CMDINFO) $@

pcboot1.bin cpmboot2.bin hsetup.bin label.bin cpmlod.bin: %.bin: %.h86 Makefile
	$(GENCMD) $< 8080 nhead
	mv $*.cmd $@

pcboot2.bin: pcboot2.h86 Makefile
	$(GENCMD) $< nhead 'code[b7c0]'
	mv pcboot2.cmd $@

cpmlod.h86: lbdos.h86 cpmboot3.h86 rebuild.py
	python3 rebuild.py merge

h70.raw: h70.h86 Makefile
	$(GENCMD) $< 'data[m800]' 'extra[m800]'
	mv h70.cmd $@
	$(CMDINFO) $@

lbdos3.raw: lbdos3.obj Makefile
	@$(LINK86) 'lbdos3=lbdos3[data[ori[0],max[0]]]' > lbdos3-link.log 2>&1; result=$$?; cat lbdos3-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' lbdos3-link.log
	mv lbdos3.cmd $@
	$(CMDINFO) $@

# Verify the FAT stage independently against the OEM DRIBIO reference.
pcboot3.bin: pcboot3.h86 Makefile
	$(GENCMD) $< nhead 8080
	mv pcboot3.cmd $@

check-fat: pcboot3.bin
	python3 check_fat.py
