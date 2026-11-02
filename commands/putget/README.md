# PUT / GET / RDR: Console I/O Redirection for Concurrent DOS 4.1

Bracket-style console redirection for native CMD and DOS COM/EXE programs under Concurrent DOS 4.1, imported from the CCP/M-86 project.

| Command | Effect |
| --- | --- |
| `PUT [out{,A}{,E\|EO}] cmd` | Capture the program's console output in `out` |
| `GET [in{,E\|EI}] cmd` | Feed the program's console input from `in` |
| `RDR [in,out{,A}{,E\|EI\|EO}] cmd` | Both at once |

Flags: `A` appends to the output file, `E` echoes both streams to the screen, `EO` echoes output only, `EI` echoes input only.

```text
A>PUT [BUILD.LOG,A,EO] ASM86 MYPROG
A>GET [SCRIPT.IN] PIP
A>RDR [KEYS.IN,PIP.LOG] PIP
```

## Scope and limits

| Target | Redirected interface |
| --- | --- |
| Native CMD | BDOS console input/output, through the existing INT E0 hook |
| DOS COM/EXE | Standard handles 0/1, including legacy INT 21h console calls |
| Shell built-ins, BIOS video, direct screen access, explicit CON | Outside these streams |

Use `DIR.CMD`, `SDIR.CMD` or `TYPE.CMD` for native command capture. Command
selection follows PCTMP ORDER; explicit extensions are honored. The DOS
adapter searches the current location, then eligible SYS files on the system
drive/current user or user zero. DOS support requires this project's patched
PCTMP; the versioned capability probe safely rejects historical kernels.

DOS input is byte-exact: NUL and Ctrl-Z are data, block reads return count zero
at EOF, and buffered line input returns an empty line. CR/LF works across
successive line reads. DOS append uses the logical byte length. Echo goes to
the console, and stderr remains on handle 2. Descendant DOS EXEC calls inherit
the handles and echo settings; exit restores the parent bindings. Applications
must honor EOF. Native text-record input/append behavior is described below.

The native hook filters by virtual console, so it can intercept other native
processes sharing that console while active. DOS handles belong to the launched
process hierarchy. Both paths keep other consoles' streams independent.
The DOS root loader supports paragraph-aligned EXE headers. These wrappers
do not add shell `<`, `>` or `|`.

## DOS ownership and launch

The shared `dosredir.lib` locates PCTMP and queries its ORDER table. Private
selector FFh must return AX=5244h, DX=1 before selector 9 is used. Selector 9
copies parsed filenames into a pending request owned by the caller's process
descriptor; selector 1 consumes that request when launching the DOS child.
PCTMP opens and binds files after DOS initialization, in the child's process.
The CMD installs no hook for DOS and retains no DOS handle. The kernel keeps
no pointer or callback into the CMD. The wrapper reacquires the console,
performs existing PCTMP cleanup and cancels unused requests on failure.

The packet and internal ownership contract are documented in
[patches.md](../../patches.md) and [api.md](../../api.md). Kernel changes stay
within the existing MS1/MS2 PCTMP component; no helper executable or sibling
project is required.

## Native CMD path

1. `init_environment` checks BDOS 12 (BH = 11h or 14h, as SUBMIT does), saves the SYSDAT segment, raises priority one level above the parent and records the console number (BDOS 153).
2. The bracket prefix is parsed; file names go through BDOS 152 into FCBs. Input is opened (BDOS 15). Output is deleted and created, or opened and positioned at the first `1Ah` for `A` (BDOS 35 and 33).
3. The `INT E0h` vector (`0000:0380h`) is replaced by `int_e0_hook`. The hook runs on its own stack and saves and restores the child's DMA address and segment (BDOS 52 and 51).
4. The child is started with `p_cli` (BDOS 150), and the tool waits with BDOS 146 until the console is released.
5. The hook is removed, the last partial record is padded with `1Ah` and written, and the files are closed.

Trapped calls, only when the running process's console is ours:

| BDOS call | Redirected side |
| --- | --- |
| 2 Console Output, 6 Direct I/O (output), 9 Print String | output |
| 1 Console Input, 6 Direct I/O (`DL`=FDh/FFh), 10 Read Buffer, 11 Console Status; 6 Direct Status (`DL`=FEh) | input |

Details:

* Output is written with random writes (BDOS 34) and a record counter. Screen echo calls BDOS 2 with `in_interceptor` set, so the hook does not capture its own echo.
* Input is read in 128-byte records. At `1Ah` or end of file, `trap_readbuf` returns an empty line, which ends programs that quit on an empty line (PIP does). Any later input call goes to the keyboard. An input file should therefore contain everything the program needs, including its exit. The PCE regression supplies a PIP copy line followed by an empty line, then checks the destination bytes and return to the shell.
* `p_cns` is at PD offset `20h` (see `kernel/con/pd.def`).

## Files

```
commands/putget/
├── Makefile       # builds put.cmd get.cmd rdr.cmd
├── put.a86        # PUT front end
├── get.a86        # GET front end
├── rdr.a86        # RDR front end
├── putget.lib     # shared engine: environment, parsing, files, hook, traps
├── dosredir.lib   # shared DOS resolution and PCTMP launch adapter
├── putget.dat     # shared data buffers (one copy, included at org 100h)
├── putget.def     # constants; `debug equ 0` gates the BDOS call logger
└── README.md
```

The tools are shipped on `cdostools.img`, alongside PIP.
`make check-redirection` runs native CMD and DOS stream/error-recovery tests on
disposable CP/M and FAT disks. `make check-pctmp-live` also checks nested EXEC
and Ctrl-C return. NASM builds test fixtures only; production commands use ASM86.

## 4.1 adaptation

The shared engine recognizes all three BDOS 6 input/status selectors: FDh
(blocking input), FEh (status), and FFh (input if ready). The imported engine
recognized only FFh; PIP uses FDh after checking console status, so GET would
otherwise wait on the keyboard during a copy. Output handling remains unchanged.

The DOS adapter adds standard-handle routing without changing the native hook.
