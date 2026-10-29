#!/usr/bin/env python3
"""Compare retained SHOW 3.3 with the maintained build under CDOS 4.1."""

from pathlib import Path
import contextlib, datetime, re, shutil, struct, subprocess, sys, tempfile
from alias_check import ROOT as R


@contextlib.contextmanager
def workspace():
    folder = Path(tempfile.mkdtemp(prefix="cdos-show-"))
    try:
        yield folder
    except BaseException:
        print("SHOW diagnostics retained in", folder, flush=True)
        raise
    else:
        shutil.rmtree(folder)


def fat_free(b):
    sector = struct.unpack_from("<H", b, 11)[0]
    cluster = b[13]
    reserved = struct.unpack_from("<H", b, 14)[0]
    tables = b[16]
    root = struct.unpack_from("<H", b, 17)[0]
    total = struct.unpack_from("<H", b, 19)[0]
    size = struct.unpack_from("<H", b, 22)[0]
    count = (
        total - reserved - tables * size - (root * 32 + sector - 1) // sector
    ) // cluster
    fat = b[reserved * sector :]
    free = 0
    for i in range(2, count + 2):
        v = struct.unpack_from("<H", fat, i * 3 // 2)[0]
        v = (v >> 4) if i & 1 else (v & 0xFFF)
        if v == 0:
            free += 1
    return free * cluster * sector // 1024


def check(no_label=False, create=False, access=False):
    with workspace() as F:

        def run(*args):
            return subprocess.run(args, cwd=F, check=True, capture_output=True)

        shutil.copyfile(R / "media/cdos86.img", F / "cdos86.img")
        shutil.copyfile(R / "media/diskdefs", F / "diskdefs")
        run(
            "mformat",
            "-C",
            "-i",
            "fat.img",
            "-t",
            "40",
            "-h",
            "2",
            "-n",
            "8",
            "-c",
            "2",
            "::",
        )
        for src, name in [
            (R / "base/show.cmd", "OSHOW.CMD"),
            (R / "commands/show/show.cmd", "NSHOW.CMD"),
        ]:
            run("mcopy", "-i", "fat.img", str(src), "::" + name)
        run("mmd", "-i", "fat.img", "::ADIR")
        (F / "one.txt").write_bytes(b"fixture\r\n\x1a")
        run("mcopy", "-i", "fat.img", "one.txt", "::ADIR/CHILD.TXT")
        twist = str(R / "tools/cpm86twist.py")
        run("python3", twist, "untwist", "cdos86.img", "logical.img")
        run("cpmcp", "-f", "ccpm86-320", "logical.img", "one.txt", "1:one.txt")
        b = bytearray((F / "logical.img").read_bytes())
        for at in range(4096, 6144, 32):
            if b[at] == 0xE5 and not no_label:
                label = bytearray(32)
                label[0] = 0x20
                label[1:12] = b"SHOWTEST   "
                label[12] = 0x61 if access else (0x31 if create else 0x21)
                for off, date in [
                    (24, datetime.date(2000, 2, 29)),
                    (28, datetime.date(2026, 10, 29)),
                ]:
                    struct.pack_into(
                        "<HBB",
                        label,
                        off,
                        (date - datetime.date(1978, 1, 1)).days + 1,
                        0x12,
                        0x34,
                    )
                b[at : at + 32] = label
                break
        (F / "logical.img").write_bytes(b)
        run("python3", twist, "twist", "logical.img", "cdos86.img")
        cfg = (
            (R / "media/cdos86.cfg")
            .read_text()
            .replace('driver = "sdl"', 'driver = "null"')
            .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
            .replace('file     = "cdostools.img"', 'file     = "fat.img"')
        )
        (F / "cdos86.cfg").write_text(cfg)
        cases = [
            "a:space",
            "b:space",
            "a:drive",
            "b:drive",
            "a:users",
            "b:users",
            "a:label",
            "b:label",
            "help",
            "open",
            "locked",
            "bogus",
            "[space]",
            "a:space b:drive",
            "",
            "drive",
            "b:",
            "[b:users]",
            "a:label b:users",
            "n:space",
            "[users]",
            "label",
        ]
        if no_label:
            cases = ["a:label", "b:label"]
        if create or access:
            cases = ["a:label"]
        initial_fat_free = fat_free((F / "fat.img").read_bytes())
        used = {0}
        for at in range(4096, 6144, 32):
            if b[at] < 16:
                used.update(x for x in b[at + 16 : at + 32] if x)
        initial_cpm_free = (158 - len(used)) * 2
        cmds = ["c f000000"]
        keys = {" ": "Space", "[": "LeftBracket", "]": "RightBracket", ".": "Period"}
        for i, tail in enumerate(cases):
            for v in ["O", "N"]:
                text = f"put [b:{v}{i}.txt] b:{v.lower()}show.cmd {tail}"
                for c in text:
                    cmds += [
                        "key "
                        + ("+Shift Semicolon -Shift" if c == ":" else keys.get(c, c)),
                        "c 200000",
                    ]
                cmds += [
                    "key Return",
                    "c 4000000",
                    f'save "{v}{i}.bin" bin b800:0000 fa0',
                ]
        cmds += ["q"]
        with (F / "pce.log").open("wb") as log:
            p = subprocess.run(
                ["pce-ibmpc", "-c", "cdos86.cfg", "-t", "null", "-g", "vga"],
                cwd=F,
                input=("\n".join(cmds) + "\n").encode(),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=400,
            )
        assert not p.returncode

        for i, tail in enumerate(cases):
            outputs = []
            for v in ["O", "N"]:
                label = v + str(i)
                data = (F / (label + ".bin")).read_bytes()
                rows = [
                    "".join(
                        chr(c) if 32 <= c < 127 else " " for c in data[j : j + 160 : 2]
                    ).strip()
                    for j in range(0, 3840, 160)
                ]
                assert [x for x in rows if x][-1] == "A>", (tail, v, rows)
                dst = F / (label + ".txt")
                run("mcopy", "-o", "-i", "fat.img", "::" + dst.name, str(dst))
                outputs.append(dst.read_bytes().rstrip(b"\x1a").decode("ascii"))
            old, new = outputs

            def normalize(text):
                text = re.sub(r"SHOW (2\.1|3\.3)", "SHOW #", text)
                return re.sub(r"(Space:)\s+\d+k", r"\1 #k", text)

            assert normalize(old) == normalize(new), (tail, old, new)
            if tail == "a:space":
                assert int(re.search(r"Space:\s+(\d+)k", new)[1]) == initial_cpm_free, (
                    initial_cpm_free,
                    new,
                )
            if tail == "b:space":
                assert (
                    int(re.search(r"Space:\s+(\d+)k", old)[1]) == initial_fat_free - 2
                ), (initial_fat_free, old)
                assert (
                    int(re.search(r"Space:\s+(\d+)k", new)[1]) == initial_fat_free - 3
                ), (initial_fat_free, new)
            if tail in ("", "[space]"):
                assert "N:" not in new and "O:" not in new and "P:" not in new, new
            if tail in ("b:users", "b:label", "[b:users]"):
                assert "requires CP/M media." in new and "01/00/78" not in new, new
            if tail == "a:users":
                assert re.search(r"Active Files:\s+0\s+1", new), new
            if tail in ("a:label", "locked", "label"):
                if no_label:
                    assert "No Directory Label exists" in new, new
                else:
                    assert (
                        "SHOWTEST." in new
                        and "02/29/00 12:34" in new
                        and "10/29/26 12:34" in new
                    ), new
                    labelrow = next(
                        x for x in new.splitlines() if x.startswith("SHOWTEST.")
                    )
                    assert (
                        ("off     on" in labelrow)
                        if (create or access)
                        else ("off     off" in labelrow)
                    ), new
            if tail in ("open", "bogus"):
                assert "Invalid Option" in new, new
        print(
            f"PASS: SHOW {len(cases)} OEM/rebuilt CP/M/FAT12 cases, capacities/free space, users/media guards, labels/Y2K and option dispatch; disposable images only"
        )


if __name__ == "__main__":
    check("--no-label" in sys.argv, "--create" in sys.argv, "--access" in sys.argv)
