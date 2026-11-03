#!/usr/bin/env python3
"""Exercise FAT labels through native commands and DOS on disposable images.

NASM assembles only the temporary read-only DOS probe. SET attribute/label
requests operate exclusively on disposable FAT images. All 32 bytes of every
real volume entry are compared before/after to protect it from file access.
"""

from pathlib import Path
import tempfile, subprocess, re, json, hashlib

R = Path(__file__).resolve().parent.parent
DOS_PROBE = r"""bits 16
cpu 8086
org 100h
push cs
pop ds
mov dx,dta
mov ah,1ah
int 21h
mov dx,mask
mov cx,8
mov ah,4eh
int 21h
jc no_label
mov dx,found
mov ah,9
int 21h
mov si,dta+30
call puts
mov ah,4fh
int 21h
jnc repeated
mov dx,once
jmp print_status
no_label:
mov dx,absent
jmp print_status
repeated:
mov dx,repeat_error
print_status:
mov ah,9
int 21h
mov dx,fcb
mov ah,0fh
int 21h
cmp al,0ffh
jne opened
mov dx,denied
jmp print_open
opened:
mov dx,open_error
print_open:
mov ah,9
int 21h
mov ax,4c00h
int 21h
puts:
lodsb
or al,al
jz puts_done
mov dl,al
mov ah,2
int 21h
jmp puts
puts_done:
mov dx,newline
mov ah,9
int 21h
ret
mask db 'B:\*.*',0
found db 'LABEL=$'
once db 'LABEL FIND-NEXT: end',13,10,'$'
absent db 'LABEL: absent',13,10,'$'
repeat_error db 'ERROR: repeated label',13,10,'$'
denied db 'LABEL OPEN: denied',13,10,'$'
open_error db 'ERROR: label opened as file',13,10,'$'
newline db 13,10,'$'
fcb db 2,'DOSVOL     '
times 25 db 0
dta times 128 db 0
"""
F = Path(tempfile.mkdtemp(prefix="cdos-label-assess-"))
print("Disposable evidence:", F, flush=True)


def run(folder, *args):
    return subprocess.run(args, cwd=folder, check=True, capture_output=True).stdout


def root_entries(path):
    b = path.read_bytes()
    ss = int.from_bytes(b[11:13], "little")
    start = (
        int.from_bytes(b[14:16], "little") + b[16] * int.from_bytes(b[22:24], "little")
    ) * ss
    out = []
    for n in range(int.from_bytes(b[17:19], "little")):
        o = start + n * 32
        e = b[o : o + 32]
        if e[0] == 0:
            break
        if e[0] != 0xE5:
            out.append(
                {
                    "slot": n,
                    "name": e[:11].decode("ascii", "replace"),
                    "attribute": e[11],
                }
            )
    return out


def label_bytes(path):
    b = path.read_bytes()
    ss = int.from_bytes(b[11:13], "little")
    root = (
        int.from_bytes(b[14:16], "little") + b[16] * int.from_bytes(b[22:24], "little")
    ) * ss
    return [
        b[o : o + 32]
        for n in range(int.from_bytes(b[17:19], "little"))
        if (o := root + n * 32) and b[o] not in [0, 229] and b[o + 11] == 8
    ]


keys = {
    " ": "Space",
    ":": "+Shift Semicolon -Shift",
    ".": "Period",
    "[": "LeftBracket",
    "]": "RightBracket",
    "=": "Equal",
    "*": "+Shift 8 -Shift",
    "\\": "Backslash",
}
results = {}
for variant in ["none", "first", "last"]:
    d = F / variant
    d.mkdir()
    (d / "cdos86.img").write_bytes((R / "media/cdos86.img").read_bytes())
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
    if variant == "first":
        run(d, "mlabel", "-i", "fat.img", "::DOSVOL")
    (d / "one.txt").write_bytes(b"fixture\r\n\x1a")
    run(d, "mcopy", "-i", "fat.img", "one.txt", "::FIRST.TXT")
    run(d, "mmd", "-i", "fat.img", "::SUB")
    run(d, "mcopy", "-i", "fat.img", "one.txt", "::SUB/CHILD.TXT")
    if variant == "last":
        run(d, "mlabel", "-i", "fat.img", "::DOSVOL")
    (d / "probe.asm").write_text(DOS_PROBE)
    run(d, "nasm", "-f", "bin", "probe.asm", "-o", "probe.com")
    run(d, "mcopy", "-i", "fat.img", "probe.com", "::PROBE.COM")
    before_label = label_bytes(d / "fat.img")
    before = root_entries(d / "fat.img")
    (d / "before.json").write_text(json.dumps(before, indent=2))
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
    cases = [
        ("dir b:", "dir"),
        ("dir.cmd b:", "external-dir"),
        ("sdir b:", "sdir"),
        ("show b:label", "show-label"),
        ("set b:dosvol [ro,sys]", "set-label-file"),
        ("set b:*.* [ro,sys]", "set-files"),
        ("chdir b:\\sub", "chdir"),
        ("dir b:", "subdir-dir"),
        ("sdir b:", "subdir-sdir"),
        ("show b:label", "subdir-show"),
        ("chdir b:\\", "root"),
        ("b:probe.com", "dos-label"),
    ]
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
    for command, label in cases:
        b = (d / (label + ".bin")).read_bytes()
        s = "\n".join(
            bytes(b[o : o + 160 : 2]).decode("ascii", "replace").rstrip()
            for o in range(0, 3840, 160)
        )
        (d / (label + ".txt")).write_text(s)
        screens[label] = s.rstrip()
    assert (
        label_bytes(d / "fat.img") == before_label
    ), "SET modified a volume-label entry"
    after = root_entries(d / "fat.img")
    (d / "after.json").write_text(json.dumps(after, indent=2))
    results[variant] = {"before": before, "after": after, "screens": screens}

    assert "DOSVOL" not in screens["sdir"], screens["sdir"]
    assert not any(
        "DOSVOL" in text.split("\n", 1)[-1]
        for name, text in screens.items()
        if name in ["dir", "external-dir"]
    ), screens
    if variant != "none":
        assert "LABEL=DOSVOL" in screens["dos-label"], screens["dos-label"]
        assert "LABEL FIND-NEXT: end" in screens["dos-label"], screens["dos-label"]
    else:
        assert "LABEL: absent" in screens["dos-label"], screens["dos-label"]
    assert "LABEL OPEN: denied" in screens["dos-label"], screens["dos-label"]

    for topic in ["show-label", "subdir-show"]:
        expected = "No volume label exists" if variant == "none" else "DOSVOL"
        assert expected in screens[topic], screens[topic]
    assert "File not found" in screens["set-label-file"], screens["set-label-file"]
    assert re.search(r"Files Found = +2\b", screens["sdir"]), screens["sdir"]
    print(
        "PASS:",
        variant,
        "label: DIR/SDIR filtering, DOS first/next/open, SET full-entry preservation and root-label SHOW display",
        flush=True,
    )
(F / "results.json").write_text(json.dumps(results, indent=2))
