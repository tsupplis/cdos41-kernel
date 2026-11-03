#!/usr/bin/env python3
"""Sequential live BDOS 230/SET tests; all mutations use disposable images.

The temporary COM is only a native INT E0h probe; NASM is not a production
build dependency. Two copied kernels simulate absent and unrelated 230
handlers without modifying source or distribution binaries.
"""

from pathlib import Path
import tempfile, subprocess, re, json, sys
from historical_check import payload, symbols

R = Path(__file__).resolve().parent.parent
PROBE = r"""bits 16
cpu 8086
org 100h
push cs
pop ds
mov [packet+8],ds
mov byte [stage],'A'
call api
cmp word [packet+10],27h
jne failed
cmp word [packet+12],4146h
jne failed
mov byte [stage],'B'
mov word [packet+4],1
call api
cmp word [packet+12],20h
jne failed
mov byte [stage],'C'
mov word [packet+4],2
mov word [packet+10],2
mov word [packet+12],2
call api
cmp word [packet+12],22h
jne failed
mov byte [stage],'D'
mov word [packet+4],1
call api
cmp word [packet+12],22h
jne failed
mov byte [stage],'E'
mov word [packet+4],2
mov word [packet+10],2
mov word [packet+12],0
call api
cmp word [packet+12],20h
jne failed
mov byte [stage],'F'
mov word [packet],14
call raw
cmp ax,0ffffh
jne failed
cmp bx,ax
jne failed
cmp cx,80h
jne failed
mov word [packet],16
mov byte [stage],'G'
mov word [packet+6],cpmfcb
mov word [packet+4],1
call raw
cmp ax,0ffffh
jne failed
cmp cx,81h
jne failed
mov byte [stage],'H'
mov cx,229
xor dx,dx
int 0e0h
cmp ax,0ffffh
jne failed
cmp bx,ax
jne failed
cmp cx,2
jne failed
mov byte [stage],'I'
cmp byte [fcb],2
jne failed
mov dx,passed
mov ah,9
int 21h
mov ax,4c00h
int 21h
api:
call raw
or ax,ax
jnz failed
cmp bx,ax
jne failed
or cx,cx
jnz failed
ret
raw:
push si
push di
push bp
mov si,1234h
mov di,5678h
mov bp,9abch
mov cx,230
mov dx,packet
int 0e0h
cmp si,1234h
jne failed
cmp di,5678h
jne failed
cmp bp,9abch
jne failed
push ax
mov ax,ds
mov dx,cs
cmp ax,dx
jne failed
pop ax
pop bp
pop di
pop si
ret
failed:
mov dl,[stage]
mov ah,2
int 21h
mov dx,bad
mov ah,9
int 21h
mov ax,4c01h
int 21h
stage db 0
passed db 'BDOS 230 LIVE PASS',13,10,'$'
bad db ' BDOS 230 LIVE FAILED',13,10,'$'
packet dw 16,1,0,fcb,0,0,0,0
fcb db 2,'CHILD   TXT'
times 24 db 0a5h
cpmfcb db 1,'NOFILE  TXT'
times 24 db 0
"""
F = Path(tempfile.mkdtemp(prefix="cdos-fatattr-live-"))
print("Diagnostics:", F, flush=True)


def run(d, *args):
    return subprocess.run(args, cwd=d, check=True, capture_output=True).stdout


def root(image):
    b = image.read_bytes()
    ss = int.from_bytes(b[11:13], "little")
    start = (
        int.from_bytes(b[14:16], "little") + b[16] * int.from_bytes(b[22:24], "little")
    ) * ss
    return [
        (b[o : o + 11], b[o : o + 32])
        for o in range(start, start + int.from_bytes(b[17:19], "little") * 32, 32)
        if b[o] not in (0, 229)
    ]


def patch_kernel(d, mode):
    if mode == "normal":
        return
    run(
        d,
        "python3",
        str(R / "tools/cpm86twist.py"),
        "untwist",
        "cdos86.img",
        "logical.img",
    )
    run(d, "cpmcp", "-f", "ccpm86-320", "logical.img", "0:ccpm.sys", "kernel.sys")
    b = bytearray((d / "kernel.sys").read_bytes())
    if mode == "unrelated":
        code = payload("bdos")
        at = symbols("pcbdos")["FUNC230"]
        signature = code[at : at + 24]
        assert b.count(signature) == 1
        b[b.index(signature)] = 0xC3  # return zero without writing capability packet
    else:
        code = payload("sup")
        at = symbols("sup")["NETCHK"]
        signature = code[at : at + 24]
        assert b.count(signature) == 1, signature.hex()
        pos = b.index(signature)
        assert b[pos : pos + 3] == bytes.fromhex("80f9e6")
        b[pos + 2] = 228  # E6 now follows the old illegal-function path
    (d / "kernel.sys").write_bytes(b)
    run(d, "cpmrm", "-f", "ccpm86-320", "logical.img", "0:CCPM.SYS")
    run(d, "cpmcp", "-f", "ccpm86-320", "logical.img", "kernel.sys", "0:CCPM.SYS")
    run(
        d,
        "python3",
        str(R / "tools/cpm86twist.py"),
        "twist",
        "logical.img",
        "cdos86.img",
    )


