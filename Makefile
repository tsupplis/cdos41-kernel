.PHONY: all commands kernel boot media check test clean xios-alt
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
	$(MAKE) -C boot check
	$(MAKE) -C media check
test: all
	$(MAKE) -C media test
clean:
	$(MAKE) -C commands clean
	$(MAKE) -C kernel clean
	$(MAKE) -C kernel/xios clean
	$(MAKE) -C boot clean
	$(MAKE) -C media clean
