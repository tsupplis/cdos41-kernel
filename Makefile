DISKSZIP=disks.zip
DIST_DISKS=cdos86.img cdostools.img cdosmaint.img cdosmenu.img cdosdos.img cdosoem1.img cdosoem2.img

.PHONY: all commands kernel boot media check check-pce test clean xios-alt
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
	$(MAKE) -C kernel/con check-cursor
	$(MAKE) -C boot check
	$(MAKE) -C media check
check-pce: all
	$(MAKE) -C media check-pce
test: all
	$(MAKE) -C media test
clean:
	$(MAKE) -C commands clean
	$(MAKE) -C kernel clean
	$(MAKE) -C kernel/xios clean
	$(MAKE) -C boot clean
	$(MAKE) -C media clean
	$(RM) $(DISKSZIP) $(DIST_DISKS)

.PHONY: check-aliases
check-aliases: all
	python3 tools/alias_check.py

.PHONY: dist check-dist
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

.PHONY: check-redirection
check-redirection: all
	python3 tools/redirection_check.py

.PHONY: check-sdir
check-sdir: all
	python3 tools/sdir_check.py

.PHONY: check-type
check-type: all
	python3 tools/type_check.py
	python3 tools/type_check.py --passwords
	python3 tools/type_check.py --large

.PHONY: check-show
check-show: all
	python3 tools/show_check.py
	python3 tools/show_check.py --no-label
	python3 tools/show_check.py --create
	python3 tools/show_check.py --access

.PHONY: check-set
check-set: all
	python3 tools/set_check.py
	python3 tools/set_check.py --stamps
	python3 tools/set_check.py --passwords

.PHONY: check-wmenu
check-wmenu: all
	python3 tools/wmenu_check.py

.PHONY: check-era
check-era: all
	python3 tools/import_check.py era

.PHONY: check-ren
check-ren: all
	python3 tools/import_check.py ren

.PHONY: check-systat
check-systat: all
	python3 tools/import_check.py systat

.PHONY: check-window
check-window: all
	$(MAKE) -C commands/window check livetest.cmd
	python3 tools/window_check.py

.PHONY: check-help check-dir-options check-batch-live
check-help: all
	python3 tools/help_check.py
check-dir-options: all
	python3 tools/dir_options_check.py
check-batch-live: all
	python3 tools/batch_check.py

.PHONY: check-help-live
check-help-live: all
	python3 tools/help_live_check.py

.PHONY: check-fat-batch
check-fat-batch: all
	python3 tools/fat_batch_check.py
