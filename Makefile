.PHONY: all commands kernel check clean xios-alt
all: commands kernel
commands:
	$(MAKE) -C commands all
kernel:
	$(MAKE) -C kernel all
xios-alt:
	$(MAKE) -C kernel xios-alt
check: all
	@set -e; for f in kernel/con/*.con kernel/rsp?/*.rsp; do cmdinfo $$f; done
	$(MAKE) -C commands check
clean:
	$(MAKE) -C commands clean
	$(MAKE) -C kernel clean
	$(MAKE) -C kernel/xios clean
