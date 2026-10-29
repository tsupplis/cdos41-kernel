#!/usr/bin/env python3
"""Compare OEM SET 3.1 and the maintained build on disposable CP/M/FAT media.

Use direct console captures: PUT changes command loading in this fixture.
Each variant gets an identical disk pair; comparison includes final directory bytes.
Failed runs retain their images, screens and emulator log for diagnosis.
"""

from pathlib import Path
import subprocess, tempfile, shutil, sys, re
from alias_check import ROOT as R

F = Path(tempfile.mkdtemp(prefix="cdos-set-"))
print("SET diagnostics:", F, flush=True)


def run(*a):
    return subprocess.run(a, cwd=F, check=True, capture_output=True)


shutil.copyfile(R / "media/diskdefs", F / "diskdefs")
run(
    "python3",
    str(R / "tools/cpm86twist.py"),
    "untwist",
    str(R / "media/cdos86.img"),
    "seed.img",
)
(F / "fixture.txt").write_bytes(b"fixture\r\n\x1a")
for n in ["one.txt", "two.txt"]:
    run("cpmcp", "-f", "ccpm86-320", "seed.img", "fixture.txt", "0:" + n)
cases = [
    "[help]",
    "",
    "a:",
    "b:",
    "a:one.txt",
    "b:one.txt",
    "a:missing.txt",
    "b:missing.txt",
    "a:one.txt [ro,sys,archive=on,f1=on,f2=on,f3=on,f4=on]",
    "a:one.txt",
    "a:*.txt [rw,dir,archive=off,f1=off,f2=off,f3=off,f4=off]",
    "a:*.txt",
    "b:one.txt [ro,sys,archive=on]",
    "b:one.txt",
    "b:one.txt [rw,dir,archive=off]",
    "b:adir",
    "b:adir [ro]",
    "b: [name=test]",
    "b: [protect=on]",
    "b: [update=on]",
    "b: [default=secret]",
    "b:one.txt [password=secret]",
    "b:one.txt [protect=read]",
    "a: [name=test]",
    "a:",
    "a: [update=on]",
    "a: [create=on,access=on]",
    "a: [default=secret]",
    "a: [protect=on]",
    "a:one.txt [password=secret,protect=read]",
    "a:one.txt;secret",
    "a:one.txt;secret [protect=none]",
    "a: [default=secret]",
    "a:one.txt [password=,protect=none]",
    "a: [protect=off]",
    "[bogus]",
    "a:one.txt [f5=on]",
    "a: [ro]",
    "a: [rw]",
]

