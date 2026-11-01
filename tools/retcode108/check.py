"""Boot a disposable CDOS system and exercise native program return codes."""
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
MEDIA = HERE.parents[1] / "media"


def check(folder):
    def run(args, cwd):
        subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.DEVNULL)

    probes = []
    for source in sorted(HERE.glob("*.a86")):
        shutil.copy(source, folder)
        run(["cpm86_asm86", source.name], folder)
        run(["cpm86_gencmd", source.stem + ".h86"], folder)
        probes.append(folder / (source.stem + ".cmd"))

    shutil.copy(MEDIA / "cdos86.img", folder)
    twist = ["python3", HERE.parent / "cpm86twist.py"]
    logical = folder / "probes.img"
    run(twist + ["untwist", MEDIA / "cdos86base.img", logical], MEDIA)
    run(["cpmcp", "-f", "ccpm86-320", logical, *probes, "0:"], MEDIA)
    run(twist + ["twist", logical, folder / "cdostools.img"], MEDIA)
    config = (MEDIA / "cdos86.cfg").read_text().replace('"sdl"', '"null"')
    (folder / "cdos86.cfg").write_text(config.replace('"sdl:lowpass=5000"', '"null"'))

    commands = ["c f000000"]

    def key(name):
        commands.extend(["key " + name, "c 180000"])

    def launch(name):
        for char in "b:" + name:
            key("+Shift Semicolon -Shift" if char == ":" else char)
        key("Return")
        commands.append("c 2000000")

    def capture(name):
        commands.append(f'save "{name}.bin" bin b800:0000 fa0')

    launch("rparent")
    capture("chain")
    launch("rctrl")
    capture("waiting")
    key("+Ctrl c -Ctrl")
    commands.append("c 3000000")
    capture("abort")
    launch("rdisk")
    capture("fatal")
    launch("rhold")
    capture("held")
    key("+Ctrl +Alt 2 -Alt -Ctrl")
    launch("rparent")
    capture("second")
    key("+Ctrl +Alt 1 -Alt -Ctrl")
    key("x")
    commands.append("c 2000000")
    capture("first")
    commands.append("q")
    with (folder / "monitor.log").open("wb") as log:
        subprocess.run(["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
                       cwd=folder, input=("\n".join(commands) + "\n").encode(),
                       stdout=log, stderr=subprocess.STDOUT, timeout=150, check=True)

    for name, markers in {
        "chain": ["PASS rleaf", "PASS rparent"],
        "waiting": ["CTRL-C READY"],
        "abort": ["PASS rctrl"],
        "fatal": ["Read/Only Disk", "PASS rdisk"],
        "held": ["ISOLATION READY"],
        "second": ["PASS rparent"],
        "first": ["PASS rhold"],
    }.items():
        screen = (folder / (name + ".bin")).read_bytes()[::2].decode("cp437")
        if "FAIL " in screen or any(marker not in screen for marker in markers):
            raise RuntimeError(f"{name}: {screen}")
    print("PASS: BDOS 108 launch, chain, parent status, Ctrl-C, disk error and console isolation")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="cdos-retcode-") as tmp:
        check(Path(tmp))
