"""Compare real SPL machine code with scripted, in-memory BDOS services."""
from pathlib import Path
import struct
import subprocess
import tempfile

SPL = Path(__file__).resolve().parents[1]
ROOT = SPL.parents[1]


def message(command, job=0, device=0, priority=0, copies=0, flags=0,
            data=b"", length=None, status=0, name=b"", faults=0):
    packet = bytearray(160)
    packet[0:2] = bytes((command, job))
    packet[2:2 + len(name)] = name
    packet[13:19] = bytes((status, device, priority, flags, copies, 0))
    struct.pack_into("<H", packet, 23, len(data) if length is None else length)
    packet[32:32 + len(data)] = data
    assert len(packet) == 160 and len(name) <= 11 and len(data) <= 128
    return struct.pack("<H", faults) + packet


def index_image(jobs=()):
    image = bytearray(b" " * (127 * 128))
    for job, device, priority, status in jobs:
        entry = bytearray(64)
        entry[0] = job
        entry[1:12] = b"SAVED   TXT"
        entry[12:18] = bytes((status, device, priority, 0, 2, 2))
        struct.pack_into("<3H", entry, 18, 1, 1, 7)
        entry[24] = 1
        entry[25:36] = b"SPLAA   DSP"
        image[job * 64:(job + 1) * 64] = entry
    return image


def event(job, state=0):
    return message(16, job, data=bytes((state,)) + b"LST000: " + b"\0\0\1\0")


def cases():
    yield "empty", [], {}, 0
    yield "submit-stream-finish-status", [
        message(0), message(1, data=b"A" * 100),
        message(1, data=b"B" * 60), message(7),
        message(3), message(17, status=1), message(17, status=2),
        message(3), event(0), message(3), message(10, 1),
    ], {}, 5
    yield "defaults-and-clamp", [
        message(0, device=1, priority=19, copies=3, flags=1, name=b"HELLO   TXT"),
        message(1, data=b"C" * 128, length=65535),
        message(1, length=0), message(7), message(3), message(17, status=0),
        event(0), message(3),
    ], {}, 4
    yield "eight-submissions", [
        *[message(0) for _ in range(9)],
        message(2, 3), message(0), message(7, 0), message(2, 8),
        message(2, 99), message(7, 99), message(10, 1),
    ], {}, 15
    yield "priority-dispatch-abort", [
        message(0), message(7),
        message(0, priority=180), message(7, 1),
        message(0, priority=10), message(7, 2),
        message(0, priority=10), message(7, 3),
        message(2, 1), event(0), event(2), event(3), message(3),
    ], {}, 10
    yield "active-abort", [
        message(0), message(7), message(2),
        message(17, status=1), event(0), message(3),
    ], {}, 4
    yield "file-errors", [
        message(0, faults=4), message(0, faults=2), message(0),
        message(1, 2, data=b"E" * 128, faults=1), message(7, 2),
        message(3, 2, faults=8), message(3, 2), message(10, 1),
    ], {}, 6
    yield "partial-final-write-error", [
        message(0), message(1, data=b"partial"), message(7, faults=1),
        message(3), event(0),
    ], {}, 3
    yield "two-devices", [
        message(0), message(7), message(0, device=1), message(7, 1),
        message(3), message(3, 1), event(0), event(1), message(3),
    ], {}, 7
    yield "stale-output", [
        message(0, faults=16), message(2), message(255),
    ], {}, 3
    yield "stop-preserve", [
        message(0), message(7), message(0), message(10),
    ], {"DELETE_BUSY": 1}, 3
    yield "stop-delete", [
        message(0), message(7), message(0), message(10, 1),
    ], {"DELETE_BUSY": 1}, 3
    yield "missing-device", [message(0, device=2), message(255)], {}, 2
    for n in range(1, 4):
        yield f"queue-create-failure-{n}", [], {"QFAIL": n}, 0
    yield "recovery-priority", [
        message(3), event(5), event(9), event(1),
        message(0), message(2, 10), message(3),
    ], {"INDEX_EXISTS": 1, "jobs": [(1, 0, 128, 2), (5, 0, 10, 3),
                                  (9, 0, 10, 4), (11, 0, 20, 5)]}, 4
    yield "job-number-wrap", [message(0), message(2, 0)], {
        "INDEX_EXISTS": 1, "jobs": [(253, 0, 128, 2)]
    }, 2
    yield "all-job-numbers-used", [message(0)], {
        "INDEX_EXISTS": 1, "jobs": [(i, 0, 128, 2) for i in range(254)]
    }, 1
    yield "truncated-index", [message(0), message(2)], {
        "INDEX_EXISTS": 1, "INDEX_RECORDS": 0
    }, 2


