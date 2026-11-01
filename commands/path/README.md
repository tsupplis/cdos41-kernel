# DOS PATH

PATH.EXE is equivalent to the CDOS 4.11 executable on release disk 3.
The rebuild has the same command body and data. The original enters the
314-byte body through five NOPs. The rebuild places the padding after it.
Calls and branches move with the body and data offsets stay fixed.

The startup jump skips the four differing linker identification bytes.
In the backward group-copy routine the original starts a paragraph copy at
offset 0Fh, while the local linker emits 0Eh. PATH cannot enter this routine.
Its two populated groups require exactly their stored lengths (20 and 24
paragraphs) and request no expansion. The loader exits if memory is too
small. Otherwise the accumulated extra space is zero at every group, so
the displacement test skips the copy call at CS:01C9h. This conclusion
applies specifically to this executable's group descriptors.

The remaining difference is the MZ checksum. `make check` verifies the
entire executable against the pinned release hash with these exact changes.
