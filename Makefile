DISTDIR=dist
DISKSZIP=disks.zip
DIST_DISKS=cdos86.img cdostools.img cdosmaint.img cdosmenu.img cdosdos.img cdosoem1.img cdosoem2.img
SOURCEDIST=$(DISTDIR)/cdos86-source.tar.gz

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
	rm -rf $(DISTDIR)

.PHONY: check-aliases
check-aliases: all
	python3 tools/alias_check.py

.PHONY: dist source-dist check-dist
# Re-enter after recursive builds, as in CCP/M, to refresh image timestamps.
dist: all
	$(MAKE) $(DISKSZIP) source-dist

$(DIST_DISKS): %: media/%
	cp $< $@

$(DISKSZIP): $(DIST_DISKS) LICENSE.md LICENSE-bis.md README.md ccp.md patches.md Makefile
	$(RM) $@
	COPYFILE_DISABLE=1 zip -X -j $@ $(DIST_DISKS) LICENSE.md LICENSE-bis.md README.md ccp.md patches.md

# Include tracked and new source inputs; omit ignored build products/deletions.
source-dist:
	mkdir -p $(DISTDIR)
	@git ls-files --cached --others --exclude-standard | LC_ALL=C sort -u | \
	  while IFS= read -r source; do \
	    if test -f "$$source"; then printf '%s\n' "$$source"; fi; \
	  done > $(DISTDIR)/source-files.txt
	COPYFILE_DISABLE=1 tar -czf $(SOURCEDIST) -T $(DISTDIR)/source-files.txt

check-dist: dist
	unzip -t $(DISKSZIP)
	tar -tzf $(SOURCEDIST) > /dev/null
