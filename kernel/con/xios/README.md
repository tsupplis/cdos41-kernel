# XIOS source layout

The three `.a86` files are short assembly entry points. Edit their functional
`.lib` includes; no source generation or flattening is involved. RASM86 builds
core.obj, console.obj and devices.obj; LINK86 links them into one XIOS component
with one loaded segment. Other kernel components retain their existing layout.

| Object | Maintained includes |
| --- | --- |
| Core | xsystem.lib (header, dispatch, interrupts), xservice.lib (supervisor interface), xrtc.lib, xinit.lib |
| Console | xkey.lib, xinput.lib (input, status, control blocks), xcon1.lib, xcon2.lib, egvideo.lib |
| Devices | xdiskirq.lib, xdevice.lib, xaux.lib, xfloppy.lib, xhard.lib |

coreif.inc, consif.inc and devif.inc declare each object's imports and exports.
shared.inc holds common constants and macros. consoles.def remains the shared
XIOS/CIO configuration. All includes appear directly in the entry files because
RASM86 does not support nested INCLUDE. Keep their order: it determines layout.
Assembly uses consistent label, operation and operand columns and CRLF endings.
Preserve spaces inside string operands.

Run `make -C kernel/con xios.con`. tools/build_xios.py stages sources in
kernel/con/.xios/xios and retains assembler/linker logs and result.json there.
Published diagnostics remain squid.sym and squid.map for existing tools.

The build checks fixed SYS-DATA/header/SETUP offsets in abi.json, entry jumps,
and that the two UART input buffers fit wholly inside reclaimable startup code.
HARD8087 prevents emulator substitution; the published header preserves
optional-NDP behaviour because XIOS probes hardware itself.

Default assembler use factors are 46/69/54 percent (core/console/devices).
The component remains 37,760 file bytes and 37,568 loaded bytes.
