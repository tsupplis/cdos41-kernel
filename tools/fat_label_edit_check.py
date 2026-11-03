#!/usr/bin/env python3
"""Live FAT label editing on disposable disks; NASM builds only a test probe."""

from pathlib import Path
import tempfile, subprocess, re, json

R = Path(__file__).resolve().parent.parent
DOS_PROBE = r"""bits 16
cpu 8086
org 100h
push cs
pop ds
cld
mov ah,1ah
mov dx,dta
int 21h
mov byte [stage],66
mov dx,filefcb
mov ah,0fh
int 21h
cmp al,0
jne failed
mov byte [stage],67
mov dx,subpath
mov ah,3bh
int 21h
jc failed
mov byte [stage],68
mov dx,label
mov ah,16h
int 21h
cmp al,0
jne failed
mov byte [stage],69
mov dx,label
mov ah,10h
int 21h
cmp al,0
jne failed
mov byte [stage],70
mov dx,label
mov ah,14h
int 21h
or al,al
jz failed
mov byte [stage],71
mov dx,filefcb
mov ah,14h
int 21h
cmp al,3
je partial_file_ok
or al,al
jnz failed
partial_file_ok:
cmp word [dta],'KE'
jne failed
mov byte [stage],72
mov dx,filefcb
mov ah,10h
int 21h
mov byte [stage],73
mov dx,duplicate
mov ah,16h
int 21h
cmp al,0ffh
jne failed
mov byte [stage],74
mov dx,renamefcb
mov ah,17h
int 21h
or al,al
jnz failed
mov dx,dta
mov ah,1ah
int 21h
mov byte [stage],75
mov dx,mask
mov cx,8
mov ah,4eh
int 21h
jc failed
mov si,dta+30
mov di,expected
compare:
lodsb
cmp al,[di]
jne failed
inc di
or al,al
jnz compare
mov byte [stage],76
mov dx,wrong
mov ah,13h
int 21h
cmp al,0ffh
jne failed
mov byte [stage],77
mov dx,deleted
mov ah,13h
int 21h
or al,al
jnz failed
mov byte [stage],78
mov dx,mask
mov cx,8
mov ah,4eh
int 21h
jnc failed
mov byte [stage],79
mov dx,handlepath
mov cx,8
mov ah,3ch
int 21h
jnc failed
cmp ax,5
jne failed
mov dx,ok
mov ah,9
int 21h
mov ax,4c00h
int 21h
failed:
mov dl,[stage]
mov ah,2
int 21h
mov dx,bad
mov ah,9
int 21h
mov ax,4c01h
int 21h
stage db '0'
subpath db 'B:\SUB',0
mask db 'B:\*.*',0
handlepath db 'B:\ILLEGAL',0
expected db 'LABNEW',0
ok db 'DOS LABEL OPERATIONS PASS',13,10,'$'
bad db 'DOS LABEL OPERATIONS FAILED',13,10,'$'
filefcb db 2,'LABONE     '
times 25 db 0
label db 255,0,0,0,0,0,8,2,'LABONE     '
times 25 db 0
duplicate db 255,0,0,0,0,0,8,2,'LABTWO     '
times 25 db 0
renamefcb db 255,0,0,0,0,0,8,2,'LABONE     '
times 4 db 0
db 0,'LABNEW     '
times 9 db 0
wrong db 255,0,0,0,0,0,8,2,'NOTHERE    '
times 25 db 0
deleted db 255,0,0,0,0,0,8,2,'LABNEW     '
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


keys = {
    " ": "Space",
    ":": "+Shift Semicolon -Shift",
    ".": "Period",
    "[": "LeftBracket",
    "]": "RightBracket",
    "=": "Equal",
    "*": "+Shift 8 -Shift",
    "\\": "Backslash",
    '"': "+Shift Quote -Shift",
}
results = {}
for variant in ["last"]:
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
    (d / "one.txt").write_bytes(b"fixture\r\n\x1a")
    run(d, "mcopy", "-i", "fat.img", "one.txt", "::FIRST.TXT")
    run(d, "mmd", "-i", "fat.img", "::SUB")
    run(d, "mcopy", "-i", "fat.img", "one.txt", "::SUB/CHILD.TXT")
    (d / "ops.asm").write_text(DOS_PROBE)
    run(d, "nasm", "-f", "bin", "ops.asm", "-o", "ops.com")
    run(d, "mcopy", "-i", "fat.img", "ops.com", "::OPS.COM")
    (d / "keep").write_bytes(b"KEEP NORMAL FILE\r\n")
    run(d, "mcopy", "-i", "fat.img", "keep", "::LABONE")
    image_before = (d / "fat.img").read_bytes()
    sector_size = int.from_bytes(image_before[11:13], "little")
    fat_start = int.from_bytes(image_before[14:16], "little") * sector_size
    fat_end = (
        fat_start
        + image_before[16] * int.from_bytes(image_before[22:24], "little") * sector_size
    )
    fat_before = image_before[fat_start:fat_end]
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
        ('set b: [name="my disk"]', "spaces"),
        ("show b:label", "spaces-show"),
        ("set b: [name=abcdefghijkl]", "too-long"),
        ("show b:label", "after-invalid"),
        ("set b: [name=nochange,update=on]", "metadata-rejected"),
        ("show b:label", "after-metadata"),
        ("set b: [name=]", "delete"),
        ("b:ops.com", "dos"),
        ("show b:label", "afterdos"),
        ("dir b:", "subdir"),
        ("set b: [name=final]", "final"),
        ("show b:label", "final-show"),
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
    after = root_entries(d / "fat.img")
    (d / "after.json").write_text(json.dumps(after, indent=2))
    assert "Volume label for drive B: MY DISK" in screens["spaces"], screens["spaces"]
    assert "MY DISK" in screens["spaces-show"], screens["spaces-show"]
    assert "MY DISK" in screens["after-invalid"], screens["after-invalid"]
    assert "MY DISK" in screens["after-metadata"], screens["after-metadata"]
    assert "(none)" in screens["delete"], screens["delete"]
    assert "DOS LABEL OPERATIONS PASS" in screens["dos"], screens["dos"]
    assert "No volume label exists" in screens["afterdos"], screens["afterdos"]
    assert "CHILD" in screens["subdir"], screens["subdir"]
    assert "FINAL" in screens["final-show"], screens["final-show"]
    assert [e["name"] for e in after if e["attribute"] == 8] == ["FINAL      "], after
    assert (d / "fat.img").read_bytes()[
        fat_start:fat_end
    ] == fat_before, "Label operations changed FAT allocation"
    assert run(d, "mtype", "-i", "fat.img", "::LABONE") == b"KEEP NORMAL FILE\r\n"
    assert run(d, "mtype", "-i", "fat.img", "::SUB/CHILD.TXT") == b"fixture\r\n\x1a"
    results[variant] = {"before": before, "after": after, "screens": screens}
    print(
        "PASS: native and DOS label editing, duplicate rejection, same-name file protection, root targeting from a subdirectory and unchanged allocation",
        flush=True,
    )
(F / "results.json").write_text(json.dumps(results, indent=2))