# Each variant starts from identical images. All mutations target fixtures only.
cases += [
    "[make=on]",
    "a:one.txt [protect=edit]",
    "a:one.txt [archive=maybe]",
    "a: [rx]",
    "a: [create=on]",
    "a: [access=on]",
    "a: [update=off]",
    "a: [protect=on]",
    "a:two.txt [protect=read]",
    "a:one.txt [password=secret,protect=read]",
    "a:one.txt;secret [protect=write]",
    "a:one.txt;secret [protect=delete]",
    "a:one.txt;secret [protect=none]",
    "a:one.txt [password=,protect=none]",
    "a: [protect=off]",
    "a:one.txt [ro,sys,archive=on,f1=on,f2=on,f3=on,f4=on]",
    "b:one.txt [ro,sys,archive=on]",
    "b:adir [rw]",
]
if "--stamps" in sys.argv:
    # A CP/M timestamp directory reserves every fourth slot for its SFCB.
    b = bytearray((F / "seed.img").read_bytes())
    entries = [b[a : a + 32] for a in range(4096, 6144, 32) if b[a] != 0xE5]
    assert len(entries) < 48
    b[4096:6144] = b"\xe5" * 2048
    for i, e in enumerate(entries):
        a = 4096 + (i + i // 3) * 32
        b[a : a + 32] = e
    for i in range(3, 64, 4):
        b[4096 + i * 32 : 4096 + (i + 1) * 32] = bytes([0x21]) + bytes(31)
    (F / "seed.img").write_bytes(b)
    cases = [
        "a: [name=stamps]",
        "a: [create=on]",
        "a: [update=on]",
        "a: [access=on]",
        "a: [access=off]",
        "a: [create=on,access=on]",
        "a: [create=on]",
        "a: [create=off]",
        "a: [update=off]",
        "a: [access=on]",
        "a: [access=off]",
        "a: [name=final]",
    ]
inputs = {}
if "--passwords" in sys.argv:
    cases = [
        "a: [protect=on]",
        "a:one.txt [password=secret,protect=read]",
        "a:one.txt;wrong [protect=write]",
        "a:one.txt;secret [protect=delete]",
        "a:one.txt;secret [protect=read]",
        "a: [default=secret]",
        "!type a:one.txt",
        "a:one.txt;secret [protect=none]",
        "a: [password=label]",
        "a: [name=cancelled]",
        "a: [name=changed]",
        "a: [password=,protect=off]",
        "a: [protect=off]",
    ]
    inputs = {2: "secret\r", 9: "\x03", 10: "labex\x08l\r", 11: "bad\x18label\r"}
keys = {
    " ": "Space",
    "[": "LeftBracket",
    "]": "RightBracket",
    ".": "Period",
    ",": "Comma",
    "=": "Equal",
    ";": "Semicolon",
    "*": "+Shift 8 -Shift",
    ":": "+Shift Semicolon -Shift",
}


def session(v, src):
    D = F / v
    D.mkdir()
    shutil.copyfile(F / "diskdefs", D / "diskdefs")

    def run(*a):
        return subprocess.run(a, cwd=D, check=True, capture_output=True)

    run(
        "python3",
        str(R / "tools/cpm86twist.py"),
        "twist",
        str(F / "seed.img"),
        "cdos86.img",
    )
    run(
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
    for s, n in [(R / src, "testset.cmd"), (F / "fixture.txt", "one.txt")]:
        run("mcopy", "-i", "fat.img", str(s), "::" + n)
    run("mmd", "-i", "fat.img", "::adir")
    cfg = (
        (R / "media/cdos86.cfg")
        .read_text()
        .replace('driver = "sdl"', 'driver = "null"')
        .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        .replace('file     = "cdostools.img"', 'file     = "fat.img"')
    )
    (D / "cdos86.cfg").write_text(cfg)
    cmds = ["c f000000"]
    for i, tail in enumerate(cases):
        for c in "cls":
            cmds += ["key " + c, "c 200000"]
        cmds += ["key Return", "c 2000000"]
        for c in (tail[1:] if tail.startswith("!") else f"b:testset.cmd {tail}"):
            cmds += ["key " + keys.get(c, c), "c 200000"]
        cmds += ["key Return", "c 4000000"]
        for char in inputs.get(i, ""):
            key = {
                "\r": "Return",
                "\x08": "Backspace",
                "\x18": "+Ctrl x -Ctrl",
                "\x03": "+Ctrl c -Ctrl",
            }.get(char, char)
            cmds += ["key " + key, "c 200000"]
        cmds += ["c 4000000", f'save "l{i}.bin" bin b800:0000 fa0']
    cmds += ["q"]
    with (D / "pce.log").open("wb") as log:
        subprocess.run(
            ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
            cwd=D,
            input=("\n".join(cmds) + "\n").encode(),
            stdout=log,
            stderr=log,
            timeout=450,
            check=True,
        )
    for i, tail in enumerate(cases):
        (D / f"l{i}.txt").write_bytes(bytes((D / f"l{i}.bin").read_bytes()[:3840:2]))
    print(v, "done", flush=True)


from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(2) as pool:
    list(
        pool.map(
            lambda args: session(*args),
            [("o", "base/set.cmd"), ("n", "commands/set/set.cmd")],
        )
    )


def screen(v, i):
    b = (F / v / f"l{i}.txt").read_bytes()
    rows = [b[j : j + 80].decode("ascii").rstrip() for j in range(0, len(b), 80)]
    assert [x for x in rows if x][-1] == "A>", (v, cases[i], rows)
    return "\n".join(rows).rstrip()


for i, c in enumerate(cases):
    a = screen("o", i)
    b = screen("n", i)
    norm = lambda s: re.sub(r"SET (?:2\.1|3\.1N?)", "SET #", s)
    assert norm(a) == norm(b), (i, c, a, b)
    if c.startswith("b: [") and any(x in c for x in ["name=", "protect=", "update="]):
        assert "requires CP/M media." in b, (c, b)
    if c == "a: [create=on,access=on]":
        assert "Cannot have both create and access" in b, b
    if c == "a: [default=secret]" and "Default Password set to SECRET" in b:
        assert "Enable password" not in b
    if c == "!type a:one.txt":
        assert "fixture" in b, b
    if c == "[make=on]":
        assert "Invalid Parameter" in b, b
    if c == "a:one.txt [protect=edit]" and "--passwords" not in sys.argv:
        assert "password protection first" in b, b
    if c == "a:one.txt [ro,sys,archive=on,f1=on,f2=on,f3=on,f4=on]":
        assert "read only (RO)" in b and "A1234" in b, b
    if c.endswith("[protect=write]"):
        assert "Protection = WRITE" in b, b
    if c.endswith("[protect=delete]"):
        assert "Protection = DELETE" in b, b
    if c == "a:*.txt [rw,dir,archive=off,f1=off,f2=off,f3=off,f4=off]":
        assert "A:ONE" in b and "A:TWO" in b, b
# Examine persisted directory records, independently of the command's messages.
states = []
for v in ["o", "n"]:
    D = F / v
    subprocess.run(
        [
            "python3",
            str(R / "tools/cpm86twist.py"),
            "untwist",
            "cdos86.img",
            "final.img",
        ],
        cwd=D,
        check=True,
        capture_output=True,
    )
    b = (D / "final.img").read_bytes()
    records = {}
    for a in range(4096, 6144, 32):
        e = b[a : a + 32]
        name = bytes(x & 127 for x in e[1:12])
        if e[0] in (0, 0x20) and (
            name in (b"ONE     TXT", b"TWO     TXT") or e[0] == 0x20
        ):
            records[(e[0], name)] = e[:24]  # Label timestamps follow byte 23.
    if "--stamps" not in sys.argv and "--passwords" not in sys.argv:
        one = records[(0, b"ONE     TXT")]
        two = records[(0, b"TWO     TXT")]
        assert all(one[x] & 128 for x in [1, 2, 3, 4, 9, 10, 11]), one
        assert all(not two[x] & 128 for x in [1, 2, 3, 4, 9, 10, 11]), two
    fat = (D / "fat.img").read_bytes()
    sector = int.from_bytes(fat[11:13], "little")
    root = (
        int.from_bytes(fat[14:16], "little")
        + fat[16] * int.from_bytes(fat[22:24], "little")
    ) * sector
    attrs = {}
    for a in range(root, root + int.from_bytes(fat[17:19], "little") * 32, 32):
        e = fat[a : a + 32]
        if e[:11] in [b"ONE     TXT", b"ADIR       "]:
            attrs[e[:11]] = e[11]
    if "--stamps" not in sys.argv and "--passwords" not in sys.argv:
        assert (
            attrs[b"ONE     TXT"] & 0x27 == 0x05
        ), attrs  # CP/M archived clears DOS archive-needed; system + RO
        assert attrs[b"ADIR       "] == 0x30, attrs
    states.append((records, attrs))
assert states[0] == states[1], states
print(
    f"PASS: SET {len(cases)} OEM/rebuilt cases and persisted CP/M/FAT attributes"
    + (" with formatted timestamps" if "--stamps" in sys.argv else "")
)
shutil.rmtree(F)
