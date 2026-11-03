#!/usr/bin/env python3
"""Verify BATCH EXIT and normal EOF through a real native parent's BDOS 108."""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(tempfile.mkdtemp(prefix="cdos-batch-exit-"))
print("Diagnostics:", FOLDER, flush=True)


def run(*args):
    return subprocess.run(args, cwd=FOLDER, capture_output=True, check=True)


# A native child deliberately gives BATCH a nonzero result before EXIT/EOF.
seed = """        cseg
start:
        mov dx,77
        mov cl,108
        int 0e0h
        xor cx,cx
        xor dx,dx
        int 0e0h
        dseg
        org 100h
        rs 256
        end start
"""
(FOLDER / "set77.a86").write_bytes(seed.replace("\n", "\r\n").encode())
shutil.copyfile(Path(__file__).with_name("exittest.a86"), FOLDER / "exittest.a86")

cases = []
for form, expected in [
    ("EXIT", 0),
    ("EXIT 0", 0),
    ("EXIT 1", 1),
    ("EXIT 7", 7),
    ("EXIT 255", 255),
    ("eXiT 00042   \t", 42),
]:
    cases.append(
        (
            "@ECHO=OFF\r\nB:SET77.CMD\r\n"
            + form
            + "\r\nECHO EXIT-DID-NOT-STOP\r\nEXIT 99\r\n",
            expected,
            True,
        )
    )
# Both physical EOF and Ctrl-Z must clear the preceding child's result.
for ctrl_z in [False, True]:
    cases.append(("@ECHO=OFF\r\nB:SET77.CMD\r\n", 0, ctrl_z))
for invalid in ["-1", "+1", "256", "65535", "99999999", "0x10", "7x", "1 2", "=7"]:
    form = "EXIT" + (invalid if invalid.startswith("=") else " " + invalid)
    cases.append(("@ECHO=OFF\r\n" + form + "\r\nEXIT 19\r\n", 19, True))
# Chaining must retain the explicit status of the replacement script.
cases.append(("@ECHO=OFF\r\nB:REPLACE.BAT\r\nEXIT 99\r\n", 23, True))

# Test-only observer layout: public PD parent link and the local native status word.
pd = (ROOT / "kernel/con/black.sym").read_text(errors="replace")
assert re.search(r"001E\s+P_PARENT\b", pd), "parent PD offset changed"
assert re.search(r"002C\s+P_RETCODE\b", pd), "return-code PD offset changed"
for name in ["exittest", "set77"]:
    run("pcdev_rasm86", name + ".a86")
    run("pcdev_linkcmd", f"{name}={name}[data[origin[0],max[0]]]")

shutil.copyfile(ROOT / "media/diskdefs", FOLDER / "diskdefs")
run(
    "python3",
    str(ROOT / "tools/cpm86twist.py"),
    "untwist",
    str(ROOT / "media/cdos86.img"),
    "a.logical",
)
run("cpmrm", "-f", "ccpm86-320", "a.logical", "0:BATCH.CMD")
run(
    "cpmcp",
    "-f",
    "ccpm86-320",
    "a.logical",
    str(ROOT / "commands/batch/batch.cmd"),
    "0:BATCH.CMD",
)
run("cpmchattr", "-f", "ccpm86-320", "a.logical", "s", "0:BATCH.CMD")
run("python3", str(ROOT / "tools/cpm86twist.py"), "twist", "a.logical", "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
for number, (body, _, ctrl_z) in enumerate(cases):
    name = f"X{number:02}.BAT"
    (FOLDER / name).write_bytes(body.encode() + (b"\x1a" if ctrl_z else b""))
    run("mcopy", "-i", "fat.img", name, "::")
(FOLDER / "replace.bat").write_bytes(b"@ECHO=OFF\r\nEXIT 23\r\n\x1a")
run("mcopy", "-i", "fat.img", "replace.bat", "::")
for name in ["exittest.cmd", "set77.cmd"]:
    run("mcopy", "-i", "fat.img", name, "::")

cfg = (
    (ROOT / "media/cdos86.cfg").read_text().replace('driver = "sdl"', 'driver = "null"')
)
cfg = cfg.replace("sdl:lowpass=5000", "null").replace("cdostools.img", "fat.img")
cfg = re.sub(
    r'(?m)^path\s*=\s*"([^"\n]+)"',
    lambda m: 'path = "' + str((ROOT / "media" / m[1]).resolve()) + '"',
    cfg,
)
(FOLDER / "test.cfg").write_text(cfg)
commands = ["c f000000"]
def command(text):
    for ch in text + "\n":
        key = {":": "+Shift Semicolon -Shift", " ": "Space", "\n": "Return"}.get(ch, ch)
        commands.extend(["key " + key, "c 200000"])
    commands.append("c 8000000")
for number, (_, expected, _) in enumerate(cases):
    command("cls")
    command(f"a:batch b:x{number:02}.bat")
    command(f"b:exittest {expected}")
    commands.append(f'save "screen-{number}.bin" bin b800:0000 fa0')
commands.append("q")
with (FOLDER / "pce.log").open("wb") as log:
    subprocess.run(
        ["pce-ibmpc", "-c", "test.cfg", "-t", "null", "-g", "vga"],
        cwd=FOLDER,
        input=("\n".join(commands) + "\n").encode(),
        stdout=log,
        stderr=log,
        timeout=300,
        check=True,
    )
for number in range(len(cases)):
    video = (FOLDER / f"screen-{number}.bin").read_bytes()
    screen = "\n".join(
        bytes(video[i : i + 160 : 2]).decode("cp437").rstrip() for i in range(0, 3840, 160)
    )
    (FOLDER / f"screen-{number}.txt").write_text(screen)
    assert "BATCH EXIT PASS" in screen and "BATCH EXIT FAIL" not in screen, (number, screen)
    assert "EXIT-DID-NOT-STOP" not in screen, (number, screen)
print(
    f"PASS: {len(cases)} BATCH EXIT/EOF/invalid-status/chain cases through native BDOS 108"
)
shutil.rmtree(FOLDER)
