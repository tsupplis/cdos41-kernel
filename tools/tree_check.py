#!/usr/bin/env python3
"""DOS Plus-style TREE on disposable FAT and CP/M media."""

from pathlib import Path
import shutil, subprocess, re, tempfile

R = Path(__file__).resolve().parent.parent
F = Path(tempfile.mkdtemp(prefix="cdos-tree-"))
print("Diagnostics:", F, flush=True)


def run(*a):
    return subprocess.run(a, cwd=F, capture_output=True, check=True)


shutil.copyfile(R / "media/diskdefs", F / "diskdefs")
run(
    "python3",
    str(R / "tools/cpm86twist.py"),
    "untwist",
    str(R / "media/cdos86.img"),
    "a.logical",
)
run("cpmrm", "-f", "ccpm86-320", "a.logical", "0:ED.CMD", "0:SDIR.CMD")
run(
    "cpmcp",
    "-f",
    "ccpm86-320",
    "a.logical",
    str(R / "commands/tree/tree.cmd"),
    "0:TREE.CMD",
)
run("python3", str(R / "tools/cpm86twist.py"), "twist", "a.logical", "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
for d in ["SUB", "EMPTY", "SUB/DEEP"]:
    run("mmd", "-i", "fat.img", "::" + d)
for name, size in [
    ("ROOT.TXT", 123),
    ("SUB/ONE.DAT", 1000),
    ("SUB/DEEP/TWO.DAT", 37),
    ("SUB/HIDE.DAT", 7),
    ("SUB/BIG.DAT", 70000),
    ("SUB/SYSTEM.DAT", 17),
]:
    (F / "fixture").write_bytes(b"x" * size)
    run("mcopy", "-i", "fat.img", "fixture", "::" + name)
run("mattrib", "-i", "fat.img", "+h", "::SUB/HIDE.DAT")
run("mattrib", "-i", "fat.img", "+s", "::SUB/SYSTEM.DAT")
cfg = (
    (R / "media/cdos86.cfg")
    .read_text()
    .replace('driver = "sdl"', 'driver = "null"')
    .replace("sdl:lowpass=5000", "null")
    .replace("cdostools.img", "fat.img")
)
cfg = re.sub(
    r'(?m)^path\s*=\s*"([^"\n]+)"',
    lambda m: 'path = "' + str((R / "media" / m[1]).resolve()) + '"',
    cfg,
)
(F / "test.cfg").write_text(cfg)
commands = ["c f000000"]
keys = {
    ":": "+Shift Semicolon -Shift",
    " ": "Space",
    ".": "Period",
    "[": "LeftBracket",
    "]": "RightBracket",
    "\\": "Backslash",
}
for text, label in [
    ("cls", "clear"),
    ("tree b:", "tree"),
    ("cls", "clear2"),
    ("tree a:", "cpm"),
    ("chdir b:\\sub", "location"),
    ("cls", "clear3"),
    ("tree b:", "private"),
    ("dir b:one.dat", "retained"),
]:
    for ch in text + "\n":
        commands += ["key " + ({"\n": "Return"}.get(ch, keys.get(ch, ch))), "c 200000"]
    commands += ["c 10000000", f'save "{label}.bin" bin b800:0000 fa0']
commands += ["q"]
with (F / "pce.log").open("wb") as log:
    subprocess.run(
        ["pce-ibmpc", "-c", "test.cfg", "-t", "null", "-g", "vga"],
        cwd=F,
        input=("\n".join(commands) + "\n").encode(),
        stdout=log,
        stderr=log,
        timeout=60,
        check=True,
    )
screens = {}
for label in ["tree", "cpm", "private", "retained"]:
    b = (F / (label + ".bin")).read_bytes()
    s = "\n".join(
        bytes(b[i : i + 160 : 2]).decode("latin1").rstrip() for i in range(0, 3840, 160)
    )
    print(label + "\n" + s)
    (F / (label + ".txt")).write_text(s)
    screens[label] = s

rows = []
for line in screens["tree"].splitlines():
    m = re.match(r"\s*([0-9,]+)\s+([0-9,]+)\s+(B:\\.*)", line)
    if m:
        rows.append((int(m[1].replace(",", "")), int(m[2].replace(",", "")), m[3]))
assert rows == [
    (123, 1, "B:\\"),
    (71024, 4, "B:\\SUB"),
    (37, 1, "B:\\SUB\\DEEP"),
    (0, 0, "B:\\EMPTY"),
], rows
assert "TREE requires a DOS/FAT disk." in screens["cpm"]
assert (
    "ONE" in screens["retained"] and "File not found" not in screens["retained"]
), screens["retained"]
assert screens["private"].rstrip().endswith("A>"), screens["private"]
print(
    "PASS: TREE FAT statistics, hidden files, nested/empty directories, CP/M rejection and private directory mapping"
)
shutil.rmtree(F)
