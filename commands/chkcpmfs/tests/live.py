"""Check CHKCPMFS on disposable CP/M and FAT media under live CDOS."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

COMMAND = Path(__file__).resolve().parents[1]
ROOT = COMMAND.parents[1]
MEDIA = ROOT / "media"
FORMAT = "ccpm86-320"
DIRECTORY = 4096


def run(*args, cwd, **kwargs):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, **kwargs)


def convert(source, target, direction):
    run(sys.executable, str(ROOT / "tools/cpm86twist.py"),
        direction, str(source), str(target), cwd=MEDIA)


def copy_to_cpm(image, source, target):
    run("cpmcp", "-f", FORMAT, str(image), str(source), target, cwd=MEDIA)


def directory_entries(image):
    data = image.read_bytes()
    return [(at, data[at:at + 32])
            for at in range(DIRECTORY, DIRECTORY + 64 * 32, 32)
            if data[at] <= 15]


def prepare_system(folder):
    logical = folder / "system-logical.img"
    convert(MEDIA / "cdos86.img", logical, "untwist")
    copy_to_cpm(logical, COMMAND / "chkcpmfs.cmd", "0:CHKCPMFS.CMD")
    entries = directory_entries(logical)
    system = [record for _, record in entries if record[1:12] == b"CCPM    SYS"]
    assert system and any(any(record[16:32]) for record in system)
    references = sum(sum(block != 0 for block in record[16:32])
                     for _, record in entries)
    image = folder / "system-source.img"
    convert(logical, image, "twist")
    return image, len(entries), references


def prepare_data(folder):
    logical = folder / "data-logical.img"
    convert(MEDIA / "cdos86base.img", logical, "untwist")
    for user, name in ((0, "CCPM.SYS"), (1, "SECOND.DAT"), (15, "THIRD.DAT")):
        source = folder / name
        source.write_bytes((name + "\r\n").encode("ascii") * 12)
        copy_to_cpm(logical, source, f"{user}:{name}")
    entries = directory_entries(logical)
    system = next((at, record) for at, record in entries
                  if record[0] == 0 and record[1:12] == b"CCPM    SYS")
    second = next((at, record) for at, record in entries
                  if record[0] == 1 and record[1:12] == b"SECOND  DAT")
    assert system[1][16] != 0 and second[1][16] != 0
    assert system[1][16] != second[1][16]

    clean = folder / "data-clean-source.img"
    convert(logical, clean, "twist")
    data = bytearray(logical.read_bytes())
    data[second[0] + 16] = system[1][16]
    logical.write_bytes(data)
    bad = folder / "data-crosslink-source.img"
    convert(logical, bad, "twist")
    return clean, bad, system[1][16]


def prepare_fat(folder, name, *, label=False, sentinel=False):
    image = folder / f"{name}-source.img"
    args = ["mformat", "-C", "-i", str(image), "-t", "40", "-h", "2",
            "-n", "8", "-c", "2"]
    if label:
        args.extend(["-v", "CHECKDISK"])
    run(*args, "::", cwd=folder)
    if sentinel:
        source = folder / "sentinel.txt"
        source.write_bytes(b"untouched FAT sentinel\r\n")
        run("mcopy", "-i", str(image), str(source), "::SENTINEL.TXT", cwd=folder)
    return image


def boot(folder, system, second, drive):
    shutil.copyfile(system, folder / "system.img")
    shutil.copyfile(second, folder / "second.img")
    before_system = (folder / "system.img").read_bytes()
    before_second = (folder / "second.img").read_bytes()
    config = (MEDIA / "cdos86.cfg").read_text()
    config = config.replace('driver = "sdl"', 'driver = "null"')
    config = config.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
    config = config.replace('file     = "cdos86.img"', 'file     = "system.img"')
    config = config.replace('file     = "cdostools.img"', 'file     = "second.img"')
    (folder / "cdos86.cfg").write_text(config)

    commands = ["c f000000"]
    keys = {":": "+Shift Semicolon -Shift", "\n": "Return", " ": "Space"}

    def type_command(text):
        for character in text:
            commands.extend(["key " + keys.get(character, character), "c 200000"])
        commands.append("c 4000000")

    if drive == "B":
        type_command("b:\n")
        type_command("cls\n")
        type_command("a:chkcpmfs\n")
    else:
        type_command("chkcpmfs\n")
    commands.extend(['save "screen.bin" bin b800:0000 fa0', "q"])
    result = subprocess.run(
        ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
        cwd=folder, input=("\n".join(commands) + "\n").encode(),
        capture_output=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout.decode(errors="replace")[-4000:]
    video = (folder / "screen.bin").read_bytes()
    assert len(video) == 4000
    screen = "\n".join(
        "".join(chr(value) if 32 <= value < 127 else " "
                for value in video[at:at + 160:2]).rstrip()
        for at in range(0, 4000, 160)
    )
    assert (folder / "system.img").read_bytes() == before_system, (drive, screen)
    assert (folder / "second.img").read_bytes() == before_second, (drive, screen)
    return screen


def main():
    with tempfile.TemporaryDirectory(prefix="chkcpmfs-live-") as directory:
        folder = Path(directory)
        system, entries, references = prepare_system(folder)
        clean, bad, shared = prepare_data(folder)
        fat_empty = prepare_fat(folder, "fat-empty")
        fat_label = prepare_fat(folder, "fat-label", label=True)
        fat_file = prepare_fat(folder, "fat-file", sentinel=True)

        screen = boot(folder, system, clean, "A")
        assert "Drive A  DPB block shift" in screen, screen
        assert (f"Directory entries scanned: {entries}  "
                f"block references checked: {references}") in screen, screen
        assert "Consistency errors: 0" in screen and "ERROR:" not in screen, screen
        assert "skipped" not in screen.lower(), screen

        screen = boot(folder, system, clean, "B")
        assert "Drive B  DPB block shift" in screen, screen
        assert "Directory entries scanned: 3  block references checked: 3" in screen, screen
        assert "Consistency errors: 0" in screen and "ERROR:" not in screen, screen

        screen = boot(folder, system, MEDIA / "cdos86base.img", "B")
        assert "Drive B  DPB block shift" in screen, screen
        assert "Directory entries scanned: 0  block references checked: 0" in screen, screen
        assert "Consistency errors: 0" in screen and "ERROR:" not in screen, screen

        screen = boot(folder, system, bad, "B")
        assert "Drive B  DPB block shift" in screen, screen
        assert re.search(r"USER 1 FILE SECOND\s+\.DAT: BLOCK "
                         + str(shared) + r" IS REFERENCED MORE THAN ONCE", screen), screen
        assert "Consistency errors: 1" in screen, screen

        for fat in (fat_empty, fat_label, fat_file):
            screen = boot(folder, system, fat, "B")
            assert "DOS media detected; no CP/M filesystem scan performed." in screen, screen
            assert "Directory entries scanned:" not in screen, screen
    print(f"PASS: live CDOS system ({entries} entries, {references} references), "
          "all-user and empty CP/M disks, cross-link, FAT refusal; images unchanged")


if __name__ == "__main__":
    main()
