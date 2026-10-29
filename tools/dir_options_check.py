#!/usr/bin/env python3
"""Check shell/BATCH DIR option spellings on CP/M and FAT media."""

from pathlib import Path
import tempfile, subprocess, shutil, re
from alias_check import ROOT as R

F = Path(tempfile.mkdtemp(prefix="cdos-dir-options-"))
print("Diagnostics:", F, flush=True)


def run(*args):
    return subprocess.run(args, cwd=F, check=True, capture_output=True)


shutil.copyfile(R / "media/diskdefs", F / "diskdefs")
run(
    "python3",
    str(R / "tools/cpm86twist.py"),
    "untwist",
    str(R / "media/cdos86.img"),
    "logical.img",
)
(F / "fixture").write_bytes(b"fixture\r\n\x1a")
for name in ["norm.tst", "sys.tst"]:
    run("cpmcp", "-f", "ccpm86-320", "logical.img", "fixture", "0:" + name)
run("cpmchattr", "-f", "ccpm86-320", "logical.img", "s", "0:sys.tst")
run("python3", str(R / "tools/cpm86twist.py"), "twist", "logical.img", "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
for name in ["norm.tst", "sys.tst", "hide.tst"]:
    run("mcopy", "-i", "fat.img", "fixture", "::" + name)
run("mattrib", "-i", "fat.img", "+s", "::sys.tst")
run("mattrib", "-i", "fat.img", "+h", "::hide.tst")
for i in range(32):
    run("mcopy", "-i", "fat.img", "fixture", f"::page{i:02}.dat")
(F / "dopts.bat").write_bytes(b"DIR B:*.TST [S]\r\n")
run("cpmcp", "-f", "ccpm86-320", "logical.img", "dopts.bat", "0:dopts.bat")
run("python3", str(R / "tools/cpm86twist.py"), "twist", "logical.img", "cdos86.img")
cfg = (
    (R / "media/cdos86.cfg")
    .read_text()
    .replace('driver = "sdl"', 'driver = "null"')
    .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
    .replace('file     = "cdostools.img"', 'file     = "fat.img"')
)
(F / "cdos86.cfg").write_text(cfg)
c = ["c f000000"]
keys = {
    " ": "Space",
    ".": "Period",
    ":": "+Shift Semicolon -Shift",
    "[": "LeftBracket",
    "]": "RightBracket",
    "*": "+Shift 8 -Shift",
    "/": "Slash",
    ",": "Comma",
}


def key(k):
    c.extend(["key " + k, "c 200000"])


def command(text, label):
    for ch in "cls":
        key(ch)
    key("Return")
    c.append("c 1000000")
    for ch in text:
        key(keys.get(ch, ch))
    key("Return")
    c.extend(["c 4000000", f'save "{label}.bin" bin b800:0000 fa0'])


cases = []
for drive in ["a", "b"]:
    for opt in ["/s", "[s]", "[s", "[s,w]", "[s w]"]:
        label = str(len(cases))
        cases.append((drive, opt, label))
        command(f"dir {drive}:*.tst {opt}", label)
    command(f"dir {drive}:*.tst", "plain-" + drive)
command("dir [s] b:*.tst", "prefix")
command("a:dopts.bat", "batch")
command("dir b:page*.dat /l [p]", "pause")
key("Space")
c.extend(["c 8000000", 'save "resumed.bin" bin b800:0000 fa0'])
command("dir b:page*.dat [l,p", "open-pause")
key("Space")
c.extend(["c 8000000", 'save "open-resumed.bin" bin b800:0000 fa0', "q"])
with (F / "pce.log").open("wb") as log:
    subprocess.run(
        ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
        cwd=F,
        input=("\n".join(c) + "\n").encode(),
        stdout=log,
        stderr=log,
        timeout=300,
        check=True,
    )
assert "unknown key:" not in (F / "pce.log").read_text(errors="replace")


def screen(name):
    b = (F / (name + ".bin")).read_bytes()
    s = "\n".join(
        bytes(b[j : j + 160 : 2]).decode("ascii", "replace").rstrip()
        for j in range(0, 3840, 160)
    )
    (F / (name + ".txt")).write_text(s)
    return s


for drive, opt, label in cases:
    s = screen(label)
    body = "\n".join(s.splitlines()[1:])
    assert re.search(r"SYS\s+TST", body), (drive, opt, s)
    assert not re.search(r"NORM\s+TST", body), (drive, opt, s)
    if drive == "b":
        assert re.search(r"HIDE\s+TST", body), (drive, opt, s)
    assert [x for x in s.splitlines() if x][-1] == "A>", s
for drive in ["a", "b"]:
    s = screen("plain-" + drive)
    body = "\n".join(s.splitlines()[1:])
    assert re.search(r"NORM\s+TST", body), s
    assert not re.search(r"SYS\s+TST", body), s
for name in ["prefix", "batch"]:
    s = screen(name)
    assert re.search(r"SYS\s+TST", s) and not re.search(r"NORM\s+TST", s), s
for a, b in [("pause", "resumed"), ("open-pause", "open-resumed")]:
    assert "Press any key to continue..." in screen(a), screen(a)
    s = screen(b)
    assert [x for x in s.splitlines() if x][-1] == "A>", s
print(
    "PASS: DIR /S, [S], [S, combined flags, prefix/suffix, DOS hidden/system and CP/M system filtering, BATCH and bracket paging",
    flush=True,
)
shutil.rmtree(F)
