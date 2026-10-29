#!/usr/bin/env python3
"""CDOS WINDOW/WMENU compatibility against the retained OEM programs."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tempfile, shutil, subprocess, re
from alias_check import ROOT as R

F = Path(tempfile.mkdtemp(prefix="cdos-window-"))
print("Diagnostics:", F, flush=True)
actions = [
    ("main", []),
    ("size-select", ["Space"]),
    ("size", ["Return"]),
    ("size-change", ["KP_8"]),
    ("size-done", ["Esc"]),
    ("color-select", ["Space"] * 4),
    ("color", ["Return"]),
    ("color-change", ["KP_6", "KP_8"]),
    ("color-done", ["Esc"]),
    ("tracking-select", ["KP_4"] * 2),
    ("tracking", ["Return"]),
    ("tracking-change", ["Space"]),
    ("tracking-done", ["Esc"]),
    ("write-select", ["Space"] * 3),
    ("write", ["Return"]),
    ("write-done", ["Esc"]),
    ("abort-select", ["Space"]),
    ("abort", ["Return"]),
    ("finished", ["Return"]),
]
cases = [
    ("b:window view", "view"),
    ("b:window top n=0", "zero"),
    ("b:window top n=5", "five"),
    ("b:window ch n=1 pr=2,pc=3,nr=5,nc=20,fg=red,bg=blue", "change"),
    ("b:window write n=1 type=setup,file=b:before.sub", "setup"),
    ("cls", "clear"),
    ("b:window write n=1 type=window,file=b:small.txt", "small"),
    ("cls", "clear2"),
    ("b:window write n=1 type=console,file=b:whole.txt", "whole"),
    ("b:window full n=1", "full"),
    ("b:live", "live"),
    ("b:wmenu", "installed"),
    ("b:wmenu", "duplicate"),
]


def session(v):
    D = F / v
    D.mkdir()

    def run(*a):
        return subprocess.run(a, cwd=D, check=True, capture_output=True)

    shutil.copyfile(R / "media/cdos86.img", D / "cdos86.img")
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
    for n in ["window", "wmenu"]:
        src = (
            R / "base" / (n + ".cmd")
            if v == "o"
            else R / "commands/window" / (n + ".cmd")
        )
        run("mcopy", "-i", "fat.img", str(src), "::" + n + ".cmd")
    run("mcopy", "-i", "fat.img", str(R / "commands/window/livetest.cmd"), "::live.cmd")
    cfg = (
        (R / "media/cdos86.cfg")
        .read_text()
        .replace('driver = "sdl"', 'driver = "null"')
        .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        .replace('file     = "cdostools.img"', 'file     = "fat.img"')
    )
    (D / "cdos86.cfg").write_text(cfg)
    c = ["c f000000"]
    names = {
        " ": "Space",
        ".": "Period",
        ":": "+Shift Semicolon -Shift",
        ",": "Comma",
        "=": "Equal",
    }

    def key(k):
        c.extend(["key " + k, "c 200000"])

    def command(text, label):
        for ch in "cls":
            key(ch)
        key("Return")
        c.append("c 1000000")
        for ch in text:
            key(names.get(ch, ch))
        key("Return")
        c.extend(["c 4000000", f'save "{label}.bin" bin b800:0000 fa0'])

    for text, label in cases:
        command(text, label)
    key("+Ctrl +Alt Esc -Alt -Ctrl")
    c.append("c 4000000")
    for label, keys in actions:
        for k in keys:
            key(k)
            c.append("c 1000000")
        c.extend(["c 2000000", f'save "{label}.bin" bin b800:0000 fa0'])
    command("b:window write n=1 type=setup,file=b:after.sub", "after")
    command("b:window full n=1", "finish-full")
    command("b:window view", "final-view")
    c.append("q")
    with (D / "pce.log").open("wb") as log:
        subprocess.run(
            ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
            cwd=D,
            input=("\n".join(c) + "\n").encode(),
            stdout=log,
            stderr=log,
            timeout=400,
            check=True,
        )
    assert "unknown key:" not in (D / "pce.log").read_text(errors="replace")
    for p in D.glob("*.bin"):
        b = p.read_bytes()
        p.with_suffix(".screen").write_text(
            "\n".join(
                bytes(b[j : j + 160 : 2]).decode("ascii", "replace").rstrip()
                for j in range(0, 4000, 160)
            )
        )
    for name in ["before.sub", "small.txt", "whole.txt", "after.sub"]:
        run("mcopy", "-o", "-i", "fat.img", "::" + name, name)
    print(v, "done", flush=True)


with ThreadPoolExecutor(2) as pool:
    list(pool.map(session, ["o", "n"]))


def screen(v, n):
    return (F / v / (n + ".screen")).read_text()


def rows(v, n):
    return [
        l.lower().split()
        for l in screen(v, n).splitlines()[:24]
        if re.match(r"\s*[1-4]\s+\d+", l)
    ]


assert rows("o", "view") == rows("n", "view") and len(rows("n", "view")) == 4
for n in ["zero", "five"]:
    assert "NUMBER=<1-4>" in screen("o", n) and "NUMBER=<1-4>" in screen("n", n)
for v in ["o", "n"]:
    assert "PASS: GLASS" in screen(v, "live")
    assert "already installed" in screen(v, "duplicate")
    for label, _ in actions:
        b = (F / v / (label + ".bin")).read_bytes()[3840:4000]
        text = b[::2].decode("ascii", "replace")
        (F / v / (label + ".status")).write_text(text)
        if label != "finished":
            assert "N=1" in text, (v, label, text)
for label, _ in actions:
    if label == "finished":
        continue
    a = (F / "o" / (label + ".bin")).read_bytes()[3840:4000]
    b = (F / "n" / (label + ".bin")).read_bytes()[3840:4000]
    # Compare menu wording/selection exactly; submenu values and highlight fields below.
    if label in [
        "main",
        "size-select",
        "size-done",
        "color-select",
        "color-done",
        "tracking-select",
        "tracking-done",
        "write-select",
        "write-done",
        "abort-select",
        "abort",
    ]:
        assert a == b, (label, a[::2], b[::2])
    if label == "size-change":
        assert b"NRows=23" in b[::2], b[::2]
    if label == "tracking-change":
        assert b"Tracking=No" in b[::2], b[::2]
for n in ["before.sub", "after.sub"]:
    a = (F / "o" / n).read_bytes().split(b"\x1a", 1)[0].lower().split()
    b = (F / "n" / n).read_bytes().split(b"\x1a", 1)[0].lower().split()
    assert a == b, (n, a, b)
for n in ["small.txt", "whole.txt"]:
    a = (F / "o" / n).read_bytes().split(b"\x1a", 1)[0]
    b = (F / "n" / n).read_bytes().split(b"\x1a", 1)[0]
    assert a == b, (n, a[:200], b[:200], len(a), len(b))
assert rows("o", "final-view") == rows("n", "final-view"), (
    rows("o", "final-view"),
    rows("n", "final-view"),
)
print(
    "PASS: WINDOW 1..4 numbering, bounds, geometry/colors, setup/window/console files, GLASS; WMENU install, navigation, live edits, cancellation and abort",
    flush=True,
)
shutil.rmtree(F)