keys = {
    " ": "Space",
    ":": "+Shift Semicolon -Shift",
    ".": "Period",
    "[": "LeftBracket",
    "]": "RightBracket",
    "=": "Equal",
    "*": "+Shift 8 -Shift",
    ",": "Comma",
    "\\": "Backslash",
}
for mode in (
    ["absent", "unrelated"]
    if "--gates" in sys.argv
    else ["normal", "absent", "unrelated"]
):
    d = F / mode
    d.mkdir()
    (d / "cdos86.img").write_bytes((R / "media/cdos86.img").read_bytes())
    (d / "diskdefs").write_bytes((R / "media/diskdefs").read_bytes())
    patch_kernel(d, mode)
    run(
        d,
        "mformat",
        "-C",
        "-i",
        "fat.img",
        "-t",
        "40",
        "-h",
        "2",
        "-n",
        "8",
        "-c",
        "2",
        "::",
    )
    (d / "one.txt").write_bytes(b"fixture\r\n\x1a")
    for name in ["ONE.TXT", "TWO.TXT"]:
        run(d, "mcopy", "-i", "fat.img", "one.txt", "::" + name)
    run(d, "mmd", "-i", "fat.img", "::SUB")
    run(d, "mcopy", "-i", "fat.img", "one.txt", "::SUB/CHILD.TXT")
    run(d, "mlabel", "-i", "fat.img", "::KEEPVOL")
    (d / "probe.asm").write_text(PROBE)
    run(d, "nasm", "-f", "bin", "probe.asm", "-o", "probe.com")
    run(d, "mcopy", "-i", "fat.img", "probe.com", "::PROBE.COM")
    run(d, "mcopy", "-i", "fat.img", "probe.com", "::SUB/PROBE.COM")
    before = dict(root(d / "fat.img"))
    if mode == "normal":
        cases = [
            ("set b:*.txt [hidden=on]", "on"),
            ("set b:*.txt [hidden=off]", "off"),
            ("set b:one.txt [ro,sys,hidden=on]", "combined"),
            ("set a:*.cmd [hidden=on]", "cpm-rejected"),
            ("chdir b:\\sub", "subdir"),
            ("b:probe.com", "probe"),
            ("set b:child.txt [hidden=on]", "subdir-on"),
        ]
    else:
        cases = [("set b:one.txt [hidden=on]", "unavailable")]
    cfg = (
        (R / "media/cdos86.cfg")
        .read_text()
        .replace('driver = "sdl"', 'driver = "null"')
        .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        .replace('file     = "cdostools.img"', 'file     = "fat.img"')
    )
    cfg = re.sub(
        r'(?m)^path\s*=\s*"([^"\n]+)"',
        lambda m: 'path = "' + str((R / "media" / m[1]).resolve()) + '"',
        cfg,
    )
    (d / "cfg").write_text(cfg)
    cmds = ["c f000000"]
    for command, label in cases:
        for text in ["cls", command]:
            for ch in text:
                cmds += ["key " + keys.get(ch, ch), "c 200000"]
            cmds += ["key Return", "c 4000000"]
        cmds += [f'save "{label}.bin" bin b800:0000 fa0']
    cmds += ["q"]
    with (d / "pce.log").open("wb") as log:
        subprocess.run(
            ["pce-ibmpc", "-c", "cfg", "-t", "null", "-g", "vga"],
            cwd=d,
            input=("\n".join(cmds) + "\n").encode(),
            stdout=log,
            stderr=log,
            check=True,
            timeout=180,
        )
    screens = {}
    for _, label in cases:
        b = (d / (label + ".bin")).read_bytes()
        screens[label] = "\n".join(
            b[o : o + 160 : 2].decode("ascii", "replace").rstrip()
            for o in range(0, 3840, 160)
        )
        (d / (label + ".txt")).write_text(screens[label])
    after = dict(root(d / "fat.img"))
    if mode == "normal":
        for label in ["on", "off", "combined", "subdir-on"]:
            assert (
                "HIDDEN=" in screens[label] and "Cannot" not in screens[label]
            ), screens[label]
        assert "HIDDEN requires DOS media" in screens["cpm-rejected"], screens[
            "cpm-rejected"
        ]
        assert "BDOS 230 LIVE PASS" in screens["probe"], screens["probe"]
        assert after[b"ONE     TXT"][11] == 0x27, after
        assert after[b"TWO     TXT"][11] == 0x20, after
        assert after[b"KEEPVOL    "] == before[b"KEEPVOL    "]
        for name in ["ONE.TXT", "TWO.TXT", "SUB/CHILD.TXT"]:
            assert run(d, "mtype", "-i", "fat.img", "::" + name) == b"fixture\r\n\x1a"
    else:
        assert "FAT attribute service unavailable" in screens["unavailable"], screens[
            "unavailable"
        ]
        assert before == after, "Unsuccessful capability query changed FAT metadata"
    print("PASS:", mode, "BDOS 230 / SET handshake and attribute behavior", flush=True)
