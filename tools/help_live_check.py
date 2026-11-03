#!/usr/bin/env python3
"""Read representative maintained help topics through the native HELP program."""

from pathlib import Path
import tempfile, shutil, subprocess, re
from alias_check import ROOT as R

F = Path(tempfile.mkdtemp(prefix="cdos-help-live-"))
print("Diagnostics:", F, flush=True)


def run(*a):
    return subprocess.run(a, cwd=F, check=True, capture_output=True)


shutil.copyfile(R / "media/cdos86.img", F / "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
for p in ["help/help.cmd", "helphlp/help.hlp"]:
    run("mcopy", "-i", "fat.img", str(R / "commands" / p), "::" + Path(p).name)
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
(F / "cdos86.cfg").write_text(cfg)
c = ["c f000000"]
keys = {
    " ": "Space",
    ":": "+Shift Semicolon -Shift",
    "[": "LeftBracket",
    "]": "RightBracket",
}


def command(text, label):
    for ch in text:
        c.extend(["key " + keys.get(ch, ch), "c 200000"])
    c.extend(["key Return", "c 8000000", f'save "{label}.bin" bin b800:0000 fa0'])


command("b:", "drive")
cases = [
    ("commands", "no separate DIR"),
    ("dir", "[S]"),
    ("batch", "ECHO=ON/OFF"),
    ("tree", "TREE {d:}"),
    ("echo", "Only BATCH has ECHO=ON/OFF"),
    ("languages batch echo", "equals sign changes state"),
    ("languages batch shift", "old %1 becomes %0"),
    ("languages batch goto", "GOTO :label"),
    ("languages batch exit", "decimal 0-255"),
    ("languages batch if", "IF [NOT] DIREXIST directory command"),
    ("languages batch if files", "Directories do not satisfy EXIST"),
    ("languages batch if strings", 'IF "%NAME%TOTO"=="TOTO" command'),
    ("languages batch if status", "True if the last program status is at least"),
    ("languages batch variables", "Undefined names become empty"),
    ("set", "[PASSWORD=] alone"),
    ("setenv", "Native SETENV.CMD"),
    ("wmenu", "Ctrl-Alt-Esc"),
    ("order", "ORDER="),
    ("path", "PATH.CMD is the native external version"),
]
import sys
if "--path" in sys.argv: cases = [x for x in cases if x[0] == "path"]
if "--batch" in sys.argv: cases = [x for x in cases if x[0] == "batch" or x[0].startswith("languages batch")]
if "--labels" in sys.argv:
    cases = [("set", "SET d: [NAME=] removes the FAT label"),
             ("show", "LABEL displays the physical-root volume name on FAT")]
for topic, _ in cases:
    command("cls", "clear-" + topic)
    command("help " + topic + " [nopage]", topic)
    command("", "return-" + topic)
c.append("q")
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
for topic, expected in cases:
    b = (F / (topic + ".bin")).read_bytes()
    s = "\n".join(
        bytes(b[j : j + 160 : 2]).decode("ascii", "replace").rstrip()
        for j in range(0, 3840, 160)
    )
    (F / (topic + ".txt")).write_text(s)
    assert expected in s, (topic, s)
print(
    "PASS: native HELP reads " + ", ".join(topic for topic, _ in cases),
    flush=True,
)
shutil.rmtree(F)
