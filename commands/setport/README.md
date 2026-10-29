# SETPORT

Annotated assembly reconstruction of Concurrent DOS 4.1 `base/setport.cmd`
(26 August 1984). `setport.a86` is maintained; `setporg.a86` is the frozen
initial reconstruction. Both use ASM86. No NASM dependency is introduced.

## Build and verification

```
make
make check
make clean
```

The build uses `cpm86_asm86`, `cpm86_gencmd`, `cmdinfo` and Python 3, with
only local project inputs. Every one of the 2,950 loaded instructions is
written as assembly. Data directives contain copyrights, strings, tables,
workspace and padding only. Indirect menu/token handlers have labels too.
Code branches and DATA records use semantic names; `check.py` rejects the
former anonymous address-derived labels. String literals retain complete
text, including the three-character function-key legends.

The rebuilt command is **not strictly byte-identical**: ASM86 chooses 39
semantically identical, same-length encodings in the embedded HELP module.
RASM86 and Intel ASM86 were also tried and select the same alternative forms.
All instruction addresses, branches, data and file size remain unchanged.
`check.py` validates the original's SHA-256, verifies the equivalence of every
listed encoding, then compares the entire output against the expected image.
It never modifies a built file or masks a range. Both maintained and frozen
sources must pass, including the no-raw-code check.

## Usage

```
SETPORT
SETPORT HELP
SETPORT P3 1200 7 ODD 2 INRX ODNX
```

With no arguments, function-key menus select serial format and input/output
protocols. Escape applies settings and returns to the preceding menu; F1
opens context help from `HELP.HLP`. Interactive mode requires a local console;
serial terminals can use the command line.

| Argument | Values |
| --- | --- |
| Device | P3 = printer 3 / serial 0; P4 = printer 4 / serial 1 |
| Baud | 110, 150, 300, 600, 1200, 2400, 4800, 9600 |
| Word length | 5, 6, 7, 8 |
| Parity | NONE, ODD, EVEN |
| Stop bits | 1, 2 |
| Protocol | I or O, then D/N, R/N, X/N |

I/O selects input/output. D enables DTR/DSR, R enables RTS/CTS, X enables
XON/XOFF; N disables that position. All eight masks are accepted, including
INNN/ONNN. The example selects input RTS/CTS + XON/XOFF and output DTR/DSR +
XON/XOFF. Separate tokens with spaces. Unspecified serial fields retain the
hardware settings read at startup; protocol handlers update XIOS masks.

## Relationship to CONFIG

SETPORT is a recognizable extension of the earlier CONFIG implementation:
UART detection, divisor/format packing, token scanning, length-prefixed string
output and menu rendering follow the same design. It adds a main menu,
per-port input/output protocol menus, protocol tokens, and an embedded HELP
V2.0 engine with console image save/restore and a local line editor. The HELP
engine shares structure with the available HELP PL/M source; this remains a
reconstruction of the actual SETPORT binary, not a replacement compiled from
that other source. The version test requires BDOS 163 value 1441h.

## Original CMD layout

| File offset | Size | Contents |
| --- | ---: | --- |
| 0000h | 0080h | CMD header |
| 0080h | 1CC0h | CODE |
| 1D40h | 2780h | DATA |
| 44C0h | 0130h | STACK |
| 45F0h | 0010h | Disk-record padding |
| 4600h | 0080h | Relocation records, terminator and unloaded residue |

Within CODE, the copyright occupies 0003h–0047h, utility alignment
0AEAh–0AEFh, HELP copyright 0AF3h–0B30h, and final padding 1CBDh–1CBFh.
All other CODE bytes are instructions, including retained unused interfaces.

GENCMD emits an empty EXTRA descriptor before STACK. `header.py` validates
that exact output layout, removes the empty descriptor, restores the original
relocation header fields and appends the original final disk record. Its two
relocations refer to DATA segment words at CODE 0B53h and 0B60h. The zero
terminator is followed by stale linker-buffer bytes, which resemble older
protocol code but lie outside every loaded group and are never executed.
They are preserved explicitly as file-format data. No payload patching occurs.

## Encoding exceptions

