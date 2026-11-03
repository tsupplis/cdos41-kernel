# API inventory — Concurrent DOS 4.1

| Scope | Contract |
| --- | --- |
| Build | Current CDOS 4.1 PC-MODE build with IBM SQUID XIOS; 3 November 2026 |
| Numbers | Hexadecimal unless explicitly labelled decimal |
| Implemented | Handler present in current code; not exhaustive DOS conformance certification |
| Partial / stub / missing | Limited contract / no operation / no implementation |
| DOS files | CP/M and FAT12/FAT16 media; FCB and DOS 2.x handle/pathname adapters; FAT subdirectories |
| TMP | Native command processor (`kernel/rsp1`); does not provide DOS interrupts |
| PCTMP | PC-MODE command processor, COM/EXE loader and DOS/BIOS interrupt adapters (`kernel/rsp3`) |
| XIOS | Shared hardware, console, keyboard, display, disk and printer implementation (`kernel/con`) |
| Extension column | NEW marks an implemented local addition beyond stock CDOS 4.1. European recovery identifies release-binary behaviour recovered into OEM sources. — means inherited behaviour, including documented limitations |
| Native API | `INT E0h` is provided by the shared kernel; DOS interrupts belong to PCTMP |

## INT 21h — DOS 1.x services and version/DTA queries

| AH | Service | Reference version | Status | Limit / behaviour | Extension |
| --- | --- | --- | --- | --- | --- |
| 00 | Terminate | DOS 1.x | Implemented | Legacy termination; CS must identify PSP | — |
| 01 | Console input with echo | DOS 1.x | Implemented | Standard input (0), echo to standard output (1); Ctrl-C processing | NEW (streams) |
| 02 | Console output | DOS 1.x | Implemented | Standard output (1) | NEW (streams) |
| 03 | AUX input | DOS 1.x | Implemented | Native AUX input with CIO ownership | — |
| 04 | AUX output | DOS 1.x | Implemented | Native AUX output with CIO ownership | — |
| 05 | Printer output | DOS 1.x | Implemented | Native list output; assigned printer | — |
| 06 | Direct console I/O | DOS 1.x | Implemented | DL=FFh polls standard input (0); other DL writes standard output (1) | NEW (streams) |
| 07 | Console input without echo/check | DOS 1.x | Implemented | Standard input (0), without echo or Ctrl-C check | NEW (streams) |
| 08 | Console input without echo, Ctrl-C check | DOS 1.x | Implemented | Standard input (0); Ctrl-C processing | NEW (streams) |
| 09 | Print dollar-terminated string | DOS 1.x | Implemented | Standard output (1), dollar-terminated string | NEW (streams) |
| 0A | Buffered console input | DOS 1.x | Implemented | Standard input/output; capacity includes CR, DEL acts as Backspace, zero capacity returns immediately; EOF count zero, CR/LF line input | NEW (streams) |
| 0B | Console input status | DOS 1.x | Implemented | Non-consuming readiness of standard input (0); clear at EOF | NEW (streams) |
| 0C | Flush input and read | DOS 1.x | Implemented | Flush keyboard input; AL=01h/06h/07h/08h/0Ah selects the corresponding standard-stream operation | NEW (streams) |
| 0D | Disk reset | DOS 1.x | Implemented | — | — |
| 0E | Select default drive | DOS 1.x | Implemented | — | — |
| 0F | FCB open | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 10 | FCB close | DOS 1.x | Implemented | Uses the opening directory saved in reserved FCB word 1Ch, then restores the current directory | — |
| 11 | FCB find first | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 12 | FCB find next | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 13 | FCB delete | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 14 | FCB sequential read | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 15 | FCB sequential write | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 16 | FCB create | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 17 | FCB rename | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 18 | Reserved/legacy in-use | Unused / stub | Unused | AL=00h; no service performed | — |
| 19 | Get default drive | DOS 1.x | Implemented | — | — |
| 1A | Set DTA | DOS 1.x | Implemented | — | — |
| 1B | Allocation information, current drive | DOS 1.x | Implemented | FAT12/16 geometry and DS:BX pointing at the FAT buffer’s media byte; cluster counts exclude reserved clusters. CP/M media supplies allocation geometry; its hash buffer is not a DOS FAT | — |
| 1C | Allocation information, selected drive | DOS 2.0 | Implemented | DL=0 current, 1–16=A:–P:; unsigned validation, AL=FFh for out-of-range/unavailable drives or DPB failure; preserves default drive. Same media-dependent geometry/pointer contract as 1B | NEW (invalid-drive fix) |
| 1D | Reserved/legacy read-only | Unused / stub | Unused | AL=00h; no service performed | — |
| 1E | Reserved/legacy attributes | Unused / stub | Unused | AL=00h; no service performed | — |
| 1F | Get current-drive DPB | DOS 1.x | Missing | m_null returns AL=00h; no DOS DPB pointer | — |
| 20 | USERCODE placeholder | Reserved | Stub | AL=00h; no user-code service | — |
| 21 | FCB random read | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 22 | FCB random write | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 23 | FCB file size | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 24 | Set FCB random record | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 25 | Set interrupt vector | DOS 1.x | Implemented | Vector replacement; not a promise of device virtualization | — |
| 26 | Create PSP | DOS 1.x | Implemented | PSP creation; does not allocate memory or EXEC | — |
| 27 | FCB random block read | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 28 | FCB random block write | DOS 1.x | Implemented | FCB adapter → shared CP/M/FAT filesystem | — |
| 29 | Parse filename into FCB | DOS 1.x | Implemented | — | — |
| 2A | Get date | DOS 1.x | Implemented | — | — |
| 2B | Set date | DOS 1.x | Implemented | — | — |
| 2C | Get time | DOS 1.x | Implemented | — | — |
| 2D | Set time | DOS 1.x | Implemented | — | — |
| 2E | Set verify-on-write | DOS 1.x | Implemented | AL=0/1 disables/enables additional system-wide physical write verification | NEW |
| 2F | Get DTA | DOS 2.0 | Implemented | ES:BX=current DTA | — |
| 30 | DOS version query | DOS 2.0 | Implemented | AX=0002h, BH=FFh (generic OEM), BL:CX=0 (serial); other saved registers preserved. Native CDOS version is separate | NEW (complete register returns) |


