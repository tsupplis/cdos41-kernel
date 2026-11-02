"""Compare STOP reports in disposable Concurrent DOS/PCE sessions."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


STOP = Path(__file__).resolve().parents[1]
ROOT = STOP.parents[1]
KEYS = {" ": "Space", ":": "+Shift Semicolon -Shift", ".": "Period"}
ROW = re.compile(r"^\s*(\*\*|\d+\.)\s+(.+?)\s+\d+K\s+(\d+)\s*$")


def session(folder, binary):
    folder.mkdir()
    shutil.copyfile(ROOT / "media/cdos86.img", folder / "cdos86.img")
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

    def enter(text):
        for key in text:
            script.extend(["key " + KEYS.get(key, key), "c 200000"])
        script.extend(["key Return", "c 5000000"])

    def capture(number):
        script.append(f'save "s{number}.bin" bin b800:0000 fa0')

    enter("b:")
    enter("cls")
    enter("b:stop.cmd")
    capture(0)
    enter("99")
    capture(1)
    enter("cls")
    enter("b:stop.cmd x")
    capture(2)
    enter("cls")
    enter("b:stop.cmd")
    capture(3)
    enter("")
    capture(4)
    script.append("q")

    result = subprocess.run(
        ["pce-ibmpc", "-c", "cfg", "-t", "null", "-g", "vga"],
        cwd=folder, input=("\n".join(script) + "\n").encode(),
        capture_output=True, timeout=240, check=True,
    )
    if b"unknown key:" in result.stdout or b"unknown key:" in result.stderr:
        raise RuntimeError(f"PCE rejected a key: {result.stdout!r} {result.stderr!r}")

    screens = []
    for number in range(5):
        frame = (folder / f"s{number}.bin").read_bytes()
        if len(frame) != 4000:
            raise ValueError(f"{folder}: invalid VGA screen length: {len(frame)}")
        screens.append("\n".join(
            frame[i:i + 160:2].decode("cp437").rstrip()
            for i in range(0, len(frame), 160)
        ).strip())
    return screens


def rows(screen):
    return [match.groups() for line in screen.splitlines()
            if (match := ROW.fullmatch(line))]


def verify(screens, label):
    for index in (0, 2, 3):
        screen = screens[index]
        for text in ("Entry   Program   Memory   Window",
                     "Contiguous Blocks of Free Memory", "Free Shared Code",
                     "Total Free Memory"):
            if text not in screen:
                raise AssertionError(f"{label} screen {index} missing {text!r}:\n{screen}")
        if not rows(screen):
            raise AssertionError(f"{label} screen {index} has no process rows:\n{screen}")
    for index in (0, 3):
        if "Enter the Number to delete or RETURN to exit" not in screens[index]:
            raise AssertionError(f"{label} screen {index} missing prompt:\n{screens[index]}")
    if "Entry number too large" not in screens[1]:
        raise AssertionError(f"{label} did not reject entry 99:\n{screens[1]}")
    if "Enter the Number to delete or RETURN to exit" in screens[2]:
        raise AssertionError(f"{label} prompted with a command tail:\n{screens[2]}")
    for index in (1, 2, 4):
        if not re.search(r"(?m)^B>\s*$", screens[index]):
            raise AssertionError(f"{label} screen {index} did not return to the shell:\n{screens[index]}")


def main():
    with tempfile.TemporaryDirectory(prefix="cdos-stop-live-") as directory:
        folder = Path(directory)
        original = session(folder / "original", ROOT / "base/stop.cmd")
        rebuilt = session(folder / "rebuilt", STOP / "stop.cmd")
        verify(original, "release")
        verify(rebuilt, "PL/M")
        for index in (0, 2, 3):
            if rows(original[index]) != rows(rebuilt[index]):
                raise AssertionError(
                    f"process rows differ on screen {index}:\n"
                    f"release: {rows(original[index])}\nPL/M: {rows(rebuilt[index])}"
                )
    print("PASS: paired CDOS/PCE reports, command tail, rejected entry and return")


if __name__ == "__main__":
    main()
