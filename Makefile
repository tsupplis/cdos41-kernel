.PHONY: all commands kernel check clean xios-alt
all: commands kernel
commands:
	$(MAKE) -C commands all
kernel:
	$(MAKE) -C kernel all
xios-alt:
	$(MAKE) -C kernel xios-alt
check: all
	@set -e; for f in kernel/con/*.con kernel/rsp?/*.rsp commands/genccpm/genccpm.cmd commands/pip/pip4.cmd commands/rmdir/rmdir.cmd commands/sysdisk/sysdisk.cmd; do cmdinfo $$f; done
clean:
	$(MAKE) -C commands clean
	$(MAKE) -C kernel clean
	$(MAKE) -C kernel/xios clean
