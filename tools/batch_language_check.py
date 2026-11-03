#!/usr/bin/env python3
"""Exercise the small BATCH language and native ECHO forms."""

from pathlib import Path
import re, shutil, subprocess, tempfile

R = Path(__file__).resolve().parent.parent
F = Path(tempfile.mkdtemp(prefix="cdos-language-"))
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
run(
    "cpmrm",
    "-f",
    "ccpm86-320",
    "a.logical",
    "0:ED.CMD",
    "0:SDIR.CMD",
    "0:CCPM.SYS",
    "0:BATCH.CMD",
)
for p in [
    R / "kernel/sysgen/ccpm.sys",
    R / "commands/batch/batch.cmd",
    R / "commands/putget/put.cmd",
]:
    run("cpmcp", "-f", "ccpm86-320", "a.logical", str(p), "0:")
run("cpmchattr", "-f", "ccpm86-320", "a.logical", "s", "0:BATCH.CMD")
run("python3", str(R / "tools/cpm86twist.py"), "twist", "a.logical", "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
script = (
    "@ECHO=OFF\r\nECHO MiXeD $ text\r\nECHO ON\r\nECHO=ON\r\nECHO VisibleCase\r\n@ECHO=OFF\r\nECHO ARG-%1\r\nSHIFT\r\nECHO ARG-%1\r\nGOTO Destination\r\nECHO WRONG-BRANCH\r\n"
    + ("REM " + ("padding " * 10) + "\r\n")
    + ":destination\r\nECHO LABEL-PASS\r\nGOTO END\r\nECHO WRONG-END\r\n:END\r\nECHO COMPLETE\r\n"
)
for name, data in [
    ("lang.bat", script),
    ("missing.bat", "@ECHO=OFF\r\nGOTO absent\r\nECHO WRONG-MISSING\r\n"),
    ("at.bat", "@ECHO=OFF\r\n@DIR\r\nECHO AT-PASS\r\n"),
]:
    (F / name).write_bytes(data.encode() + b"\x1a")
    run("mcopy", "-i", "fat.img", name, "::")
run("cpmcp", "-f", "ccpm86-320", "a.logical", "lang.bat", "0:LANGC.BAT")
run("python3", str(R / "tools/cpm86twist.py"), "twist", "a.logical", "cdos86.img")
(F / "back.bat").write_bytes(
    b"@ECHO=OFF\r\nGOTO start\r\n:again\r\nECHO BACKWARD-PASS\r\nGOTO end\r\n:start\r\nGOTO again\r\n:end\r\nECHO BACK-END\r\n\x1a"
)
run("mcopy", "-i", "fat.img", "back.bat", "::")
(F / "empty.bat").write_bytes(
    b"@ECHO=OFF\r\n" + b"SHIFT\r\n" * 15 + b"ECHO EMPTY-%9-END\r\n\x1a"
)
run("mcopy", "-i", "fat.img", "empty.bat", "::")
for name, data in [
    (
        "context.bat",
        b"@ECHO=OFF\r\nUSER 1\r\nUSER\r\nUSER 0\r\nB:\r\nDIR\r\nA:\r\nECHO CONTEXT-PASS\r\n",
    ),
    ("drive.bat", b"@ECHO=OFF\r\nB:\r\n"),
]:
    (F / name).write_bytes(data + b"\x1a")
    run("mcopy", "-i", "fat.img", name, "::")
run("mcopy", "-i", "fat.img", str(R / "commands/echo/echo.cmd"), "::")
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
c = ["c f000000"]
keys = {
    ":": "+Shift Semicolon -Shift",
    " ": "Space",
    ".": "Period",
    "[": "LeftBracket",
    "]": "RightBracket",
    "=": "Equal",
    "-": "Minus",
}
for text, label in [
    ("echo InteractiveCase", "interactive"),
    ("b:lang OneCase TwoCase", "batch"),
    ("cls", "clear-cpm"),
    ("a:langc OneCase TwoCase", "cpm-batch"),
    ("cls", "clear-back"),
    ("b:back", "backward"),
    ("cls", "clear-empty"),
    ("b:empty one two", "empty"),
    ("cls", "clear"),
    ("b:missing", "missing"),
    ("cls", "clear2"),
    ("b:at", "at"),
    ("cls", "clear3"),
    ("put [b:echo.out] b:echo.cmd CMDCASE", "exe"),
    ("b:context", "context"),
    ("user 0", "restore-user"),
    ("a:", "restore-drive"),
]:
    for ch in text + "\n":
        key = "Return" if ch == "\n" else keys.get(ch, ch)
        if ch.isupper():
            key = "+Shift " + ch.lower() + " -Shift"
        c += ["key " + key, "c 200000"]
    c += ["c 10000000", f'save "{label}.bin" bin b800:0000 fa0']
c += ["q"]
with (F / "pce.log").open("wb") as log:
    subprocess.run(
        ["pce-ibmpc", "-c", "test.cfg", "-t", "null", "-g", "vga"],
        cwd=F,
        input=("\n".join(c) + "\n").encode(),
        stdout=log,
        stderr=log,
        timeout=120,
        check=True,
    )
screens = {}
for label in [
    "interactive",
    "batch",
    "cpm-batch",
    "backward",
    "empty",
    "missing",
    "at",
    "exe",
    "context",
]:
    b = (F / (label + ".bin")).read_bytes()
    s = "\n".join(
        bytes(b[i : i + 160 : 2]).decode("latin1").rstrip() for i in range(0, 3840, 160)
    )
    print(label + "\n" + s)
    (F / (label + ".txt")).write_text(s)
    screens[label] = s
p = run("mtype", "-i", "fat.img", "::echo.out")
print("CMD FILE:", p.stdout)

b = screens["batch"]
for text in [
    "MiXeD $ text",
    "ON",
    "A>ECHO VisibleCase",
    "VisibleCase",
    "ARG-OneCase",
    "ARG-TwoCase",
    "LABEL-PASS",
    "COMPLETE",
]:
    assert text in b.splitlines(), (text, b)
assert "WRONG" not in b and "@ECHO" not in b, b
assert (
    "ARG-TwoCase" in screens["cpm-batch"] and "COMPLETE" in screens["cpm-batch"]
), screens["cpm-batch"]
assert (
    "BACKWARD-PASS" in screens["backward"] and "BACK-END" in screens["backward"]
), screens["backward"]
assert "EMPTY--END" in screens["empty"], screens["empty"]
assert (
    "Label not found; BATCH stopped." in screens["missing"]
    and "WRONG" not in screens["missing"]
)
assert (
    "@DIR" in screens["at"]
    and "AT-PASS" in screens["at"]
    and "Can't Find Command" in screens["at"]
)
assert p.stdout == b"CMDCASE\r\n".ljust(128, b"\x1a"), p.stdout
assert "CONTEXT-PASS" in screens["context"], screens["context"]
assert "Directory of Drive B" in screens["context"], screens["context"]
assert "User Number = 1" in screens["context"], screens["context"]
assert (R / "commands/batch/batch.cmd").read_bytes()[127] & 2
assert (R / "commands/batch/language.lib").read_bytes() == (
    R / "kernel/rsp3/language.lib"
).read_bytes()
print(
    "PASS: PCTMP ECHO, script-only ECHO=ON/OFF and @ECHO, SHIFT, GOTO across records, missing-label exit, rejected @command and exact CMD redirection"
)
shutil.rmtree(F)
