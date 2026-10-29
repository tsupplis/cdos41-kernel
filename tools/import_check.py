from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tempfile, shutil, subprocess, re, sys
from alias_check import ROOT as R

mode = sys.argv[1]
F = Path(tempfile.mkdtemp(prefix="cdos-" + mode + "-"))
print("Diagnostics:", F, flush=True)


def session(v):
    D = F / v
    D.mkdir()

    def run(*a):
        return subprocess.run(a, cwd=D, check=True, capture_output=True)

    shutil.copyfile(R / "media/diskdefs", D / "diskdefs")
    run(
        "python3",
        str(R / "tools/cpm86twist.py"),
        "untwist",
        str(R / "media/cdos86.img"),
        "logical.img",
    )
    for name, data in [("one.txt", b"ONE\r\n\x1a"), ("two.txt", b"TWO\r\n\x1a")]:
        (D / name).write_bytes(data)
        run("cpmcp", "-f", "ccpm86-320", "logical.img", name, "0:" + name)
    run("python3", str(R / "tools/cpm86twist.py"), "twist", "logical.img", "cdos86.img")
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
    for tool in ["systat", "ren", "era"]:
        src = (
            R / "base" / f"{tool}.cmd"
            if v == "o"
            else R / "commands" / tool / f"{tool}.cmd"
        )
        run("mcopy", "-i", "fat.img", str(src), "::" + tool + ".cmd")
    run("mcopy", "-i", "fat.img", str(R / "commands/era/eraq.cmd"), "::eraq.cmd")
    for name, data in [
        ("one.txt", b"ONE\r\n\x1a"),
        ("two.txt", b"TWO\r\n\x1a"),
        ("a.dat", b"A\x1a"),
        ("b.dat", b"B\x1a"),
        ("keep.bin", b"KEEP"),
    ]:
        (D / name).write_bytes(data)
        run("mcopy", "-i", "fat.img", name, "::" + name)
    run("mmd", "-i", "fat.img", "::adir")
    run("mcopy", "-i", "fat.img", "one.txt", "::adir/child.txt")
    cfg = (
        (R / "media/cdos86.cfg")
        .read_text()
        .replace('driver = "sdl"', 'driver = "null"')
        .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        .replace('file     = "cdostools.img"', 'file     = "fat.img"')
    )
    (D / "cdos86.cfg").write_text(cfg)
    cmds = ["c f000000"]
    keys = {
        " ": "Space",
        ".": "Period",
        "[": "LeftBracket",
        "]": "RightBracket",
        ":": "+Shift Semicolon -Shift",
        "=": "Equal",
        ",": "Comma",
        "*": "+Shift 8 -Shift",
        ";": "Semicolon",
        "\r": "Return",
        "\x03": "+Ctrl c -Ctrl",
        "\x08": "Backspace",
        "\x18": "+Ctrl x -Ctrl",
    }

    def key(k):
        cmds.extend(["key " + keys.get(k, k), "c 200000"])

    def command(text, label, answer=""):
        for c in "cls":
            key(c)
        key("\r")
        cmds.append("c 1000000")
        for c in text:
            key(c)
        key("\r")
        cmds.append("c 4000000")
        for c in answer:
            key(c)
        cmds.extend(["c 4000000", f'save "{label}.bin" bin b800:0000 fa0'])

    if mode == "systat":
        cases = [
            (f"b:systat [{o}]", "") for o in ["h", "o", "p", "u", "q", "c", "m", "z"]
        ] + [("b:systat [p c 01]", " "), ("b:systat [o c 02]", " ")]
    elif mode == "ren":
        cases = [
            ("b:ren", ""),
            ("b:ren b:new.txt=b:one.txt", ""),
            ("b:ren b:new.txt=b:two.txt", "n"),
            ("b:ren b:new.txt=b:two.txt", "y"),
            ("b:ren b:*.bak=b:*.dat", ""),
            ("b:ren b:bdir=b:adir", ""),
            ("b:ren b:x.txt=a:one.txt", ""),
            ("set a: [protect=on]", ""),
            ("set a:one.txt [password=secret,protect=read]", ""),
            ("b:ren a:new.txt=a:one.txt;wrong", "secret\r"),
            ("b:ren a:last.txt=a:new.txt;secret", ""),
            ("b:ren a:keep.txt=a:last.txt;wrong", "\x03"),
        ]
    elif mode == "era":
        cases = [
            ("b:era b:one.txt", ""),
            ("b:era b:missing.txt", ""),
            ("b:era b:*.dat", ""),
            ("b:era [bad]", ""),
            ("set a: [protect=on]", ""),
            ("set a:one.txt [password=secret,protect=delete]", ""),
            ("b:era a:one.txt;wrong", "secret\r"),
            ("b:era a:two.txt", ""),
        ]
    else:
        raise ValueError(mode)
    for i, (c, a) in enumerate(cases):
        command(c, str(i), a)
    cmds.extend(['save "ram.bin" bin 0000:0000 a0000', "q"])
    with (D / "pce.log").open("wb") as log:
        subprocess.run(
            ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
            cwd=D,
            input=("\n".join(cmds) + "\n").encode(),
            stdout=log,
            stderr=log,
            timeout=400,
            check=True,
        )
    results = []
    for i, (c, _) in enumerate(cases):
        b = (D / f"{i}.bin").read_bytes()
        s = "\n".join(
            bytes(b[j : j + 160 : 2]).decode("ascii").rstrip()
            for j in range(0, 3840, 160)
        ).rstrip()
        (D / f"{i}.txt").write_text(s)
        assert s.splitlines()[-1] == "A>", (v, c, s)
        results.append(s)
    if mode != "systat":
        b = (D / "fat.img").read_bytes()
        sz = int.from_bytes(b[11:13], "little")
        off = (
            int.from_bytes(b[14:16], "little")
            + b[16] * int.from_bytes(b[22:24], "little")
        ) * sz
        records = {}
        for a in range(off, off + int.from_bytes(b[17:19], "little") * 32, 32):
            e = b[a : a + 32]
            if e[0] not in [0, 0xE5] and e[:11].split()[0].lower() not in [
                b"systat",
                b"ren",
                b"era",
                b"eraq",
            ]:
                records[e[:11]] = (
                    e[11],
                    e[28:32],
                )  # Compare attributes/length, not placement.
        run("mcopy", "-i", "fat.img", "::keep.bin", "keep-final.bin")
        assert (D / "keep-final.bin").read_bytes() == b"KEEP"
        if mode == "ren":
            assert (
                b"NEW     TXT" in records
                and b"A       BAK" in records
                and b"B       BAK" in records
            ), records
            run("mcopy", "-i", "fat.img", "::new.txt", "new-final.txt")
            assert (D / "new-final.txt").read_bytes() == b"TWO\r\n\x1a"
        else:
            assert b"TWO     TXT" in records, records
            assert not any(
                n in records for n in [b"ONE     TXT", b"A       DAT", b"B       DAT"]
            ), records
        run(
            "python3",
            str(R / "tools/cpm86twist.py"),
            "untwist",
            "cdos86.img",
            "final.img",
        )
        b = (D / "final.img").read_bytes()
        cpnames = {
            bytes(x & 127 for x in b[a + 1 : a + 12])
            for a in range(4096, 6144, 32)
            if b[a] == 0
        }
        if mode == "ren":
            assert b"LAST    TXT" in cpnames and b"KEEP    TXT" not in cpnames, cpnames
        else:
            assert (
                b"ONE     TXT" not in cpnames and b"TWO     TXT" not in cpnames
            ), cpnames
        return results, records
    return results, {}


with ThreadPoolExecutor(2) as pool:
    out = list(pool.map(session, ["o", "n"]))
for i, (a, b) in enumerate(zip(out[0][0], out[1][0])):
    if mode == "systat":
        if i == 6:
            assert (
                "SYSTAT" in a and "SYSTAT" in b and "* FREE *" in a and "* FREE *" in b
            )
            continue
        a = re.sub(r"(Free Memory Descriptors = +)[0-9A-F]+", r"\1#", a)
        b = re.sub(r"(Free Memory Descriptors = +)[0-9A-F]+", r"\1#", b)
    assert a == b, (i, a, b)
assert out[0][1] == out[1][1], out
print(f"PASS: {mode.upper()} {len(out[0][0])} OEM/rebuilt cases", flush=True)
shutil.rmtree(F)
