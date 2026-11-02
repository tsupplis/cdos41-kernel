"""Compare STOP sessions under Concurrent DOS in disposable PCE machines.

Each binary runs the same keystroke script. Complete VGA text frames,
including attributes, must match apart from the status line and its clock.
The script also stops a real PIP process running on another console.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


STOP = Path(__file__).resolve().parents[1]
ROOT = STOP.parents[1]
KEYS = {" ": "Space", ":": "+Shift Semicolon -Shift", ".": "Period"}
ROW = re.compile(r"^\s*(\*\*|\d+\.)\s+(.+?)\s+\d+K\s+(\d+)\s*$")
HEADING = "Entry   Program   Memory   Window"
PROMPT = "Enter the Number to delete or RETURN to exit"
FRAME = 4000
STATUS = 24 * 160


def session(folder, binary, system_image):
    folder.mkdir()
    shutil.copyfile(system_image, folder / "cdos86.img")
    config = (ROOT / "media/cdos86.cfg").read_text()
    config = config.replace('driver = "sdl"', 'driver = "null"')
    config = config.replace("sdl:lowpass=5000", "null")
    config = config.replace("cdostools.img", "fat.img")
    (folder / "cfg").write_text(config)
    subprocess.run(
        ["mformat", "-C", "-i", "fat.img", "-t", "40", "-h", "2",
         "-n", "8", "-c", "2", "::"],
        cwd=folder, check=True, capture_output=True,
    )
    subprocess.run(
        ["mcopy", "-i", "fat.img", str(binary), "::stop.cmd"],
        cwd=folder, check=True, capture_output=True,
    )

    script = ["c f000000"]
    names = []

    def enter(text):
        for key in text:
            script.extend(["key " + KEYS.get(key, key), "c 200000"])
        script.extend(["key Return", "c 5000000"])

    def console(number):
        script.extend([f"key +Ctrl +Alt {number + 1} -Alt -Ctrl", "c 2000000"])

    def capture(name):
        names.append(name)
        script.append(f'save "{name}.bin" bin b800:0000 fa0')

    enter("b:")
    enter("b:stop.cmd")
    capture("report")
    enter("99")
    capture("too-large")
    enter("b:stop.cmd")
    enter("x")
    capture("invalid")
    enter("b:stop.cmd x")
    capture("tail")
    enter("b:stop.cmd")
    enter("")
    capture("return")
    console(1)
    enter("pip")
    capture("victim")
    console(0)
    enter("b:stop.cmd")
    capture("with-victim")
    enter("1")
    capture("stopped")
    enter("b:stop.cmd")
    capture("after")
    enter("")
    console(1)
    capture("victim-console")
    enter("dir pip.cmd")
    capture("victim-shell")
    script.append("q")

    result = subprocess.run(
        ["pce-ibmpc", "-c", "cfg", "-t", "null", "-g", "vga"],
        cwd=folder, input=("\n".join(script) + "\n").encode(),
        capture_output=True, timeout=480, check=True,
    )
    if b"unknown key:" in result.stdout or b"unknown key:" in result.stderr:
        raise RuntimeError(f"PCE rejected a key: {result.stdout!r} {result.stderr!r}")

    frames = {}
    for name in names:
        frame = (folder / f"{name}.bin").read_bytes()
        if len(frame) != FRAME:
            raise ValueError(f"{folder}: invalid VGA screen length: {len(frame)}")
        frames[name] = frame
    return frames


def text(frame):
    return "\n".join(
        frame[i:i + 160:2].decode("cp437").rstrip()
        for i in range(0, STATUS, 160)
    ).rstrip()


def last_report(screen, label, name):
    start = screen.rfind(HEADING)
    if start < 0:
        raise AssertionError(f"{label} {name}: missing heading:\n{screen}")
    return screen[start:]


def rows(screen):
    return [match.groups() for line in screen.splitlines()
            if (match := ROW.fullmatch(line))]


def at_shell(screen, drive):
    return re.search(rf"(?m)^{drive}>\Z", screen)


def verify(frames, label):
    screens = {name: text(frame) for name, frame in frames.items()}

    def fail(name, reason):
        raise AssertionError(f"{label} {name}: {reason}:\n{screens[name]}")

    for name in ("report", "tail", "with-victim", "after"):
        report = last_report(screens[name], label, name)
        for line in ("Contiguous Blocks of Free Memory", "Free Shared Code",
                     "Total Free Memory"):
            if line not in report:
                fail(name, f"missing {line!r}")
        if not rows(report):
            fail(name, "no process rows")
    for name in ("report", "with-victim", "after"):
        if PROMPT not in last_report(screens[name], label, name):
            fail(name, "missing prompt")
    if PROMPT in last_report(screens["tail"], label, "tail"):
        fail("tail", "prompted despite a command tail")
    if not screens["too-large"].endswith("Entry number too large\nB>"):
        fail("too-large", "entry 99 was not rejected")
    if not screens["invalid"].endswith("Invalid Entry number.\nB>"):
        fail("invalid", "entry x was not rejected")
    for name in ("tail", "return", "stopped"):
        if not at_shell(screens[name], "B"):
            fail(name, "did not return to the shell")

    victims = [row for row in rows(last_report(screens["with-victim"], label, "with-victim"))
               if row[1] == "PIP"]
    if len(victims) != 1 or victims[0][0] != "1.":
        fail("with-victim", "expected PIP as entry 1")
    if "has not been stopped" in screens["stopped"]:
        fail("stopped", "abort failed")
    if any(row[1] == "PIP" for row in rows(last_report(screens["after"], label, "after"))):
        fail("after", "PIP is still listed")
    if not screens["victim"].endswith("*"):
        fail("victim", "PIP prompt missing")
    if not at_shell(screens["victim-console"], "A"):
        fail("victim-console", "PIP's console did not return to the shell")
    if not re.search(r"A>dir pip\.cmd\n(?:.*\n)*.*PIP\s+CMD(?:.*\n)*A>\Z", screens["victim-shell"]):
        fail("victim-shell", "PIP's console did not run DIR")


def compare(original, rebuilt):
    for name, frame in original.items():
        if frame[:STATUS] != rebuilt[name][:STATUS]:
            raise AssertionError(
                f"{name}: frames differ\n--- release\n{text(frame)}\n"
                f"--- PL/M\n{text(rebuilt[name])}"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-image", type=Path, default=ROOT / "media/cdos86.img",
                        help="bootable Concurrent DOS image (default: media/cdos86.img)")
    parser.add_argument("--dump", type=Path,
                        help="also write each screen as text into this directory")
    args = parser.parse_args()
    if not args.system_image.is_file():
        parser.error(f"system image not found: {args.system_image}")
    with tempfile.TemporaryDirectory(prefix="cdos-stop-live-") as directory:
        folder = Path(directory)
        system_image = folder / "system.img"
        reference = folder / "reference.cmd"
        candidate = folder / "candidate.cmd"
        shutil.copyfile(args.system_image, system_image)
        shutil.copyfile(ROOT / "base/stop.cmd", reference)
        shutil.copyfile(STOP / "stop.cmd", candidate)
        original = session(folder / "original", reference, system_image)
        rebuilt = session(folder / "rebuilt", candidate, system_image)
        if args.dump:
            args.dump.mkdir(parents=True, exist_ok=True)
            for label, frames in (("release", original), ("plm", rebuilt)):
                for name, frame in frames.items():
                    (args.dump / f"{label}-{name}.txt").write_text(text(frame) + "\n")
        verify(original, "release")
        verify(rebuilt, "PL/M")
        compare(original, rebuilt)
    print(f"PASS: {len(original)} identical CDOS/PCE screens, including a real "
          "PIP process stopped on another console")


if __name__ == "__main__":
    main()
