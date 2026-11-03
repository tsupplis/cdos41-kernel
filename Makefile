# Concurrent DOS 4.1 — local commands, kernel, boot track and disk distribution.
# all builds media; check verifies outputs; dist packages the disk images.

DISKSZIP=disks.zip
DIST_DISKS=cdos86.img cdostools.img cdosdev.img cdosmaint.img cdosmenu.img cdosdos.img cdosextras.img cdosadmin.img

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

.PHONY: chkcpmfs-live-images
chkcpmfs-live-images: kernel boot
	$(MAKE) -C media cdos86.img

xios-alt:
	$(MAKE) -C kernel xios-alt

check: all
	python3 tools/graphics_unit_check.py
	@set -e; for f in kernel/con/*.con kernel/rsp?/*.rsp; do cmdinfo $$f; done
	$(MAKE) -C commands check
	$(MAKE) -C kernel/sysgen check
	$(MAKE) -C kernel/con check-cursor check-rtc
	python3 tools/historical_check.py
	python3 tools/pctmp_recovery_check.py
	python3 tools/pctmp_io_check.py
	python3 tools/dos_stamp_check.py
	python3 tools/dos_api_check.py
	python3 tools/dos_console_check.py
	python3 tools/dos_switch_check.py
	python3 tools/dos_handles_check.py
	python3 tools/dos_redirection_config_check.py
	python3 tools/fat_recovery_check.py
	python3 tools/pctmp_context_check.py
	python3 tools/pctmp_critical_check.py
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
	python3 tools/dos_redirection_check.py

check-sdir: all
	python3 tools/sdir_check.py
	python3 tools/sdir_paths_check.py

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
	python3 tools/window_color_check.py

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

.PHONY: check-setenv
check-setenv: all
	python3 tools/setenv_check.py

# Execute historical recovery regressions against the locally built components.
.PHONY: check-historical
check-historical: kernel
	python3 tools/historical_check.py
	python3 tools/pctmp_recovery_check.py
	python3 tools/pctmp_io_check.py
	python3 tools/dos_stamp_check.py
	python3 tools/dos_api_check.py
	python3 tools/dos_console_check.py
	python3 tools/dos_switch_check.py
	python3 tools/dos_handles_check.py
	python3 tools/dos_redirection_config_check.py
	python3 tools/fat_recovery_check.py
	python3 tools/pctmp_context_check.py
	python3 tools/pctmp_critical_check.py

# Real DOS loaders and PSP services in a disposable PCE boot.
.PHONY: check-pctmp-live
check-pctmp-live: all
	python3 tools/pctmp_live_check.py
	python3 tools/dos_stamp_live_check.py
	python3 tools/dos_api_live_check.py
	python3 tools/dos_console_live_check.py
	python3 tools/dos_handles_live_check.py

# Compare original and rebuilt commands on disposable CP/M and FAT media.
.PHONY: check-release-commands
check-release-commands: all
	python3 tools/release_commands_check.py
	python3 tools/date_check.py

.PHONY: check-dskmaint-live
check-dskmaint-live: all
	python3 tools/dskmaint_live_check.py

.PHONY: check-retcode
check-retcode: media
	python3 tools/retcode108/check.py

# Same independent loader fixtures in CCP/M and CDOS; disposable PCE disks only.
.PHONY: check-exe
check-exe: all
	python3 tools/exe_header_check.py

# Version-query and CON raw/cooked handle semantics; disposable PCE media.
.PHONY: check-dos-console
check-dos-console: all
	python3 tools/dos_console_check.py
	python3 tools/dos_console_live_check.py

# Enhanced EGA/VGA drawing; NASM fixtures and disposable PCE disks only.
.PHONY: check-graphics
check-graphics: all
	python3 tools/graphics_unit_check.py
	python3 tools/graphics_check.py
	python3 tools/graphics_check.py ega
	python3 tools/graphics_check.py cga

# DOS option-prefix state, EXEC and launch persistence on disposable media.
.PHONY: check-dos-switch
check-dos-switch: all
	python3 tools/dos_switch_check.py
	python3 tools/dos_switch_live_check.py

# Allocation-info and free-space drive validation; disposable PCE disks only.
.PHONY: check-dos-allocation
check-dos-allocation: all
	python3 tools/pctmp_io_check.py
	python3 tools/dos_alloc_live_check.py
