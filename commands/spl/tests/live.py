"""Compare PRINTMGR/DSP interoperability in disposable CDOS/PCE sessions."""
from pathlib import Path
import shutil
import subprocess
import tempfile

SPL = Path(__file__).resolve().parents[1]
ROOT = SPL.parents[1]
COMMANDS = [
    "b:", "printmgr start 0", "printmgr status", "printmgr start 0",
    "printmgr sample.txt", "printmgr status", "printmgr reset",
    "printmgr status", "printmgr start 0", "printmgr terminate",
    "printmgr status",
]
KEYS = {" ": "Space", ":": "+Shift Semicolon -Shift", ".": "Period"}


def system_image(folder):
    folder.mkdir()
    for name in ("bdos.con", "cio.con", "mem.con", "rtm.con", "sup.con",
                 "sysdat.con", "xios.con", "pin.rsp", "clock.rsp",
                 "pctmp.rsp", "confid.rsp"):
        shutil.copyfile(ROOT / "kernel/sysgen" / name, folder / name)
    answers = (ROOT / "kernel/sysgen/genccpm.in").read_text()
    answers = answers.replace("osstart=6000", "osstart=6000 nqcbs=20 qbufsize=800")
    with (folder / "sysgen.log").open("wb") as log:
        subprocess.run(["emu2", str(ROOT / "commands/genccpm/genccpm.cmd")],
                       input=answers.encode(), cwd=folder, stdout=log, stderr=log,
                       check=True, timeout=60)
    assert (folder / "ccpm.sys").is_file(), (folder / "sysgen.log").read_text(errors="replace")
    subprocess.run(["python3", str(ROOT / "tools/sysgen_check.py"),
                    str(folder / "ccpm.sys")], check=True)
    shutil.copyfile(ROOT / "media/diskdefs", folder / "diskdefs")
    twist = ROOT / "tools/cpm86twist.py"
    subprocess.run(["python3", str(twist), "untwist",
                    str(ROOT / "media/cdos86.img"), str(folder / "logical.img")],
                   check=True)
    subprocess.run(["cpmrm", "-f", "ccpm86-320", "logical.img", "0:ccpm.sys"],
                   cwd=folder, check=True)
    subprocess.run(["cpmcp", "-f", "ccpm86-320", "logical.img", "ccpm.sys",
                    "0:ccpm.sys"], cwd=folder, check=True)
    subprocess.run(["python3", str(twist), "twist", str(folder / "logical.img"),
                    str(folder / "cdos86.img")], check=True)
    return folder / "cdos86.img"


def session(folder, binary, system):
    folder.mkdir()

    def run(*args):
        return subprocess.run(args, cwd=folder, check=True, capture_output=True)

    shutil.copyfile(system, folder / "cdos86.img")
    config = (ROOT / "media/cdos86.cfg").read_text()
    config = config.replace('driver = "sdl"', 'driver = "null"')
    config = config.replace("sdl:lowpass=5000", "null")
    config = config.replace("cdostools.img", "fat.img")
    (folder / "cfg").write_text(config)
    run("mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2",
        "-n", "8", "-c", "2", "::")
    for source, target in [
        (binary, "spl.cmd"),
        (ROOT / "commands/printmgr/printmgr.cmd", "printmgr.cmd"),
        (ROOT / "commands/dsp/dsp.cmd", "dsp.cmd"),
    ]:
        run("mcopy", "-i", "fat.img", str(source), "::" + target)
    (folder / "sample.txt").write_bytes(b"SPL reconstruction test\r\n\x1a")
    run("mcopy", "-i", "fat.img", "sample.txt", "::sample.txt")
    script = ["c f000000"]
    for number, command in enumerate(COMMANDS):
        for key in ("c", "l", "s", "Return"):
            script.extend(["key " + key, "c 200000"])
        for key in command:
            script.extend(["key " + KEYS.get(key, key), "c 200000"])
        script.extend(["key Return", "c 5000000",
                       f'save "s{number}.bin" bin b800:0000 fa0'])
    script.append("q")
    with (folder / "log").open("wb") as log:
        subprocess.run(["pce-ibmpc", "-c", "cfg", "-t", "null", "-g", "vga"],
                       cwd=folder, input=("\n".join(script) + "\n").encode(),
                       stdout=log, stderr=log, timeout=240, check=True)
    assert "unknown key:" not in (folder / "log").read_text(errors="replace")
    screens = []
    for number in range(len(COMMANDS)):
        frame = (folder / f"s{number}.bin").read_bytes()
        screen = "\n".join(frame[j:j + 160:2].decode("cp437").rstrip()
                           for j in range(0, 3840, 160)).strip()
        screens.append(screen)
    assert "Successful" in screens[1], screens[1]
    assert "No active jobs" in screens[2], screens[2]
    assert "already set up" in screens[3], screens[3]
    assert "Successful" in screens[4] and "sample.txt" in screens[4].lower(), screens[4]
    assert "all jobs were deleted" in screens[6], screens[6]
    assert "Could not obtain access" in screens[7], screens[7]
    assert "Successful" in screens[8], screens[8]
    assert "all jobs were saved" in screens[9], screens[9]
    assert "Could not obtain access" in screens[10], screens[10]
    return screens


def check():
    with tempfile.TemporaryDirectory(prefix="cdos-spl-live-") as directory:
        folder = Path(directory)
        system = system_image(folder / "system")
        original = session(folder / "original", ROOT / "base/spl.cmd", system)
        rebuilt = session(folder / "rebuilt", SPL / "spl.cmd", system)
        for command, old, new in zip(COMMANDS, original, rebuilt):
            assert old == new, (command, old, new)
    print("PASS: 11 paired CDOS/PCE screens: startup, submission, status, reset, restart, terminate")


if __name__ == "__main__":
    check()
