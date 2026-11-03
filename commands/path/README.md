# PATH

`PATH.CMD` displays or sets the owning console's DOS search path through the
native PCTMP environment interface. The same `npath.lib` implementation is
compiled directly into TMP and BATCH; their built-ins need no external file.

```
PATH
PATH=B:\TOOLS;C:\BIN
PATH B:\TOOLS;C:\BIN
PATH=
PATH ;
```

The last two forms clear the value. Names are stored as uppercase `PATH`;
values retain their supplied case. Other environment variables are preserved.
Validation checks the environment terminator, capacity and 127-byte value
limit before modifying the block. A failed update leaves it unchanged.
Explicit `PATH.CMD` can be launched through P_CLI and has TAIL=KEEP.
PATH controls the DOS environment; SYSDISK controls native system searching.

`pathx.a86` and `check.py` are retained as the legacy DOS PATH reconstruction
and comparison reference. They do not participate in the native default build.
The historical `base/path.exe` remains available for interoperability tests.
