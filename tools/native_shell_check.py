#!/usr/bin/env python3
"""Check native PATH and external-only SYSDISK on disposable media."""

from pathlib import Path
import tempfile, subprocess, shutil, re
from alias_check import ROOT as R

F = Path(tempfile.mkdtemp(prefix="cdos-native-shell-"))
print("Diagnostics:", F, flush=True)


def run(*args):
    return subprocess.run(args, cwd=F, check=True, capture_output=True)


shutil.copyfile(R / "media/diskdefs", F / "diskdefs")
run("python3", str(R/"tools/cpm86twist.py"), "untwist", str(R/"media/cdos86.img"), "logical.img")
(F/"native.bat").write_bytes(b"PATH=BatchValue\r\nB:XSYS.CMD [OFF]\r\nB:XSYS.CMD [ON]\r\nPATH\r\n")
run("cpmcp", "-f", "ccpm86-320", "logical.img", "native.bat", "0:NATIVE.BAT")
run("python3", str(R/"tools/cpm86twist.py"), "twist", "logical.img", "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
run("mcopy", "-i", "fat.img", str(R/"commands/path/path.cmd"), "::NPATH.CMD")
run("mcopy", "-i", "fat.img", str(R/"commands/sysdisk/sysdisk.cmd"), "::XSYS.CMD")
run("mmd", "-i", "fat.img", "::FIRST")
cfg = (
    (R / "media/cdos86.cfg")
    .read_text()
    .replace('driver = "sdl"', 'driver = "null"')
    .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
    .replace('file     = "cdostools.img"', 'file     = "fat.img"')
)
cfg = re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"', lambda m: 'path = "' + str((R / "media" / m[1]).resolve()) + '"', cfg)
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
    "=": "Equal",
    "\\": "Backslash",
}


def key(k):
    c.extend(["key " + k, "c 200000"])


def command(text, label):
    for ch in "cls":
        key(ch)
    key("Return")
    c.append("c 1000000")
    for ch in text:
        key(keys.get(ch, "+Shift "+ch.lower()+" -Shift" if ch.isupper() else ch))
    key("Return")
    c.extend(["c 4000000", f'save "{label}.bin" bin b800:0000 fa0'])


cases = [
 ("path=MixedValue", "pathset", "A>"),
 ("path", "pathquery", "PATH=MixedValue"),
 ("b:npath.cmd", "externalpath", "PATH=MixedValue"),
 ("b:npath.cmd=ExternalValue", "externalset", "A>"),
 ("path", "externalverify", "PATH=ExternalValue"),
 ("path=", "pathclear", "A>"),
 ("path", "cleared", "PATH="),
 ("sysdisk", "no-builtin", "Can't Find Command"),
 ("b:xsys.cmd a:", "sysset", "A>"),
 ("b:xsys.cmd", "sysquery", "A:"),
 ("b:xsys.cmd [off]", "sysoff", "The system drive is off"),
 ("b:xsys.cmd [on]", "syson", "A:"),
 ("b:xsys.cmd b:\\first", "syssub", "A>"),
 ("b:xsys.cmd", "subquery", "B:\\FIRST"),
 ("a:native.bat", "batch", "PATH=BatchValue"),
 ("path", "batchpath", "PATH=BatchValue"),
 ("b:xsys.cmd a:", "reset", "A>"),
]
for text,label,expected in cases: command(text,label)
c += ["q"]
with (F/"pce.log").open("wb") as log:
 subprocess.run(["pce-ibmpc","-c","cdos86.cfg","-t","null","-g","vga"],cwd=F,input=("\n".join(c)+"\n").encode(),stdout=log,stderr=log,timeout=300,check=True)
for text,label,expected in cases:
 b=(F/(label+".bin")).read_bytes()
 screen="\n".join(bytes(b[j:j+160:2]).decode("ascii","replace").rstrip() for j in range(0,3840,160))
 (F/(label+".txt")).write_text(screen)
 assert expected in screen,(text,expected,screen)
 assert screen.rstrip().endswith("A>"),(text,screen)
 if label=="batch":
  assert "The system drive is off" in screen,screen
  assert "Can't Find Command" not in screen,screen
print("PASS: TMP/BATCH PATH query/set/clear and PATH.CMD; SYSDISK is external-only and works from TMP/BATCH")
shutil.rmtree(F)
