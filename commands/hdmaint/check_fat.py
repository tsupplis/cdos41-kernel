"""Compare the rebuilt FAT loader with both historical copies."""
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
loader = (here / "pcboot3.bin").read_bytes()
bios = (root / "boot/dribio.com").read_bytes()
dos = (root / "boot/dridos.com").read_bytes()
original = (root / "base/hdmaint.cmd").read_bytes()
assert len(loader) == 1280, "Unexpected PCBOOT3 size"
assert bios[:len(loader)] == loader, "PCBOOT3 differs from DRIBIO"
assert not any(bios[len(loader):]), "Unexpected DRIBIO trailing data"
slot = original[0x7280:0x7a80]
assert len(slot) == 2048 and slot == bios[:2048], "Embedded HDMAINT loader differs"
assert len(dos) == 0x4280 and not any(dos), "Unexpected DRIDOS dummy contents"
print("PASS: PCBOOT3 matches DRIBIO and HDMAINT at 7280h; padding and DRIDOS verified")
