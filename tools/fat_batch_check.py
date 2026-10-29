#!/usr/bin/env python3
"""Check FAT BAT loading with DOS case flags, EOF forms and CMD execution."""

from pathlib import Path
import tempfile, subprocess, shutil

R = Path(__file__).resolve().parent.parent

F = Path(tempfile.mkdtemp(prefix="cdos-fat-batch-"))
print("Diagnostics:", F, flush=True)


def run(*args):
    p = subprocess.run(args, cwd=F, capture_output=True)
    if p.returncode:
        raise RuntimeError(args, p.stderr.decode(errors="replace"))
    return p


shutil.copyfile(R / "media/cdos86.img", F / "cdos86.img")
run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2", "-n", "8", "-c", "2", "::")
run("mcopy", "-i", "fat.img", str(R / "commands/era/era.cmd"), "::ERA.CMD")
(F / "sentinel").write_bytes(b"untouched sentinel\r\n\x1a")
run("mcopy", "-i", "fat.img", "sentinel", "::KEEP.TST")
cfg = (
    (R / "media/cdos86.cfg")
    .read_text()
    .replace('driver = "sdl"', 'driver = "null"')
    .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
    .replace('file     = "cdostools.img"', 'file     = "fat.img"')
)
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
}


def key(k):
    c.extend(["key " + k, "c 200000"])


def command(text, label):
    for ch in "cls":
        key(ch)
    key("Return")
    c.append("c 1000000")
    for ch in text:
        key(keys.get(ch, ch))
    key("Return")
    c.extend(["c 4000000", f'save "{label}.bin" bin b800:0000 fa0'])


cases = []
for flags in [0x00, 0x08, 0x10, 0x18]:
    for ending in ["crlf", "ctrlz", "padded"]:
        name = f"t{flags:02x}" + {"crlf": "c", "ctrlz": "z", "padded": "p"}[ending]
        drop = name + ".tst"
        lines = ["REM refill the command buffer " + str(i) for i in range(12)]
        lines += ["USER 1", "USER 0", "B:ERA B:" + drop]
        payload = ("\r\n".join(lines) + "\r\n").encode()
        if ending != "crlf":
            payload += b"\x1a"
        if ending == "padded":
            payload += b"\x1a" * (-len(payload) % 128)
        (F / "script").write_bytes(payload)
        run("mcopy", "-i", "fat.img", "script", "::" + name.upper() + ".BAT")
        run("mcopy", "-i", "fat.img", "sentinel", "::" + drop.upper())
        cases.append((name, flags, drop))
# Set the FAT12 short-name case byte explicitly; do not depend on mtools defaults.
b = bytearray((F / "fat.img").read_bytes())
w = lambda at: int.from_bytes(b[at : at + 2], "little")
root = (w(14) + b[16] * w(22)) * w(11)
entries = {bytes(b[at : at + 11]): at for at in range(root, root + w(17) * 32, 32)}
for name, flags, drop in cases:
    keyname = name.upper().ljust(8).encode() + b"BAT"
    b[entries[keyname] + 12] = flags
# Exercise a FAT-hosted external CMD with both lowercase flags as well.
b[entries[b"ERA     CMD"] + 12] = 0x18
(F / "fat.img").write_bytes(b)
for name, flags, drop in cases:
    command("b:" + name + ".bat", name)
c += ["q"]
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
for name, flags, drop in cases:
    b = (F / (name + ".bin")).read_bytes()
    screen = "\n".join(
        bytes(b[j : j + 160 : 2]).decode("ascii", "replace").rstrip()
        for j in range(0, 3840, 160)
    )
    (F / (name + ".txt")).write_text(screen)
    assert "User Number = 1" in screen and "User Number = 0" in screen, screen
    assert "Error" not in screen and "error" not in screen, screen
    assert [x for x in screen.splitlines() if x][-1] == "A>", screen
    # Check the FAT directory through mtools after the emulator has closed it.
    p = subprocess.run(
        ["mtype", "-i", "fat.img", "::" + drop], cwd=F, capture_output=True
    )
    assert p.returncode != 0, (name, "ERA did not remove its target")
assert (
    run("mtype", "-i", "fat.img", "::KEEP.TST").stdout == (F / "sentinel").read_bytes()
)
print(
    "PASS: 12 FAT BAT cases: four filename case flags, CR/LF or Ctrl-Z EOF, record padding, buffer refill, FAT-hosted ERA and unrelated sentinel",
    flush=True,
)
shutil.rmtree(F)