## INT 21h — DOS 2.x services

AH=2Fh through 68h dispatch through `ms2_func_table`. Successful entry clears
CF; error handlers set CF and return a DOS error in AX. This differs from the
DOS 1.x FCB AL-status convention. Unimplemented slots are explicitly listed below.

DOS 2.0 already included the internal interfaces 1Fh, 32h, 34h, 37h,
50h–53h and 55h; they are not reserved slots or later-DOS additions.
Some expose version-dependent DOS data structures. The statuses below
describe this kernel’s implementation. See Microsoft’s
[DOS 2.0 system-call assignments](https://github.com/microsoft/MS-DOS/blob/main/v2.0/source/SYSCALL.txt).

| AH | Service | Status | Limit / behaviour | Extension |
| --- | --- | --- | --- | --- |
| 31 | Terminate and keep resident | Partial | Records termination type 3 and disowns the process memory; ignores DX retained-paragraph count; not full DOS TSR compatibility | — |
| 32 | Get selected-drive DOS DPB | Stub | No service; CF clear, AL=0, AH retained | — |
| 33 | Ctrl-Break control | Implemented | AL=0 queries DL; AL=1 sets DL=0/1. Enabled checking polls additional DOS calls and invokes INT 23h with caller registers. Raw 06h/07h and 33h/59h are excluded | NEW |
| 34 | Get InDOS flag pointer | Stub | No pointer; CF clear, AL=0, AH retained | — |
| 35 | Get interrupt vector | Implemented | AL=vector, ES:BX=result from interrupt vector table | — |
| 36 | Free disk space | Implemented | Geometry and free clusters from native services; shares 1Ch’s unsigned drive validation. Invalid/unavailable drive returns AX=FFFFh; default drive preserved | NEW (invalid-drive fix) |
| 37 | Switch character / device availability | Partial | AL=0 queries DL, AL=1 sets from DL; AL=0 on success, AL=FFh for unsupported selectors, CF clear. Default `/`; shared within one console across EXEC and root launches. Device-availability selectors 2/3 remain unsupported | NEW (get/set switch character) |
| 38 | Country information | Implemented | AL=0 returns the full 32-byte US record. Other selectors and DX=FFFFh return CF set, AX=2 | NEW |
| 39 / 3A / 3B | Make / remove / change directory | Implemented | FAT hierarchical directories; CP/M user areas are not DOS directories | — |
| 3C / 3D / 3E | Create / open / close handle | Implemented | 20 handle slots, initially 0-4 are standard devices. Close releases device and standard references; final disk references flush before reuse | NEW (handle lifecycle) |
| 3F / 40 | Read / write handle | Implemented | Byte counts and shared position; EOF reads stop at the logical byte length, including size-plus-one requests | NEW (EOF boundary fix) |
| 41 | Delete pathname | Implemented | Path parsing followed by native file deletion | — |
| 42 | Seek handle | Implemented | Origins 0/1/2: beginning/current/end | — |
| 43 | Get / set file attributes | Implemented | Translated native/FAT attributes; media-dependent semantics | — |
| 44 | IOCTL | Partial | AL=0 returns device/file information; AL=1 sets CON raw/cooked mode via DL bit 5 (DH must be zero). AH=3Fh/40h honor the mode; DUP/EXEC share it. AL=6/7 queries readiness. Other selectors/devices for AL=1 return AX=1 | NEW |
| 45 / 46 | Duplicate / force duplicate handle | Implemented | Shared position and counted ownership; checked targets, self/alias duplication and close failures. Standard handles can be rebound | NEW (ownership and validation) |
| 47 | Get current directory | Implemented | Reconstructs FAT path using the temporary P: directory mapping | — |
| 48 / 49 / 4A | Allocate / free / resize memory | Implemented | DOS memory descriptor blocks, PSP ownership and largest-available-block errors | — |
| 4B | Execute / load program or overlay | Partial | AL=0 runs COM/EXE with inherited handles and restores parent registers, stack and DTA. AL=1 prepares a child; AL=3 loads an EXE overlay. Other selectors rejected | European recovery + NEW (EXEC lifecycle) |
| 4C | Terminate with status | Implemented | AL=status, type 0. Releases child handle references including standard streams and restores the parent table | NEW (handle cleanup) |
| 4D | Get child return code | Implemented | Returns stored status/type in AX, then clears it; distinct from native function 108 and private shell return code | — |
| 4E / 4F | Find first / next by pathname | Implemented | DTA search state, attributes and translated CP/M/FAT entries | — |
| 50 | Set current PSP | Implemented | Saves BX in the active PSP used by EXEC/termination; does not switch concurrent processes | European 1985 recovery |
| 51 | Get current PSP | Implemented | Returns the active PSP segment in BX | European 1985 recovery |
| 52 | Get DOS internal-variable pointer (list of lists) | Stub | No pointer; CF clear, AL=0, AH retained | — |
| 53 | Construct DOS DPB from BPB | Stub | No DPB constructed; CF clear, AL=0, AH retained | — |
| 54 | Get verify flag | Implemented | AL=0/1 returns the additional system-wide verification setting from XIOS | NEW |
| 55 | Duplicate PSP | Stub | No PSP duplicated; CF clear, AL=0, AH retained | — |
| 56 | Rename pathname | Implemented | Path preparation and native rename | — |
| 57 | Get / set handle date/time | Implemented | AL=0/1, disk files, 1980-2099. FAT retains two-second precision. CP/M requires update stamps and stores minutes. Set failures return CF set | NEW |
| 58 | Later service | Missing | CF set, AX=1 | — |
| 59 | Extended error information | Implemented | BX=0 queries the last error in AX, class in BH, action in BL and locus in CH. Successful calls and repeated queries retain the error; state is per console | NEW |
| 5A–67 | Later services | Missing | CF set, AX=1 | — |
| 68 | Commit file | Implemented | Flushes an open disk file and byte-count metadata, retaining its handle, position, directory context and lock. Invalid/device handles return AX=6 | NEW |
| 69–FF | Later services | Missing | CF set, AX=1 | — |

## Filesystem and process boundaries

| Interface | CDOS 4.1 contract |
| --- | --- |
| DOS versus native version | INT 21h/AH=30h returns 0002h. INT E0h/CL=0Ch and A3h return 1441h in this build |
| DOS allocation pointers | AH=1Bh/1Ch return the drive hash/FAT buffer segment with offset zero. On FAT media this holds FAT data; on CP/M media it is not a DOS FAT. AH=1Fh remains unimplemented |
| Native file services | The same FCB calls reach CP/M or FAT media; directory, password, label and stamp operations are media-dependent, not interchangeable |
| Native FAT search results | BLACK translates entries into CP/M-style records. Bytes 16 and 17 repeat flags: bit 80h indicates DOS representation, bit 40h a directory. Check the byte-0 XFCB guard before interpreting allocation bytes this way |
| FAT names and F4 | Short names are matched without case. FAT byte 12 case bits do not activate CP/M F4 compatibility in the patched kernel; genuine CP/M F4 remains supported |
| CP/M-only metadata | User areas, XFCB passwords and configurable directory labels/stamping are CP/M facilities; see SET/SHOW command notes for rejected FAT operations |
| Native CMD tail case (NEW) | Local header extension: byte 7Fh bit 1 (02h) opts into case preservation. Clear means historical uppercase conversion. CHSET TAIL=KEEP/UPPER edits the flag; filenames/default FCBs still use normal parsing. BATCH/ECHO/PUT/GET/RDR opt in; DOS INT 21h is unchanged |
| Program loading | Native CLI (E0h/96h) loads native programs; the shell separately selects CMD/BAT/COM/EXE and uses the PC-MODE loader for DOS programs. DOS EXEC is a third, DOS-caller interface |
| Write verification | Direct XIOS AL=27h (39 decimal), CH=0/1 sets additional verification, CH=FFh queries; AX=BX returns 0/1. Local extension beyond 4.1; boot-time floppy and per-volume hard-disk verification remain additive |
| Environment | Per-console DOS environment is 1,024 bytes in this build; DOS PSP exposes its segment. SETENV.EXE edits it; this is not an extra INT E0h function |
| Console redirection | GET/PUT/RDR support native BDOS console calls and DOS standard input/output, including legacy INT 21h calls; shell `<`, `>` and `|` parsing is not implemented |

## Graphics modes and entry points

Mode selection and drawing support are separate contracts. “BIOS mode” below
identifies the display format; native callers select it through XIOS or the
console escape stream, without executing a DOS program.

| BIOS mode (hex) | Display | Adapter | Native XIOS mode byte | Native `ESC a` parameter | DOS INT 10h/AH=00h |
| --- | --- | --- | --- | --- | --- |
| 04 | 320×200, 4 colours | CGA, or detected colour EGA/VGA | 20h | 04h | Implemented |
| 05 | 320×200, 4 pixel values, CGA monochrome/burst-disabled variant | CGA, or detected colour EGA/VGA | 30h | 05h | Implemented |
| 06 | 640×200, 2 colours | CGA, or detected colour EGA/VGA | 40h | 06h | Implemented |
| 0D | 320×200, 16 colours | Colour EGA or VGA | 60h | 0Dh | Implemented |
| 0E | 640×200, 16 colours | Colour EGA or VGA | 70h | 0Eh | Implemented |
| 10 | 640×350, 16 colours | Colour EGA with at least 128 KB, or VGA passing the capability probe | 50h | 10h | Implemented |
| 11 | 640×480, 2 colours | VGA | 80h | 11h | Implemented |
| 12 | 640×480, 16 colours | VGA | 90h | 12h | Implemented |
| 13 | 320×200, 256 colours | VGA | A0h | 13h | Implemented |
| Other graphics modes | 0Fh (EGA monochrome), VESA and nonstandard modes | — | Not assigned | Not supported | No compatibility claim |

Text modes use the existing native console/window implementation. DOS mode
selectors 00h–03h and 07h have text mappings; these are not a promise of
arbitrary BIOS pages, fonts or EGA/VGA text geometries. `ESC a` does not use
the same mapping for every text selector as INT 10h.

| Native interface | Contract |
| --- | --- |
| `ESC a` | Emit bytes 1Bh, 61h, then the binary mode parameter above (not ASCII digits) |
| XIOS function 30 decimal | CH=0 sets the mode byte in CL for console DL; CH=1 queries. This is an XIOS entry, **not** BDOS function 30 or a permitted direct-BIOS packet selector |
| CGA palette extension | XIOS function 30, CH=2, CL=CGA colour-select value (bits 0–5); graphics owner only |
| EGA palette extension | XIOS function 30, CH=3, CL=palette entry 0–15, DH=6-bit EGA colour, DL=console; requires native planar mode 50h–90h and graphics ownership |
| Capability probe | INT E6h, AL=1Eh (30 decimal), input BX=0: AX=4745h (`EG`), BX bit 0 enables BIOS 10h (native 50h), bit 1 enables 0Dh/0Eh, bit 2 enables VGA 11h/12h/13h and DAC; probe before selecting |
| Console switching | BIOS-backed graphics keeps the foreground console until the owner restores text mode; there is no per-console saved EGA/VGA graphics framebuffer |

Planar graphics uses the captured adapter ROM through the XIOS IRQ/PIC
and private-stack guard, without calling the intercepted INT 10h. Page zero
and foreground graphics ownership are required. Pixel operations validate
coordinates; planar modes retain the BIOS bit-7 XOR convention, while mode
13h accepts the entire colour byte through a dedicated chain-4 memory backend
that saves/restores graphics-controller registers, sequencer masks and index selectors. Cursor, character, TTY and rectangular
scroll services use the adapter's graphics font and layout. Text restoration
reloads the firmware text mode/font and redraws the native console.

INT 10h/AH=10h implements AL=00h (single EGA palette write), 07h (VGA palette read) and
10h/15h (single VGA DAC RGB write/read, entries 0–255, components 0–63).
EGA palette entry services apply to the planar modes; mode 13h uses DAC entries.
Mode-set bit 7 (preserve display memory), block palettes, arbitrary pages,
font loading and VESA services are not added.
Native XIOS function 31 uses the nine-byte AX,BX,CX,DX,console packet; setting
bit 7 of its BIOS selector requests that packet ABI for cursor/cell/TTY too.
Palette selector 90h uses AX's low byte as its AH=10h subfunction. Results
are returned in AX for pixel/character reads, and in the packet's BX/CX/DX
for cursor and palette reads. Native requests rejected before hardware access
return FFFFh; DOS rejected reads retain the original result registers.
Legacy native simple selectors retain their ABI.

Sources: [xcon1.lib](kernel/con/xcon1.lib), [xcon2.lib](kernel/con/xcon2.lib),
[xbegin.lib](kernel/con/xbegin.lib), [ms1.a86](kernel/rsp3/ms1.a86).

## DOS and BIOS interrupts

| INT | Selector | Service | Status / limit | Implementation | Extension |
| --- | --- | --- | --- | --- | --- |
| 10 | AH=00 | Set video mode | Implemented: text/CGA and EGA/VGA modes in the graphics table | PCTMP + XIOS | — |
| 10 | AH=01 | Set cursor shape | Implemented | PCTMP + XIOS | — |
| 10 | AH=02 | Set cursor position | Implemented; bounded to console | PCTMP + XIOS | — |
| 10 | AH=03 | Get cursor position/shape | Partial in text/CGA: position returned, CX=0; enhanced graphics returns ROM position/shape | PCTMP + XIOS | — |
| 10 | AH=04 | Light pen | No operation | PCTMP | — |
| 10 | AH=05 | Select display page | No operation; one page exposed | PCTMP | — |
| 10 | AH=06 / 07 | Scroll up / down | Implemented; bounded rectangle | PCTMP + XIOS | — |
| 10 | AH=08 | Read character/attribute | Implemented | PCTMP + XIOS | — |
| 10 | AH=09 | Write character/attribute | Implemented; cursor unchanged, page forced to zero | PCTMP + XIOS | — |
| 10 | AH=0A | Write character | Implemented; console default attribute, page forced to zero | PCTMP + XIOS | — |
| 10 | AH=0B | CGA palette | CGA palette-port implementation; not a general EGA/VGA palette interface | PCTMP + XIOS | — |
| 10 | AH=0C / 0D | Write / read pixel | Implemented: listed EGA/VGA modes use bounded ROM pixel services; legacy CGA framebuffer path retained | PCTMP + XIOS | — |
| 10 | AH=0E | Teletype | Native console output path | PCTMP + XIOS | — |
| 10 | AH=0F | Get video mode | Implemented; BH=0 | PCTMP + XIOS | — |
| 10 | AH=10 | Palette / DAC | Partial: AL=00 EGA entry writes; AL=07 VGA entry reads; AL=10/15 VGA DAC entries; enhanced graphics owner only | PCTMP + XIOS | NEW |
| 10 | AH=10–FF | Later video functions | No operation | PCTMP | — |
| 11 | — | Equipment word | XIOS synthesises equipment word from firmware data and the saved console mode | PCTMP + XIOS | — |
| 12 | — | Memory size | Allocation end in KiB; not a general physical-memory entitlement | PCTMP | — |
| 13 | AH=02 / 03 / 04 | Raw read / write / verify | Implemented / limited: enabled PCMODE BDOS raw I/O; AH=04 verifies by reading one sector, not the full requested count; legacy CH/CL encoding | PCTMP → BDOS | — |
| 13 | Other AH | Other disk services | AX=0, CF clear without service; not usable support | PCTMP | — |
| 14 | All | Serial BIOS | Not intercepted; native AUX services do not virtualize BIOS INT 14h | Firmware | — |
| 15 | All | Cassette / later system services | Not intercepted; firmware-dependent | Firmware | — |
| 16 | AH=00 | Read key | Implemented; per-console queue | PCTMP + CIO/XIOS | — |
| 16 | AH=01 | Poll key | Implemented; per-console lookahead, ZF status | PCTMP + CIO/XIOS | — |
| 16 | AH=02 | Shift status | Implemented; per-console state | PCTMP + XIOS | — |
| 16 | AH=03–FF | Other / enhanced keyboard calls | Fall through to shift query; not their specified service | PCTMP | — |
| 17 | AH=00 | Print character | Native assigned list device; ownership and bounded ready poll; ignores BIOS printer selection | PCTMP + CIO/XIOS | — |
| 17 | AH=01 | Initialize printer | Native list detach; not BIOS hardware initialization | PCTMP + CIO | — |
| 17 | AH=02 | Printer status | Native list status mapping | PCTMP + XIOS | — |
| 17 | AH=03–FF | Other printer calls | No service after ownership check | PCTMP | — |
| 18 / 19 | — | ROM BASIC / bootstrap | Not intercepted; no application compatibility contract | Firmware | — |
| 1A | All | BIOS clock | Firmware entry is not intercepted. XIOS now reads BIOS RTC at startup and writes it when native date/time changes; no per-process BIOS clock virtualization | Firmware | — |
| 1B / 1C | — | Break / timer callbacks | Not installed as PC-MODE virtual callbacks | Firmware / XIOS | — |
| 1D–1F | — | BIOS table vectors | No per-console virtualization | Firmware | — |
| 20 | — | Terminate | Implemented; CS=PSP legacy convention | PCTMP | — |
| 21 | AH | DOS service dispatch | See tables above | PCTMP | — |
| 22 | — | Termination continuation | Installed return/cleanup handler; callback, not ordinary service | PCTMP | — |
| 23 | — | Ctrl-C callback | Installed handler; checked-input unwind supported | PCTMP | — |
| 24 | — | Critical-error callback | DOS 1.x/2.x caller frames; retry, abort through INT 22h; DOS 2.x ignore returns success, DOS 1.x ignore retries | PCTMP | — |
| 25 / 26 | — | Absolute disk read / write | Enabled raw-disk path through BDOS/XIOS with cache flush/invalidation; legacy sector/count fields, original flags left on caller stack | PCTMP → BDOS | — |
| 27 | — | Stay resident | IRET only; does not retain a program | PCTMP | — |
| Other | — | Unlisted interrupts | No additional PCTMP-installed handler; existing firmware/kernel ownership applies | — | — |

## INT E0h — native Concurrent DOS services

| Calling convention | Value |
| --- | --- |
| Entry | CL=function; DX=parameter, DS=parameter segment |
| Return | AX=BX=result; CX=error when AX=FFFFh; ES=segment result where applicable |
| Preserved | DS, SI, DI, BP |
| Availability | Shared kernel table; the distributed shell is PCTMP; device services reach shared XIOS |
| Error 1 / 2 | Not implemented / illegal function number; AX=BX=FFFFh |

| CL hex | Decimal | Service | Module | Status / limit | Extension |
| --- | --- | --- | --- | --- | --- |
| 00 | 0 | system reset | RTM | Implemented | — |
| 01 | 1 | conin | CIO | Implemented | — |
| 02 | 2 | conout | CIO | Implemented | — |
| 03 | 3 | AUX input | CIO | Implemented; assigned AUX device and ownership | — |
| 04 | 4 | AUX output | CIO | Implemented; assigned AUX device and ownership | — |
| 05 | 5 | list out | CIO | Implemented | — |
| 06 | 6 | raw conio | CIO | Implemented | — |
| 07 | 7 | AUX input status | CIO | Implemented; alias of AAh, not CP/M IOBYTE | — |
| 08 | 8 | AUX output status | CIO | Implemented; alias of ABh, not CP/M IOBYTE | — |
| 09 | 9 | conwrite | CIO | Implemented | — |
| 0A | 10 | conread | CIO | Implemented | — |
| 0B | 11 | constat | CIO | Implemented | — |
| 0C | 12 | Get version | SUP | AX=BX=1441h in this build | — |
| 0D | 13 | diskreset | BDOS | Implemented | — |
| 0E | 14 | diskselect | BDOS | Implemented | — |
| 0F | 15 | file open | BDOS | Implemented | — |
| 10 | 16 | file close | BDOS | Implemented | — |
| 11 | 17 | search first | BDOS | Implemented | — |
| 12 | 18 | search next | BDOS | Implemented | — |
| 13 | 19 | file delete | BDOS | Implemented | — |
| 14 | 20 | file read seq | BDOS | Implemented | — |
| 15 | 21 | file write seq | BDOS | Implemented | — |
| 16 | 22 | file make | BDOS | Implemented | — |
| 17 | 23 | file rename | BDOS | Implemented | — |
| 18 | 24 | login vector | BDOS | Implemented | — |
| 19 | 25 | get def disk | BDOS | Implemented | — |
| 1A | 26 | set dma | BDOS | Implemented | — |
| 1B | 27 | get alloc vector | BDOS | Implemented | — |
| 1C | 28 | write protect | BDOS | Implemented | — |
| 1D | 29 | get r/0 vector | BDOS | Implemented | — |
| 1E | 30 | Set file attributes | BDOS | Implemented; F5'+F6' retain the open lock during a byte-count update | NEW (combined flags) |
| 1F | 31 | get disk parm block | BDOS | Implemented | — |
| 20 | 32 | user code | BDOS | Implemented | — |
| 21 | 33 | file read random | BDOS | Implemented | — |
| 22 | 34 | file write random | BDOS | Implemented | — |
| 23 | 35 | file size | BDOS | Implemented | — |
| 24 | 36 | set random record | BDOS | Implemented | — |
| 25 | 37 | reset drive | BDOS | Implemented | — |
| 26 | 38 | access drive | BDOS | Implemented | — |
| 27 | 39 | free drive | BDOS | Implemented | — |
| 28 | 40 | file write random w/zero fill | BDOS | Implemented | — |
| 29 | 41 | Test and Write (NOT IMPLEMENTED) | SUP | Not implemented; error 1 | — |
| 2A | 42 | Lock Record | BDOS | Implemented | — |
| 2B | 43 | Unlock Record | BDOS | Implemented | — |
| 2C | 44 | Set Multi-sector | BDOS | Implemented | — |
| 2D | 45 | Set Bdos Error Mode | BDOS | Implemented | — |
| 2E | 46 | Get Disk Free Space | BDOS | Implemented | — |
| 2F | 47 | Chain to Program | SUP | Implemented | — |
| 30 | 48 | Flush Buffers | BDOS | Implemented | — |
| 31 | 49 | Reserved | SUP | Illegal; error 2 | — |
| 32 | 50 | call xios | SUP | Restricted BIOS gateway; see below | — |
| 33 | 51 | set dma base | BDOS | Implemented | — |
| 34 | 52 | get dma | BDOS | Implemented | — |
| 35 | 53 | get max mem | MEM | Implemented | — |
| 36 | 54 | get abs max mem | MEM | Implemented | — |
| 37 | 55 | alloc mem | MEM | Implemented | — |
| 38 | 56 | alloc abs mem | MEM | Implemented | — |
| 39 | 57 | free mem | MEM | Implemented | — |
| 3A | 58 | free all mem | MEM | Implemented | — |
| 3B | 59 | load | SUP | Implemented | — |
| 3C | 60 | Reserved | SUP | Illegal; error 2 | — |
| 3D | 61 | Reserved | SUP | Illegal; error 2 | — |
| 3E | 62 | Reserved | SUP | Illegal; error 2 | — |
| 3F | 63 | Reserved | SUP | Illegal; error 2 | — |
| 40 | 64 | network login | NET | Requires optional NET module; absent from standard images | — |
| 41 | 65 | network logoff | NET | Requires optional NET module; absent from standard images | — |
| 42 | 66 | network send msg | NET | Requires optional NET module; absent from standard images | — |
| 43 | 67 | network rcv msg | NET | Requires optional NET module; absent from standard images | — |
| 44 | 68 | network status | NET | Requires optional NET module; absent from standard images | — |
| 45 | 69 | get network config addr | NET | Requires optional NET module; absent from standard images | — |
| 46 | 70 | set Compatibility attributes | NET | Requires optional NET module; absent from standard images | — |
| 47 | 71 | get network server config table | NET | Requires optional NET module; absent from standard images | — |
| 48 | 72 | set network error mode | NET | Requires optional NET module; absent from standard images | — |
| 49 | 73 | attach network | NET | Requires optional NET module; absent from standard images | — |
| 4A | 74 | detach network | NET | Requires optional NET module; absent from standard images | — |
| 4B | 75 | set message buffer size | NET | Requires optional NET module; absent from standard images | — |
| 4C | 76 | get network time and date | NET | Requires optional NET module; absent from standard images | — |
| 4D | 77 | get network parameter table | NET | Requires optional NET module; absent from standard images | — |
| 4E | 78 | Reserved | SUP | Illegal; error 2 | — |
| 4F | 79 | Reserved | SUP | Illegal; error 2 | — |
| 50 | 80 | Reserved | SUP | Illegal; error 2 | — |
| 51–61 | 81–97 | Unassigned | SUP | Illegal; error 2 | — |
| 62 | 98 | Reset Alloc Vector | BDOS | Implemented | — |
| 63 | 99 | Truncate File | BDOS | Implemented | — |
| 64 | 100 | Set Dir Label | BDOS | Implemented | — |
| 65 | 101 | Return Dir Label | BDOS | Implemented | — |
| 66 | 102 | Read File XFCB | BDOS | Implemented | — |
| 67 | 103 | Write File XFCB | BDOS | Implemented | — |
| 68 | 104 | Set Date and Time | BDOS | Implemented | — |
| 69 | 105 | Get Date and Time | BDOS | Implemented | — |
| 6A | 106 | Set Default Password | BDOS | Implemented | — |
| 6B | 107 | Return Serial Number | SUP | Implemented | — |
| 6C | 108 | Get/set program return code (CP/M 3 API) | SUP | Implemented; DX=FFFFh reads the process return code, otherwise sets it; AX=BX=result, CX=0 | NEW |
| 6D | 109 | Get/Set Console Mode | CIO | Implemented | — |
| 6E | 110 | Get/Set Output Delimiter | CIO | Implemented | — |
| 6F | 111 | Print Block | CIO | Implemented | — |
| 70 | 112 | List Block | CIO | Implemented | — |
| 71 | 113 | Reserved | SUP | Illegal; error 2 | — |
| 72 | 114 | Reserved | SUP | Illegal; error 2 | — |
| 73 | 115 | Reserved | SUP | Illegal; error 2 | — |
| 74 | 116 | Set File_Date_Time | BDOS | Implemented; native stamp block plus DOS update-only form | NEW (tagged form only) |
| 75–7F | 117–127 | Unassigned | SUP | Illegal; error 2 | — |
| 80 | 128 | mem req | MEM | Implemented | — |
| 81 | 129 | (same function as 128) | MEM | Alias of 128 | — |
| 82 | 130 | mem free | MEM | Implemented | — |
| 83 | 131 | poll device | RTM | Implemented | — |
| 84 | 132 | flag wait | RTM | Implemented | — |
| 85 | 133 | flag set | RTM | Implemented | — |
| 86 | 134 | queue make | RTM | Implemented | — |
| 87 | 135 | queue open | RTM | Implemented | — |
| 88 | 136 | queue delete | RTM | Implemented | — |
| 89 | 137 | queue read | RTM | Implemented | — |
| 8A | 138 | cond. queue read | RTM | Implemented | — |
| 8B | 139 | queue write | RTM | Implemented | — |
| 8C | 140 | cond. queue write | RTM | Implemented | — |
| 8D | 141 | delay | RTM | Implemented | — |
| 8E | 142 | dispatch | RTM | Implemented | — |
| 8F | 143 | terminate | RTM | Implemented | — |
| 90 | 144 | create process | RTM | Implemented | — |
| 91 | 145 | set priority | RTM | Implemented | — |
| 92 | 146 | console attach | CIO | Implemented | — |
| 93 | 147 | console detach | CIO | Implemented | — |
| 94 | 148 | set def console | CIO | Implemented | — |
| 95 | 149 | console assign | CIO | Implemented | — |
| 96 | 150 | CLI | SUP | Implemented | — |
| 97 | 151 | call RPL | SUP | Requires matching resident procedure library | — |
| 98 | 152 | parse filename | SUP | Implemented | — |
| 99 | 153 | get def console | CIO | Implemented | — |
| 9A | 154 | sysdat addr | SUP | Implemented | — |
| 9B | 155 | time of day | SUP | Implemented | — |
| 9C | 156 | get PD addr | RTM | Implemented | — |
| 9D | 157 | abort process | RTM | Implemented | — |
| 9E | 158 | attach list | CIO | Implemented | — |
| 9F | 159 | detach list | CIO | Implemented | — |
| A0 | 160 | set list dev | CIO | Implemented | — |
| A1 | 161 | Cond. Attach list | CIO | Implemented | — |
| A2 | 162 | Cond. Attach Console | CIO | Implemented | — |
| A3 | 163 | Operating-system version | SUP | AX=BX=1441h in this build | — |
| A4 | 164 | get list dev | CIO | Implemented | — |
| A5 | 165 | AUX attach | CIO | Implemented | — |
| A6 | 166 | AUX detach | CIO | Implemented | — |
| A7 | 167 | Conditional AUX attach | CIO | Implemented | — |
| A8 / A9 | 168 / 169 | Set / get AUX device | CIO | Implemented | — |
| AA / AB | 170 / 171 | AUX input / output status | CIO | Implemented; also available as 07h/08h | — |
| AC / AD | 172 / 173 | AUX block input / output | CIO | Implemented | — |
| AE–FF | 174–255 | Unassigned (including F0h) | SUP | Illegal; error 2; no CCP/M project SETDEF extension | — |

## INT E0h / CL=32h (50 decimal) — direct BIOS gateway

Packet at DS:DX: byte selector, word CX argument, word DX argument.

| Packet selector (decimal) | Service | Status | Extension |
| --- | --- | --- | --- |
| 0 / 1 | Cold / warm boot | Terminates caller; does not reboot machine | — |
| 2 | Console status | Native console status | — |
| 3 / 4 | Console input / output | Raw CIO path | — |
| 5 | List output | Native assigned list device | — |
| 6 / 7 | AUX output / input | Implemented XIOS AUX path; direct gateway, not the CIO ownership interface | — |
| 15 | List status | XIOS list status | — |
| All others | Disk, video and other direct BIOS functions | Rejected; error 2 | — |

## PCTMP private far-call interface

This is the OEM shell/loader interface in `ms1.a86`, not an INT E0h function
and not a DOS INT 21h service. The PCTMP entry jump at code offset 3 routes
to `ms_func`; callers must locate their owning PCTMP and use its matching ABI.
CL selects the operation; DS:DX is the packet for packet operations. Results
are returned in AX/BX. Selectors 0–8 are historical; 9 and FFh are local
extensions beyond CDOS 4.1/4.11. Confirm FFh before calling 9. The range guard
now checks the number of entries; unknown selectors return FFFFh.

| CL | Service | Contract / limit |
| --- | --- | --- |
| 0 | Cleanup | PC-MODE cleanup/reset path |
| 1 | DOS program launch | Packet contains far pointer to opened FCB, far pointer to 134-byte CLI block, and user-zero flag; COM/EXE loader; paragraph-aligned MZ headers supported. No extension search or shell command parser |
| 2 | Minimum memory | DX=FFFFh queries; other values set minimum memory |
| 3 | 8087 policy | DL=FFh queries; zero/nonzero clears/sets policy bit |
| 4 | Suspend policy | DL=FFh queries; zero/nonzero clears/sets policy bit |
| 5 | Shell return code | DX=FFFFh queries; other values set; separate from DOS AH=4Dh and native function 108 |
| 6 | ORDER | DS:DX points to 13 bytes: byte 0 zero=set, nonzero=query; remaining 12 bytes are four three-character extensions |
| 7 | Built-in table address | Internal table offset returned in DX; not a standalone application service |
| 8 | Additional memory | DX=FFFFh queries; other values set additional memory |
| 9 | DOS stream configuration (NEW) | Version-1 six-word packet: version, flags, input FCB far pointer, output FCB far pointer. Flags 1=input, 2=output, 4=append, 8=echo input, 10h=echo output. AX=0 accepted; DX=0 cancels the caller’s pending request |
| FF | DOS stream capability (NEW) | AX=5244h, DX=1; historical kernels safely reject this selector |

CDOS uses this ORDER facility. The CCP/M project's E0h/F0h SETDEF packet is
**not present** here. Low-level DOS launch is not a synchronous spawn contract;
callers must manage launch selection, console reacquisition and cleanup.

## INT E6h — native XIOS compatibility entry

| AL hex | Decimal | Service | Status / return | Extension |
| --- | --- | --- | --- | --- |
| 12 | 18 | Restore normal status line | Implemented | — |
| 15 | 21 | Display supplied status line | CX:SI points to status data | — |
| 1D | 29 | Hard-disk maintenance information | Open-file flag and ROM entry | — |
| 1E | 30 | Enhanced graphics capability | Local extension: AX='EG', BX capability bits; input BX=0 for old kernels | NEW (implemented) |
| 1F | 31 | Function-key table | CX=console; returns table pointers | — |
| 20 | 32 | Maximum floppy drive | AL=result | — |
| Other | — | Unassigned selectors | No operation | — |

## Known limits and follow-up boundaries

| Area | Current limit |
| --- | --- |
| Native return status | INT E0h, CL=108. New processes start at zero. P_CHAIN transfers the word to the replacement CMD. Termination publishes the result to the surviving parent. Reads are repeatable. Fatal BDOS disk termination sets FFFDh and keyboard Ctrl-C termination sets FFFEh. |
| Serial | Native AUX and DOS 03h/04h are present; INT 14h remains firmware-owned. Hardware protocol/ownership tests are separate from this source inventory |
| DOS control calls | IOCTL supports 00h/01h/06h/07h, with 01h limited to CON. Country information uses DOS 2.x US defaults. Extended errors classify locally translated errors; unsupported services continue to report AX=1 |
| Residency | INT 27h is an IRET stub; AH=31h has a limited keep-memory path, not full TSR semantics |
| Graphics | Listed EGA/VGA modes include ROM-backed drawing and single palette/DAC entries; arbitrary pages, fonts and VESA remain unsupported |
| Raw disk | Code is enabled, unlike the CCP/M build. This inventory is not an exhaustive raw-I/O correctness test; CHS encoding and verify count remain limited |

## Sources

The tables above describe the local implementation, including project patches.
They retain the CCP/M inventory layout but do not inherit its DOS 1.x limits
or its proposed backport list. “Implemented” means a handler is present and
traced, not that every subfunction and device has passed conformance testing.

| Table / area | Local source |
| --- | --- |
| DOS 1.x and BIOS dispatch, private loader/ORDER interface | [ms1.a86](kernel/rsp3/ms1.a86) |
| DOS 2.x dispatch, handles, directories, memory and EXEC | [ms2.a86](kernel/rsp3/ms2.a86) |
| Shell selection and invocation | [tmpmenu.lib](kernel/rsp3/tmpmenu.lib), [tmpdir.lib](kernel/rsp3/tmpdir.lib) |
| Native assignments, versions and range checks | [sysdat.dat](kernel/con/sysdat.dat), [supif.sup](kernel/con/supif.sup), [sysfunc.sup](kernel/con/sysfunc.sup) |
| Native CLI | [command.sup](kernel/con/command.sup), [load.sup](kernel/con/load.sup) |
| CP/M/FAT dispatch and translated entries | [bdosif.bdo](kernel/con/bdosif.bdo), [black.a86](kernel/con/black.a86), [file3.bdo](kernel/con/file3.bdo) |
| Enabled raw-disk implementation | [pcbdos.a86](kernel/con/pcbdos.a86), [file4.bdo](kernel/con/file4.bdo) |
| AUX ownership and hardware | [aux.cio](kernel/con/aux.cio), [console.cio](kernel/con/console.cio), [xaux.lib](kernel/con/xaux.lib) |
| Video, console and keyboard | [xcon1.lib](kernel/con/xcon1.lib), [xcon2.lib](kernel/con/xcon2.lib), [xbegin.lib](kernel/con/xbegin.lib), [xchar.lib](kernel/con/xchar.lib) |
| RTC initialization and write-back | [xrtc.lib](kernel/con/xrtc.lib), [xinit.lib](kernel/con/xinit.lib) |
| Media-dependent utility contracts | [SET](commands/set/README.md), [SHOW](commands/show/README.md), [SDIR](commands/sdir/README.md) |
| DOS 2.0 internal-function assignments | [Microsoft SYSCALL.txt](https://github.com/microsoft/MS-DOS/blob/main/v2.0/source/SYSCALL.txt), [GETSET.ASM](https://github.com/microsoft/MS-DOS/blob/main/v2.0/source/GETSET.ASM) |
| Local patches | [patches.md](patches.md) |
