# BOOT — ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

PYTHON ?= python3
ASM86 = cpm86_asm86
H862BIN = h862bin

.PHONY: all check clean
.DELETE_ON_ERROR:

all: boottrack.bin

# Assemble absolute groups for GENCMD.
%.h86: %.a86 Makefile
	$(ASM86) $<

%.bin: %.h86 Makefile
	$(H862BIN) $< $@

# The working 320 KB disk's reserved track, built entirely from source:
# E5 filler, boot code at 000h, sides marker at 1FFh, loader at 900h.
boottrack.bin: bootsect.bin loader.bin Makefile
	@test "$$(wc -c < bootsect.bin)" -eq 147
	@test "$$(wc -c < loader.bin)" -eq 846
	$(PYTHON) -c "import sys; sys.stdout.buffer.write(b'\xe5' * 4096)" > $@.tmp
	dd if=bootsect.bin of=$@.tmp bs=1 seek=0 conv=notrunc 2>/dev/null
	printf '\001' | dd of=$@.tmp bs=1 seek=511 conv=notrunc 2>/dev/null
	dd if=loader.bin of=$@.tmp bs=1 seek=2304 conv=notrunc 2>/dev/null
	mv $@.tmp $@

# Verify the source-built track without requiring a binary template.
check: boottrack.bin
	@$(PYTHON) -c "from pathlib import Path; expected=bytearray(b'\xe5'*4096); expected[:147]=Path('bootsect.bin').read_bytes(); expected[511]=1; expected[2304:3150]=Path('loader.bin').read_bytes(); assert Path('boottrack.bin').read_bytes()==expected"
	@echo 'Boot track: layout, both stages, sides marker and filler verified'

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) *.bin *.h86 *.sym *.lst boottrack.bin.tmp