def execute(folder, binary, requests, options):
    image = binary.read_bytes()
    assert image[0] == 1 and image[9] == 2
    code_size = struct.unpack_from("<H", image, 1)[0] * 16
    data_size = struct.unpack_from("<H", image, 10)[0] * 16
    data_limit = struct.unpack_from("<H", image, 16)[0] * 16 or 65536
    assert len(image) >= 128 + code_size + data_size
    (folder / "code.bin").write_bytes(image[128:128 + code_size])
    (folder / "data.bin").write_bytes(
        image[128 + code_size:128 + code_size + data_size])
    (folder / "messages.bin").write_bytes(b"".join(requests))
    (folder / "index.bin").write_bytes(index_image(options.get("jobs", ())))
    settings = dict(DATA_LIMIT=data_limit, DEVICES=3, INDEX_EXISTS=0, INDEX_RECORDS=127,
                    QFAIL=0, DELETE_BUSY=0)
    settings.update({key: value for key, value in options.items() if key != "jobs"})
    (folder / "case.inc").write_text(
        "".join(f"%define {key} {value}\n" for key, value in settings.items()))
    subprocess.run(["nasm", "-f", "bin", str(SPL / "tests/splcheck.asm"),
                    "-I", str(folder) + "/", "-o", str(folder / "test.com")],
                   check=True, cwd=folder, capture_output=True)
    result = subprocess.run(["emu2", str(folder / "test.com")], cwd=folder,
                            capture_output=True, timeout=15)
    assert result.returncode == 0, (binary.name, result.returncode, result.stderr)
    return result.stdout


def records(trace):
    result = []
    offset = 0
    while offset < len(trace):
        if trace[offset:offset + 8] == b"SPLOUT  ":
            size = 168
        elif trace[offset:offset + 3] == b"DSP":
            size = 168
        else:
            size = {ord("D"): 13, ord("W"): 141, ord("I"): 131, ord("T"): 3}.get(
                trace[offset])
        assert size is not None, (offset, trace[offset:offset + 100])
        assert offset + size <= len(trace)
        result.append(trace[offset:offset + size])
        offset += size
    return result


def check():
    count = 0
    with tempfile.TemporaryDirectory(prefix="cdos-spl-") as directory:
        folder = Path(directory)
        for name, requests, options, replies in cases():
            old = execute(folder, ROOT / "base/spl.cmd", requests, options)
            new = execute(folder, SPL / "splc.cmd", requests, options)
            if old != new:
                at = next((i for i, pair in enumerate(zip(old, new))
                           if pair[0] != pair[1]), min(len(old), len(new)))
                raise AssertionError(
                    f"{name}: trace differs at {at}; lengths {len(old)}/{len(new)}; "
                    f"original={old[at:at+80]!r}, C={new[at:at+80]!r}")
            if options.get("QFAIL"):
                assert old == (b"There was not enough queue buffer space in your "
                               b"system to start the spooler.\r\n")
            else:
                trace = records(old)
                outputs = [r[8:] for r in trace if r.startswith(b"SPLOUT  ")]
                assert len(outputs) == replies, (name, len(outputs), replies)
                if name == "submit-stream-finish-status":
                    assert outputs[0][0:2] == b"\0\0"
                    assert outputs[0][15:19] == b"\x80\0\1\1"
                    assert outputs[2][32 + 12] == 3
                    assert struct.unpack_from("<3H", outputs[2], 32 + 18) == (2, 2, 32)
                    assert outputs[-1][1] == 255
                elif name == "eight-submissions":
                    assert outputs[8][0] == 3
                    assert outputs[10][1] == 8
                elif name == "all-job-numbers-used":
                    assert outputs[0][0] == 4
                elif name == "priority-dispatch-abort":
                    dispatch = [r[9] for r in trace
                                if r.startswith(b"DSP") and r[8] == 0]
                    assert dispatch == [0, 2, 3], dispatch
                elif name == "file-errors":
                    assert [p[0] for p in outputs] == [2, 2, 0, 2, 1, 0]
                elif name == "partial-final-write-error":
                    assert outputs[1][0] == 0
                elif name == "stale-output":
                    assert sum(r == b"T\x0a\0" for r in trace) == 6
            count += 1
            print(f"PASS: {name}", flush=True)
        requests = [
            message(0, device=16), message(0, device=255),
            message(2, 255), message(7, 255), message(0), message(7),
            message(3, 255), message(1, 255), event(255), message(17, 255),
        ]
        trace = execute(folder, SPL / "splc.cmd", requests, {})
        for diagnostic in (
            b"SPL: append for unknown job\r\n",
            b"SPL: event for unknown job\r\n",
            b"SPL: report for unknown job\r\n",
        ):
            assert trace.count(diagnostic) == 1
            trace = trace.replace(diagnostic, b"")
        outputs = [r[8:] for r in records(trace) if r.startswith(b"SPLOUT  ")]
        assert [p[0] for p in outputs] == [1, 1, 1, 1, 0, 0, 1]
        print("PASS: C-only malformed-message guards")
    print(f"PASS: {count} paired SPL assembly/C machine-code scenarios")


if __name__ == "__main__":
    check()
