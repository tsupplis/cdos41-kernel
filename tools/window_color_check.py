#!/usr/bin/env python3
"""Compare immediate WINDOW repaint against 4.11; no clears between colour changes."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tempfile, shutil, subprocess, re
from alias_check import ROOT as R

F = Path(tempfile.mkdtemp(prefix="cdos-window-"))
print("Diagnostics:", F, flush=True)
cases = [('cls','initial'),
 ('b:window ch n=1 pr=8,pc=2,nr=16,nc=65,vr=9,vc=1,tr=row,fg=white,bg=blue','card1'),
 ('b:window ch n=2 pr=6,pc=6,nr=16,nc=65,vr=9,vc=1,tr=row,fg=white,bg=red','card2'),
 ('b:window ch n=3 pr=4,pc=10,nr=16,nc=65,vr=9,vc=1,tr=row,fg=white,bg=green','card3'),
 ('b:window ch n=4 pr=2,pc=14,nr=16,nc=65,vr=9,vc=1,tr=row,fg=white,bg=yellow','card4'),
 ('b:window full n=1','full'),
 ('b:window ch n=1 bg=cyan','fullcolor'),
 ('b:window ch n=2 bg=magenta','backgroundcolor')]


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
        for ch in text:
            key(names.get(ch, ch))
        key("Return")
        c.extend(["c 4000000", f'save "{label}.bin" bin b800:0000 fa0'])

    for text, label in cases:
        command(text, label)
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
    print(v, "done", flush=True)


with ThreadPoolExecutor(2) as pool:
    list(pool.map(session, ["o", "n"]))


for label in ('card1','card2','card3','card4','full','fullcolor','backgroundcolor'):
    old = (F/'o'/(label+'.bin')).read_bytes()[:3840]
    new = (F/'n'/(label+'.bin')).read_bytes()[:3840]
    assert old == new, (label, 'text or attribute difference', F)
print('PASS: CARDDECK, foreground full-screen and background colour changes match original text/attributes without clearing')
