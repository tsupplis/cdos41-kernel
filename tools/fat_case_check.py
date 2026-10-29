#!/usr/bin/env python3
"""Regress FAT case flags, mixed-case short names, PIP closes and ERA matching."""

from pathlib import Path
import subprocess, tempfile, shutil, os

R = Path(os.environ.get("CDOS_TEST_ROOT", Path(__file__).resolve().parent.parent))
F = Path(tempfile.mkdtemp(prefix="cdos-fat-case-"))
print("Diagnostics:", F, flush=True)


def run(*args):
    p = subprocess.run(args, cwd=F, capture_output=True, check=True)
    return p.stdout


shutil.copyfile(R / "media/diskdefs", F / "diskdefs")
run(
    "python3",
    str(R / "tools/cpm86twist.py"),
    "untwist",
    str(R / "media/cdos86base.img"),
    "logical.img",
)
run(
    "cpmcp",
    "-f",
    "ccpm86-320",
    "logical.img",
    str(R / "kernel/sysgen/ccpm.sys"),
    str(R / "commands/chdir/chdir.cmd"),
    str(R / "commands/era/era.cmd"),
    str(R / "commands/set/set.cmd"),
    "0:",
)
run("python3", str(R / "tools/cpm86twist.py"), "twist", "logical.img", "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
run("mmd", "-i", "fat.img", "::FILES")
run("mcopy", "-i", "fat.img", str(R / "commands/pip/pip4.cmd"), "::FILES/PIP.CMD")
for i in range(40):
    n = f"F{i:03}.TST"
    (F / n).write_bytes(bytes((i + j) % 256 for j in range(128)))
    run("mcopy", "-i", "fat.img", n, "::FILES/" + n)
(F / "sentinel").write_bytes(b"preserve this file\r\n")
for n in ["MIXED.TXT", "KEEP.BIN", "A@.TXT", "A`.TXT"]:
    run("mcopy", "-i", "fat.img", "sentinel", "::FILES/" + n)
# Rewrite physical 8.3 bytes as well as the modern NT case flags. Most FAT
# writers use uppercase bytes plus flags, but both representations must work.
b = bytearray((F / "fat.img").read_bytes())
w = lambda o: int.from_bytes(b[o : o + 2], "little")
root = (w(14) + b[16] * w(22)) * w(11)
data = root + w(17) * 32
cluster_size = b[13] * w(11)
fat = w(14) * w(11)


def nxt(c):
    v = w(fat + c * 3 // 2)
    return v >> 4 if c & 1 else v & 0xFFF


cluster = next(
    w(o + 26) for o in range(root, data, 32) if b[o : o + 11] == b"FILES      "
)
entries = []
while cluster < 0xFF8:
    start = data + (cluster - 2) * cluster_size
    entries.extend(range(start, start + cluster_size, 32))
    cluster = nxt(cluster)
for o in entries:
    name = bytes(b[o : o + 11])
    key = name.decode("ascii", errors="replace")
    if name == b"PIP     CMD":
        b[o : o + 11] = b"pip     cmd"
        b[o + 12] = 0x18
    elif key.startswith("F0"):
        i = int(key[1:4])
        b[o : o + 11] = name.lower() if i % 2 else name
        b[o + 12] = [0, 8, 16, 24][i % 4]
    elif name == b"MIXED   TXT":
        b[o : o + 11] = b"MiXeD   tXt"
        b[o + 12] = 0x18
(F / "fat.img").write_bytes(b)
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
    "?": "+Shift Slash -Shift",
    "=": "Equal",
    "\\": "Backslash",
    "@": "+Shift 2 -Shift",
}
cases = []


def command(s, label, cycles="3000000"):
    for ch in s:
        c.extend(["key " + keys.get(ch, ch), "c 200000"])
    c.extend(["key Return", "c " + cycles, f'save "{label}.bin" bin b800:0000 fa0'])
    cases.append(label)


command("chdir b:\\files", "chdir")
command("b:pip a:=b:*.tst[rvw", "copy", "60000000")
command("b:pip a:=b:pip.cmd[rvw", "import", "10000000")
command("a:pip a:=b:*.tst[rvw", "imported_copy", "60000000")
command("set a:pip.cmd [f4=on]", "cpm_f4")
command("set b:pip.cmd [f4=on]", "fat_f4")
command("set b:pip.cmd [f4=off]", "fat_f4_off")
command("era b:miXed.txt", "erase_exact")
command("era b:f0??.tst", "erase_wild", "10000000")
command("era b:a@.txt", "erase_punctuation")
c.append("q")
(F / "monitor.txt").write_text("\n".join(c) + "\n")
with (F / "pce.log").open("wb") as log:
    subprocess.run(
        ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
        cwd=F,
        input=("\n".join(c) + "\n").encode(),
        stdout=log,
        stderr=log,
        timeout=420,
        check=True,
    )
for label in cases:
    bscreen = (F / (label + ".bin")).read_bytes()
    screen = "\n".join(
        bytes(bscreen[i : i + 160 : 2]).decode("ascii", "replace").rstrip()
        for i in range(0, 3840, 160)
    )
    (F / (label + ".txt")).write_text(screen)
    assert "ERROR:" not in screen and "LIMIT EXCEEDED" not in screen, (label, screen)
    assert screen.rstrip().endswith("A>"), (label, screen)
run("python3", str(R / "tools/cpm86twist.py"), "untwist", "cdos86.img", "result.img")
for i in range(40):
    n = f"F{i:03}.TST"
    run("cpmcp", "-f", "ccpm86-320", "result.img", "0:" + n, "out")
    assert (F / "out").read_bytes() == (F / n).read_bytes(), n
# F4 is still supported on CP/M, and FAT SET must preserve NT case metadata.
out = (F / "result.img").read_bytes()
pip_entry = next(
    out[o : o + 32]
    for o in range(4096, 6144, 32)
    if bytes(v & 127 for v in out[o + 1 : o + 12]) == b"PIP     CMD"
)
assert pip_entry[4] & 0x80, "CP/M F4 no longer works"
after = (F / "fat.img").read_bytes()
for o in entries:
    old = bytes(b[o : o + 11])
    if (
        old.lower().startswith(b"f0")
        or old.lower() == b"mixed   txt"
        or old == b"A@      TXT"
    ):
        assert after[o] == 0xE5, (old, "not erased")
    elif old == b"A`      TXT" or old == b"KEEP    BIN":
        assert after[o : o + 32] == b[o : o + 32], (old, "sentinel changed")
    elif old.lower() == b"pip     cmd":
        assert after[o + 12] == 0x18, "FAT case bits changed"
print(
    "PASS: 40 FAT mixed-case/NT-flag copies match; ERA exact/wildcard/punctuation; CP/M F4 retained; FAT case bits preserved.",
    flush=True,
)
shutil.rmtree(F)