Offsets below are relative to CODE (add 0080h for the file offset). MOV and
XOR reverse the opcode direction bit and the register fields; both forms have
identical operands. CMP uses the accumulator immediate form instead of the
sign-extended byte-immediate form; each occupies three bytes here. These are
the only permitted differences, recorded in `encodings.json` and checked
individually. Source comments mark every occurrence.

| CODE offset | Instruction | Original bytes | ASM86 bytes |
| --- | --- | --- | --- |
| 0EA4h | `mov al,ah` | `88E0` | `8AC4` |
| 0F0Eh | `mov si,cx` | `89CE` | `8BF1` |
| 0FECh | `cmp ax,0x3f` | `83F83F` | `3D3F00` |
| 1034h | `xor dx,dx` | `31D2` | `33D2` |
| 103Ah | `mov bx,ax` | `89C3` | `8BD8` |
| 1176h | `mov bx,ax` | `89C3` | `8BD8` |
| 11F9h | `mov cx,ax` | `89C1` | `8BC8` |
| 1200h | `mov bx,ax` | `89C3` | `8BD8` |
| 12C9h | `mov bx,ax` | `89C3` | `8BD8` |
| 12CDh | `mov si,dx` | `89D6` | `8BF2` |
| 130Eh | `mov bx,ax` | `89C3` | `8BD8` |
| 1326h | `mov bx,ax` | `89C3` | `8BD8` |
| 136Bh | `mov bx,ax` | `89C3` | `8BD8` |
| 1389h | `mov bx,ax` | `89C3` | `8BD8` |
| 13A5h | `mov bx,ax` | `89C3` | `8BD8` |
| 13B5h | `mov bx,ax` | `89C3` | `8BD8` |
| 13D1h | `mov bx,ax` | `89C3` | `8BD8` |
| 145Eh | `mov bx,ax` | `89C3` | `8BD8` |
| 1474h | `mov bx,ax` | `89C3` | `8BD8` |
| 14EEh | `mov bx,ax` | `89C3` | `8BD8` |
| 1536h | `xor dx,dx` | `31D2` | `33D2` |
| 157Ch | `mov bx,ax` | `89C3` | `8BD8` |
| 159Fh | `mov bx,ax` | `89C3` | `8BD8` |
| 1616h | `mov bx,ax` | `89C3` | `8BD8` |
| 1634h | `mov bx,ax` | `89C3` | `8BD8` |
| 1640h | `mov bx,ax` | `89C3` | `8BD8` |
| 1654h | `mov bx,ax` | `89C3` | `8BD8` |
| 167Ch | `mov bx,ax` | `89C3` | `8BD8` |
| 169Fh | `mov bx,ax` | `89C3` | `8BD8` |
| 16C0h | `mov si,ax` | `89C6` | `8BF0` |
| 16E7h | `mov bx,ax` | `89C3` | `8BD8` |
| 16F5h | `mov bx,ax` | `89C3` | `8BD8` |
| 1726h | `mov bx,ax` | `89C3` | `8BD8` |
| 1763h | `mov bx,ax` | `89C3` | `8BD8` |
| 179Dh | `mov bx,ax` | `89C3` | `8BD8` |
| 17B6h | `mov bx,ax` | `89C3` | `8BD8` |
| 17D2h | `mov bx,ax` | `89C3` | `8BD8` |
| 17F1h | `mov bx,ax` | `89C3` | `8BD8` |
| 185Bh | `mov bx,ax` | `89C3` | `8BD8` |

## Source organization

The source follows execution from startup and OS/console checks through
UART detection, format packing, command-tail token dispatch, configuration
menus, input/output protocol updates, and the display primitives. The
embedded HELP section then documents its BDOS wrappers, screen save/restore,
index lookup, topic parsing/listing, paging and local line editor. Shared
entries and indirect callbacks have names describing their role.

DATA uses explicit length words, quoted text, symbolic handler/string
pointers and typed workspace fields. Comments before DATA define the menu,
positioned-string, key-box and nine-byte command-token records. EQU aliases
identify mutable characters within strings without duplicating storage.
The loader base page and private stacks are distinguished from XIOS offsets.

The final annotation pass changes labels, comments and data presentation;
it does not change the instruction stream or the accepted 39 encoding
exceptions. Both sources are checked independently. `setporg.a86` remains
the frozen reference after this completed annotation pass.
