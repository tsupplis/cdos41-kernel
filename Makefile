# Concurrent DOS 4.1 — local commands, kernel, boot track and disk distribution.
# all builds media; check verifies outputs; dist packages the disk images.

DISKSZIP=disks.zip
DIST_DISKS=cdos86.img cdostools.img cdosmaint.img cdosmenu.img cdosdos.img cdosoem1.img cdosoem2.img

.PHONY: all commands kernel boot media check check-pce test clean xios-alt check-aliases dist check-dist check-redirection check-sdir check-type check-show check-set check-wmenu check-era check-ren check-systat check-window check-help check-dir-options check-batch-live check-help-live check-fat-batch check-fat-case check-rtc
.DELETE_ON_ERROR:

all: media
commands:
	$(MAKE) -C commands all

kernel: commands
	$(MAKE) -C kernel all

boot:
	$(MAKE) -C boot all

media: kernel boot
	$(MAKE) -C media all

xios-alt:
	$(MAKE) -C kernel xios-alt

check: all
	@set -e; for f in kernel/con/*.con kernel/rsp?/*.rsp; do cmdinfo $$f; done
	$(MAKE) -C commands check
	$(MAKE) -C kernel/sysgen check
	$(MAKE) -C kernel/con check-cursor check-rtc
	$(MAKE) -C boot check
	$(MAKE) -C media check

check-pce: all
	$(MAKE) -C media check-pce

test: all
	$(MAKE) -C media test
# Remove generated outputs only; preserve sources and reference files.
clean:
	$(MAKE) -C commands clean
	$(MAKE) -C kernel clean
	$(MAKE) -C kernel/xios clean
	$(MAKE) -C boot clean
	$(MAKE) -C media clean
	$(RM) $(DISKSZIP) $(DIST_DISKS)

check-aliases: all
	python3 tools/alias_check.py

# Re-enter after recursive builds, as in CCP/M, to refresh image timestamps.
dist: all
	$(MAKE) $(DISKSZIP)

$(DIST_DISKS): %: media/%
	cp $< $@

$(DISKSZIP): $(DIST_DISKS) LICENSE.md LICENSE-bis.md README.md ccp.md patches.md Makefile
	$(RM) $@
	COPYFILE_DISABLE=1 zip -X -j $@ $(DIST_DISKS) LICENSE.md LICENSE-bis.md README.md ccp.md patches.md

check-dist: dist
	unzip -t $(DISKSZIP)

check-redirection: all
	python3 tools/redirection_check.py

check-sdir: all
	python3 tools/sdir_check.py

check-type: all
	python3 tools/type_check.py
	python3 tools/type_check.py --passwords
	python3 tools/type_check.py --large

check-show: all
	python3 tools/show_check.py
	python3 tools/show_check.py --no-label
	python3 tools/show_check.py --create
	python3 tools/show_check.py --access

check-set: all
	python3 tools/set_check.py
	python3 tools/set_check.py --stamps
	python3 tools/set_check.py --passwords

check-wmenu: all
	python3 tools/wmenu_check.py

check-era: all
	python3 tools/import_check.py era

check-ren: all
	python3 tools/import_check.py ren

check-systat: all
	python3 tools/import_check.py systat

check-window: all
	$(MAKE) -C commands/window check livetest.cmd
	python3 tools/window_check.py

check-help: all
	python3 tools/help_check.py

check-dir-options: all
	python3 tools/dir_options_check.py

check-batch-live: all
	python3 tools/batch_check.py

check-help-live: all
	python3 tools/help_live_check.py

check-fat-batch: all
	python3 tools/fat_batch_check.py

# Mixed-case FAT names, modern case flags, PIP open-list lifetime and ERA.
check-fat-case: all
	python3 tools/fat_case_check.py

check-rtc: kernel
	$(MAKE) -C kernel/con check-rtc
