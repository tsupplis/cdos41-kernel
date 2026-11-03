# DFORM — CDOS native floppy formatter.
# all builds the declared tools; check validates them; clean removes generated files.

CMDINFO=cmdinfo
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
H862BIN=h862bin
BIN2ASM=bin2asm

TOOLS=dform.cmd
INCS=bootsect.inc loader.inc fatboot.inc
.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS) fatboot.bin
bootsect.inc loader.inc: %.inc: ../../boot/%.bin
	$(BIN2ASM) -m -f $@ $<
	unix2dos $@
../../boot/%.bin: ../../boot/%.a86
	$(MAKE) -C ../../boot $*.bin

%.h86: %.a86 Makefile
	unix2dos $<
	rm -f $@
	$(ASM86) $*
	@test -f $@

%.bin: %.h86
	$(H862BIN) $< $@

# bin2asm is already provided on PATH; labels belong to the including file.
%.inc: %.bin
	$(BIN2ASM) -m -f $@ $<
	unix2dos $@

dform.obj: dform.a86 ccpmio.a86 fat360.a86 $(INCS) Makefile
	unix2dos $<
	rm -f $@
	@$(RASM86) $< $$ pz sz > dform.log 2>&1; cat dform.log
	@grep -qE 'Number of errors: +0\.' dform.log || { rm -f $@; exit 1; }
dform.cmd: dform.obj Makefile
	$(LINK86) dform '[$$sz,cod[ori[0]],dat[ori[0],max[0]]]'
	@python3 -c "from pathlib import Path; p=Path('$@'); b=bytearray(p.read_bytes()); n=int.from_bytes(b[1:3],'little'); k=n-1024; assert k>0 and not any(b[128+16*k:128+16*n]); b[1:3]=k.to_bytes(2,'little'); p.write_bytes(b[:128+16*k])"
	$(CMDINFO) $@

check: all
	$(CMDINFO) dform.cmd
	@test "$$(wc -c < fatboot.bin)" -eq 512
clean:
	$(RM) *.cmd *.obj *.log *.bin *.inc *.sym *.lst *.h86
