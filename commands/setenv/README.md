# SETENV

Native CMD for Concurrent DOS, built with DR C, RASM86 and the same native
LINKCMD wrapper as the other C commands. TAIL=KEEP preserves the command tail.
There is no DOS runtime, PSP or INT 21h dependency.

```text
SETENV
SETENV NAME
SETENV NAME=value
SETENV NAME=
SETENV [HELP]
```

List all variables, display one, add/replace, or delete respectively. Names
are case-insensitive and always stored uppercase when added or replaced;
values retain case and spaces. For example, `SETENV Temp=Mixed Case` stores
`TEMP=Mixed Case`. Empty values remove variables. The command tail limits
one assignment to 127 characters. SETENV itself adds no quoting or expansion
language; BATCH performs its own substitutions before launching a command.

The owning PCTMP is found through the native process-parent chain. Its private
ms_func selector 0Ah returns the shared environment segment and capacity.
The query does not mutate memory; SETENV uses that pointer for its validated
commit. Unsupported PCTMP versions return an error without a write. The build
reserves 1024 bytes per console; PATH.EXE and DOS programs see the same block
through PSP:002Ch. Changes persist until reboot and are not saved to disk.

Edits are built in a separate buffer. Invalid blocks and insufficient space
cause no writes. This is a shared per-console environment, not a private copy
for each program. Concurrent writers on one console are not locked.

`make check` validates the CMD header, TAIL=KEEP and the portable editor's
addition, replacement/deletion, uppercase names, exact-fit capacity, overflow
and malformed blocks. Root `make check-setenv` tests native discovery,
mixed-case values, uppercase names, deletion, more than 128 bytes and DOS PATH
interoperability on disposable emulator disks.
