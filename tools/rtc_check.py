#!/usr/bin/env python3
"""Test actual XIOS RTC code with synthetic BIOS services, never a real clock."""

from pathlib import Path
from datetime import date, timedelta
import re, subprocess, tempfile, os

ROOT = Path(os.environ.get("CDOS_TEST_ROOT", Path(__file__).resolve().parent.parent))
CON = ROOT / "kernel/con"
HARNESS = Path(os.environ.get("RTC_TEST_ASM", CON / "tests/rtc_check.asm"))


def check():
    symbols = {
        name: int(v, 16)
        for v, name in re.findall(
            r"\b([0-9A-F]{4})\s+([A-Z][A-Z0-9]*)", (CON / "squid.sym").read_text()
        )
    }
    image = (CON / "xios.con").read_bytes()
    code = bytearray(image[128 : 128 + int.from_bytes(image[1:3], "little") * 16])
    for at, entry in [(0, "RTCSTART"), (4, "IORTCSET")]:
        code[at : at + 4] = (
            b"\xe8"
            + ((symbols[entry] - at - 3) & 65535).to_bytes(2, "little")
            + b"\xcb"
        )
    bcd = lambda n: (n // 10) * 16 + n % 10
    epoch = date(1978, 1, 1)
    cases = []
    for d in [
        epoch,
        date(1980, 2, 29),
        date(1999, 12, 31),
        date(2000, 2, 29),
        date(2026, 10, 29),
        date(2099, 12, 31),
        date(2100, 2, 28),
        date(2100, 3, 1),
        epoch + timedelta(days=65534),
    ]:
        cases.append(dict(day=d, valid=True))
    for mode in [1, 2, 3, 5]:
        cases.append(dict(day=date(2026, 10, 29), mode=mode, valid=False))
    cases.append(dict(day=date(2026, 10, 29), mode=4, valid=True))
    for dc, dd in [
        (0x1977, 0x1231),
        (0x2100, 0x0229),
        (0x2001, 0x0229),
        (0x2026, 0x0431),
        (0x2026, 0x0001),
        (0x2026, 0x1301),
        (0x2026, 0x0100),
        (0x202A, 0x0101),
        (0x2157, 0x1231),
    ]:
        cases.append(dict(day=date(2026, 10, 29), dc=dc, dd=dd, valid=False))
    for tc, td in [(0x2400, 0), (0x1260, 0), (0x1234, 0x6000), (0x1A00, 0)]:
        cases.append(dict(day=date(2026, 10, 29), tc=tc, td=td, valid=False))
    cases += [
        dict(day=date(2026, 10, 29), valid=True, write_fail=1),
        dict(day=date(2026, 10, 29), valid=True, set_day=0),
    ]
    with tempfile.TemporaryDirectory(prefix="cdos-rtc-") as td:
        folder = Path(td)
        (folder / "payload.bin").write_bytes(code)
        for index, c in enumerate(cases):
            d = c["day"]
            mode = c.get("mode", 0)
            valid = c["valid"]
            expected = d + timedelta(days=1 if mode == 4 else 0)
            days = (expected - epoch).days + 1
            dc = c.get("dc", (bcd(d.year // 100) << 8) | bcd(d.year % 100))
            dd = c.get("dd", (bcd(d.month) << 8) | bcd(d.day))
            set_day = c.get("set_day", days)
            sd = epoch + timedelta(days=max(set_day - 1, 0))
            writes = int(valid and set_day != 0)
            vals = dict(
                MODE=mode,
                WRITE_FAIL=c.get("write_fail", 0),
                DATE_C=dc,
                DATE_D=dd,
                TIME_C=c.get("tc", 0x1234),
                TIME_D=c.get("td", 0x5601),
                EXPECT_DAY=days if valid else 0x1234,
                EXPECT_TIME=0x3412 if valid else 0x2211,
                EXPECT_SEC=0x56 if valid else 0x33,
                PRESENT=int(valid),
                DATE_READS={1: 1, 2: 0, 3: 6, 4: 4, 5: 6}.get(mode, 2),
                SET_DAY=set_day,
                DATE_WRITES=writes,
                TIME_WRITES=writes * (not c.get("write_fail", 0)),
                SET_DATE_C=(bcd(sd.year // 100) << 8) | bcd(sd.year % 100),
                SET_DATE_D=(bcd(sd.month) << 8) | bcd(sd.day),
                TOD_DAY=symbols["TODDAY"],
                TOD_HOUR=symbols["TODHOUR"],
                TOD_SEC=symbols["TODSEC"],
                RTC_PRESENT=symbols["RTCPRESENT"],
            )
            (folder / "case.inc").write_text(
                "".join(f"%define {k} {int(v)}\n" for k, v in vals.items())
            )
            subprocess.run(
                [
                    "nasm",
                    "-f",
                    "bin",
                    str(HARNESS),
                    "-I",
                    str(folder) + "/",
                    "-o",
                    str(folder / "test.com"),
                ],
                cwd=folder,
                check=True,
            )
            p = subprocess.run(
                ["emu2", str(folder / "test.com")],
                cwd=folder,
                capture_output=True,
                timeout=5,
            )
            assert p.returncode == 0, (index, c, p.returncode, p.stdout, p.stderr)
    print(
        f"PASS: {len(cases)} built-XIOS RTC cases: startup, fallback, BCD/calendar bounds, century rules, rollover retries, write-back/failure and register preservation."
    )


if __name__ == "__main__":
    check()
