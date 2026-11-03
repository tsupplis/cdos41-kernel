#!/usr/bin/env python3
"""Exercise native BATCH environment/argument expansion on disposable CP/M/FAT media."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FOLDER = Path(tempfile.mkdtemp(prefix="cdos-batch-expand-"))
print("Diagnostics:", FOLDER, flush=True)

def run(*args):
    return subprocess.run(args, cwd=FOLDER, capture_output=True, check=True)

shutil.copyfile(ROOT / "media/diskdefs", FOLDER / "diskdefs")
run("python3", str(ROOT / "tools/cpm86twist.py"), "untwist", str(ROOT / "media/cdos86.img"), "a.logical")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
for tool in ["setenv/setenv.cmd", "echo/echo.cmd"]:
    run("mcopy", "-i", "fat.img", str(ROOT / "commands" / tool), "::")
# Percent characters in values are escaped once in the script, never rescanned.
script = (
    "@ECHO=OFF\r\n"
    "B:SETENV Mix=MiXeD$%%1%%OTHER%%\r\n"
    "B:SETENV OTHER=DO-NOT-EXPAND\r\n"
    "B:SETENV Verb=ECHO\r\n"
    "ECHO VALUE=[%mIx%]\r\n"
    "ECHO UNDEFINED=[%BATCH_MISSING%]\r\n"
    "ECHO ESCAPED=[%%Mix%%]\r\n"
    "ECHO ARG=[%1] TEN=[%10]\r\n"
    "ECHO QUOTED=\"%Mix%\"\r\n"
    "ECHO UNMATCHED=[%trailing]\r\n"
    "%VERB% COMMAND-PASS\r\n"
    "B:ECHO.CMD CHILD=[%Mix%]\r\n"
    "B:SETENV Mix=SecondCase\r\n"
    "ECHO REFRESH=[%mix%]\r\n"
    "SHIFT\r\nECHO SHIFT=[%1]\r\n"
    # A name split across a physical 128-byte BAT record.
)
padding = (127 - len("ECHO BOUNDARY=[") - len(script.encode()) - 6) % 128
if padding > 120:
    script += "\r\n" * 4
    padding -= 8
script += "REM " + "x" * padding + "\r\n"
script += "ECHO BOUNDARY=[%mix%]\r\n"
script += "B:SETENV Wide=" + "X" * 100 + "\r\n"
script += "ECHO " + "Y" * 22 + "%Wide%\r\n"  # exactly 127 expanded chars
script += "ECHO MUST-NOT-EXECUTE-OVERFLOW=%Wide%%Wide%\r\n"
script += "ECHO RAW-MUST-NOT-EXECUTE-" + "Z" * 130 + "\r\n"
script += "ECHO AFTER-OVERFLOW\r\nEXIT\r\nECHO AFTER-EXIT-WRONG\r\n"
(FOLDER / "expand.bat").write_bytes(script.encode() + b"\x1a")
run("mcopy", "-i", "fat.img", "expand.bat", "::")
run("cpmcp", "-f", "ccpm86-320", "a.logical", "expand.bat", "0:EXPAND.BAT")
run("python3", str(ROOT / "tools/cpm86twist.py"), "twist", "a.logical", "cdos86.img")
(FOLDER / "isolate.bat").write_bytes(b"@ECHO=OFF\r\nECHO ISOLATE=[%Mix%]\r\n\x1a")
run("mcopy", "-i", "fat.img", "isolate.bat", "::")
cfg = (ROOT / "media/cdos86.cfg").read_text().replace('driver = "sdl"', 'driver = "null"')
cfg = cfg.replace("sdl:lowpass=5000", "null").replace("cdostools.img", "fat.img")
cfg = re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"', lambda m: 'path = "' + str((ROOT / "media" / m[1]).resolve()) + '"', cfg)
(FOLDER / "test.cfg").write_text(cfg)
commands = ["c f000000"]
keys = {":": "+Shift Semicolon -Shift", " ": "Space", "\n": "Return"}
def command(text, label):
    for ch in text + "\n":
        key = keys.get(ch, ch)
        if ch.isupper():
            key = "+Shift " + ch.lower() + " -Shift"
        commands.extend(["key " + key, "c 200000"])
    commands.extend(["c 30000000", f'save "{label}.bin" bin b800:0000 fa0'])
command("b:expand FirstCase SecondArg", "fat")
command("cls", "clear")
command("a:expand FirstCase SecondArg", "cpm")
commands.extend(["key +Ctrl +Alt 2 -Alt -Ctrl", "c 8000000"])
command("b:isolate", "other-console")
commands.extend(["key +Ctrl +Alt 1 -Alt -Ctrl", "c 8000000"])
command("b:isolate", "original-console")
commands.append("q")
with (FOLDER / "pce.log").open("wb") as log:
    subprocess.run(["pce-ibmpc", "-c", "test.cfg", "-t", "null", "-g", "vga"], cwd=FOLDER,
                   input=("\n".join(commands) + "\n").encode(), stdout=log, stderr=log, timeout=180, check=True)
def screen(name):
    video = (FOLDER / (name + ".bin")).read_bytes()
    result = "\n".join(bytes(video[i:i+160:2]).decode("cp437").rstrip() for i in range(0,3840,160))
    (FOLDER / (name + ".txt")).write_text(result)
    return result
for name in ["fat", "cpm"]:
    result = screen(name)
    for expected in ["VALUE=[MiXeD$%1%OTHER%]", "UNDEFINED=[]", "ESCAPED=[%Mix%]", "ARG=[FirstCase] TEN=[FirstCase0]",
                     'QUOTED="MiXeD$%1%OTHER%"', "UNMATCHED=[%trailing]", "COMMAND-PASS", "CHILD=[MiXeD$%1%OTHER%]",
                     "REFRESH=[SecondCase]", "SHIFT=[SecondArg]", "BOUNDARY=[SecondCase]",
                     "BATCH expanded command exceeds 127 characters; skipped.", "AFTER-OVERFLOW"]:
        assert expected in result, (name, expected, result)
    assert "Y"*22+"X"*100 in result.replace("\n", ""), (name, result)
    assert "MUST-NOT-EXECUTE" not in result and "AFTER-EXIT-WRONG" not in result, result
assert "ISOLATE=[]" in screen("other-console"), screen("other-console")
assert "ISOLATE=[SecondCase]" in screen("original-console"), screen("original-console")
print("PASS: FAT/CPM scripts, native environment query, case, undefined/escaped/nonrecursive values, arguments/SHIFT, command names, CMD child tails, refresh, 127-byte boundary/overflow and console isolation")
shutil.rmtree(FOLDER)
