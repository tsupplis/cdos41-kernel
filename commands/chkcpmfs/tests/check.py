"""Exercise the actual CHKCPMFS binary with synthetic BDOS directory records."""
from pathlib import Path
import struct
import subprocess
import tempfile

COMMAND = Path(__file__).resolve().parents[1]


def entry(name, blocks=(), *, user=0, extent=0, records=0, module=0, wide=False):
    stem, suffix = name.upper().split(".")
    assert 0 < len(stem) <= 8 and len(suffix) <= 3
    result = bytearray(32)
    result[0] = user
    result[1:12] = (stem.ljust(8) + suffix.ljust(3)).encode("ascii")
    result[12], result[14], result[15] = extent, module, records
    assert len(blocks) <= (8 if wide else 16)
    for index, block in enumerate(blocks):
        if wide:
            struct.pack_into("<H", result, 16 + index * 2, block)
        else:
            result[16 + index] = block
    return bytes(result)


def cases():
    system = [
        entry("CCPM.SYS", range(start, start + count), extent=extent, records=rc)
        for start, count, extent, rc in (
            (1, 16, 1, 128), (17, 16, 3, 128), (33, 16, 5, 128),
            (49, 16, 7, 128), (65, 16, 9, 128), (81, 14, 11, 88))
    ]
    other_users = [
        entry("USER1.TXT", [95], user=1, records=1),
        entry("USER15.TXT", [96], user=15, records=1),
    ]
    yield "system-and-users", system + other_users, {}, [
        "Directory entries scanned: 8  block references checked: 96",
        "Consistency errors: 0",
    ]
    yield "crosslink-system", system + [
        entry("USER1.TXT", [1], user=1, records=1),
    ], {}, [
        "USER 1 FILE USER1   .TXT: BLOCK 1 IS REFERENCED MORE THAN ONCE",
        "Consistency errors: 1",
    ]
    yield "sparse", [entry("SPARSE.DAT", [1, 0, 3], records=48)], {}, [
        "block references checked: 2", "Consistency errors: 0",
    ]
    yield "allocated-past-record-count", [
        entry("FIRST.DAT", [1, 0, 0, 2], records=16),
        entry("SECOND.DAT", [2], records=1),
    ], {}, [
        "block references checked: 3",
        "BLOCK 2 IS REFERENCED MORE THAN ONCE",
        "Consistency errors: 1",
    ]
    yield "reserved-both-bytes", [
        entry("RESERVED.DAT", [2, 9], records=32),
    ], {"AL0": 0xA0, "AL1": 0x40}, [
        "BLOCK 2 IS RESERVED FOR THE DIRECTORY",
        "BLOCK 9 IS RESERVED FOR THE DIRECTORY",
        "Consistency errors: 2",
    ]
    yield "wide-blocks", [
        entry("FIRST.DAT", [300, 600], records=32, wide=True),
        entry("SECOND.DAT", [300, 601], records=32, wide=True),
    ], {"DSM": 600, "EXM": 0}, [
        "block references checked: 4",
        "BLOCK 300 IS REFERENCED MORE THAN ONCE",
        "BLOCK 601 IS OUTSIDE THE DISK",
        "Consistency errors: 2",
    ]
    yield "invalid-extent", [
        entry("BAD.DAT", [1], extent=0x20, module=0x40, records=129),
    ], {}, [
        "RECORD COUNT EXCEEDS 128",
        "RESERVED EXTENT BITS ARE SET",
        "Consistency errors: 2",
    ]
    yield "special-and-empty", [
        entry("LABEL.DAT", user=0x20),
        entry("STAMP.DAT", user=0x21),
        entry("XFCB.DAT", user=0x10),
        entry("DELETED.DAT", user=0xE5),
    ], {}, [
        "Directory entries scanned: 0  block references checked: 0",
        "Consistency errors: 0",
    ]
    yield "empty-directory", [], {}, [
        "Directory entries scanned: 0  block references checked: 0",
        "Consistency errors: 0",
    ]
    yield "dos-media", [], {
        "DOS_MEDIA": 1, "EXPECTED_SEARCHES": 1, "EXPECTED_DMA_SETS": 2,
    }, ["DOS media detected; no CP/M filesystem scan performed."]
    yield "unsupported-dpb", [], {
        "BSH": 8, "EXPECTED_SEARCHES": 1, "EXPECTED_DMA_SETS": 2,
    }, ["ERROR: unsupported DPB block shift; scan stopped."]


def run_case(folder, image, name, entries, overrides, expected):
    assert image[0] == 1 and image[9] == 2, "unexpected CMD segment layout"
    code_size = struct.unpack_from("<H", image, 1)[0] * 16
    data_size = struct.unpack_from("<H", image, 10)[0] * 16
    assert len(image) >= 128 + code_size + data_size
    (folder / "code.bin").write_bytes(image[128:128 + code_size])
    (folder / "data.bin").write_bytes(
        image[128 + code_size:128 + code_size + data_size])
    directory = b"".join(entries)
    directory += bytes(max(128, (len(directory) + 127) // 128 * 128) - len(directory))
    (folder / "directory.bin").write_bytes(directory)
    settings = {
        "DIR_ENTRIES": len(entries), "BSH": 4, "EXM": 1, "DSM": 157,
        "AL0": 0x80, "AL1": 0, "DOS_MEDIA": 0, "INITIAL_DMA": 0x80,
        "EXPECTED_SEARCHES": 2, "EXPECTED_DMA_SETS": 4,
    }
    settings.update(overrides)
    (folder / "case.inc").write_text(
        "".join(f"%define {key} {value}\n" for key, value in settings.items()))
    subprocess.run(
        ["nasm", "-f", "bin", str(COMMAND / "tests/check.asm"),
         "-I", str(folder) + "/", "-o", str(folder / "check.com")],
        cwd=folder, check=True, capture_output=True,
    )
    result = subprocess.run(
        ["emu2", str(folder / "check.com")], cwd=folder,
        capture_output=True, timeout=15,
    )
    output = result.stdout.decode("ascii", errors="replace")
    assert result.returncode == 0, (name, result.returncode, output, result.stderr)
    for text in expected:
        assert text in output, (name, text, output)
    if "Consistency errors: 0" in expected:
        assert "ERROR:" not in output, (name, output)
    if not overrides.get("DOS_MEDIA") and overrides.get("BSH", 4) <= 7:
        assert "skipped" not in output.lower(), (name, output)
    return output


def main():
    image = (COMMAND / "chkcpmfs.cmd").read_bytes()
    with tempfile.TemporaryDirectory(prefix="chkcpmfs-bdos-") as directory:
        folder = Path(directory)
        total = 0
        for name, entries, overrides, expected in cases():
            run_case(folder, image, name, entries, overrides, expected)
            total += 1
    print(f"PASS: {total} CHKCPMFS synthetic BDOS and DMA cases")


if __name__ == "__main__":
    main()
