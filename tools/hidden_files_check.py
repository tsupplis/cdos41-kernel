#!/usr/bin/env python3
"""HIDDEN/SYSTEM integration checks on one disposable PCE at a time."""

from pathlib import Path
import json, re, subprocess, sys, tempfile

R = Path(__file__).resolve().parent.parent


def run(d, *args):
    result = subprocess.run(args, cwd=d, capture_output=True)
    if result.returncode:
        raise RuntimeError((args, result.stderr.decode(errors="replace")))
    return result.stdout


def entries(image):
    b = image.read_bytes()
    sector = int.from_bytes(b[11:13], "little")
    start = (
        int.from_bytes(b[14:16], "little") + b[16] * int.from_bytes(b[22:24], "little")
    ) * sector
    return {
        b[o : o + 11]: b[o : o + 32]
        for o in range(start, start + int.from_bytes(b[17:19], "little") * 32, 32)
        if b[o] not in [0, 229]
    }


def fixture(prefix):
    d = Path(tempfile.mkdtemp(prefix=prefix))
    print("Diagnostics:", d, flush=True)
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
    (d / "data").write_bytes(b"KEEP CONTENT\r\n\x1a")
    for name, attribute in [
        ("N.TXT", ""),
        ("H.TXT", "+h"),
        ("S.TXT", "+s"),
        ("SH.TXT", "+s +h"),
        ("RO.TXT", "+r"),
        ("HR.TXT", "+h +r"),
        ("Q.TXT", "+h"),
        ("W1.DAT", "+h"),
        ("W2.DAT", "+s"),
    ]:
        run(d, "mcopy", "-i", "fat.img", "data", "::" + name)
        if attribute:
            run(d, "mattrib", "-i", "fat.img", *attribute.split(), "::" + name)
    run(d, "mmd", "-i", "fat.img", "::SUB")
    run(d, "mlabel", "-i", "fat.img", "::KEEPVOL")
    return d


def session(d, cases):
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
    keys = {
        " ": "Space",
        ":": "+Shift Semicolon -Shift",
        ".": "Period",
        "[": "LeftBracket",
        "]": "RightBracket",
        "=": "Equal",
        "*": "+Shift 8 -Shift",
        ",": "Comma",
        "-": "Minus",
        "/": "Slash",
        "\\": "Backslash",
    }
    commands = ["c f000000"]

    def text(value):
        for ch in value:
            commands.extend(["key " + keys.get(ch, ch), "c 200000"])

    for command, label, answer in cases:
        text("cls")
        commands.extend(["key Return", "c 2000000"])
        text(command)
        commands.extend(["key Return", "c 4000000"])
        if answer:
            text(answer)
            commands.append("c 4000000")
        commands.append(f'save "{label}.bin" bin b800:0000 fa0')
    commands.append("q")
    with (d / "pce.log").open("wb") as log:
        subprocess.run(
            ["pce-ibmpc", "-c", "cfg", "-t", "null", "-g", "vga"],
            cwd=d,
            input=("\n".join(commands) + "\n").encode(),
            stdout=log,
            stderr=log,
            check=True,
            timeout=180,
        )
    screens = {}
    for _, label, _ in cases:
        b = (d / (label + ".bin")).read_bytes()
        screens[label] = "\n".join(
            b[o : o + 160 : 2].decode("ascii", "replace").rstrip()
            for o in range(0, 3840, 160)
        )
        (d / (label + ".txt")).write_text(screens[label])
    return screens


def deletion():
    d = fixture("cdos-hidden-delete-")
    before = entries(d / "fat.img")
    cases = [
        ("era b:h.txt", "hidden", ""),
        ("era b:s.txt", "system", ""),
        ("era b:sh.txt", "both", ""),
        ("era b:*.dat", "wild", ""),
        ("era b:hr.txt", "readonly", ""),
        ("eraq b:q.txt", "query", "y"),
        ("ren b:new.txt=b:n.txt", "rename", ""),
    ]
    screens = session(d, cases)
    after = entries(d / "fat.img")
    for name in [
        b"H       TXT",
        b"S       TXT",
        b"SH      TXT",
        b"W1      DAT",
        b"W2      DAT",
        b"Q       TXT",
    ]:
        assert name not in after, (name, screens)
    for name in [b"RO      TXT", b"HR      TXT", b"KEEPVOL    ", b"SUB        "]:
        assert after[name] == before[name], (name, after.get(name), before[name])
    assert b"N       TXT" not in after and b"NEW     TXT" in after, after
    assert run(d, "mtype", "-i", "fat.img", "::NEW.TXT") == b"KEEP CONTENT\r\n\x1a"
    print(
        "PASS: ERA/ERAQ exact/wildcard HIDDEN/SYSTEM deletion, RO protection, label/directory preservation and rename",
        flush=True,
    )


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "delete":
        deletion()
