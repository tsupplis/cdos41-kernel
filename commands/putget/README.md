# PUT / GET / RDR: Console I/O Redirection for Concurrent DOS 4.1

Bracket-style console redirection for native programs under Concurrent DOS 4.1, imported from the CCP/M-86 project.

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

* **Works for native `.CMD` programs.** Verified on disposable PCE floppy images: multi-record output capture, append, GET feeding a PIP copy command, RDR feeding PIP and capturing its output, exact copied bytes and return to the shell.
* **DOS programs (`.COM`, `.EXE`) are outside this interface.** BDOS 150 (`p_cli`) launches native CMD programs. The DOS personality uses a saved kernel entry (`BDOS_PTR` in MS1), bypassing the `INT E0h` hook installed here.
* **Shell built-ins are outside this interface**, including DIR, CLS, USER and PAUSE. Run a native command such as `DIR.CMD`, `SDIR.CMD` or `TYPE.CMD` explicitly.
* **Only the caller's virtual console is affected.** The hook filters on the console number of the running process; it does not track descendants by `p_parent`. Any process on that console is captured while the tool runs.

## How it works

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
├── putget.dat     # shared data buffers (one copy, included at org 100h)
├── putget.def     # constants; `debug equ 0` gates the BDOS call logger
└── README.md
```

The tools are shipped on the bootable `cdos86.img`, alongside PIP. Run `make check-redirection` at the project root for the disposable-floppy regression.

## 4.1 adaptation

The shared engine recognizes all three BDOS 6 input/status selectors: FDh
(blocking input), FEh (status), and FFh (input if ready). The imported engine
recognized only FFh; PIP uses FDh after checking console status, so GET would
otherwise wait on the keyboard during a copy. Output handling remains unchanged.

DOS redirection would require separate integration with the DOS personality's
console and standard-handle paths.
