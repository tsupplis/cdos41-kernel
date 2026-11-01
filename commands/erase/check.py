"""Complete-file 4.11 comparison with exact linker/serial exceptions."""
from pathlib import Path
import hashlib, struct
root = Path(__file__).resolve().parent
original = (root / '../../base/erase.exe').read_bytes()
assert hashlib.sha256(original).hexdigest() == '952abb7ecad67b91b1c890a626b593240ef960b9aed517504bbb99d099019a89'
expected = bytearray(original)
assert len(expected) == 1536
assert expected[0x22b:0x23b] == b'1031-0000       '
expected[0x22b:0x23b] = b'XXXX-0000-654321'
assert struct.unpack_from('<H', expected, 4)[0] == 3
assert struct.unpack_from('<H', expected, 14)[0] == 0x37
# LINK86 shifts the 128-byte stack by one paragraph into zero reserve and
# emits one additional zero-filled 512-byte page; no code or data changes.
assert not any(expected[0x570:])
expected.extend(bytes(512))
struct.pack_into('<H', expected, 4, 4)
struct.pack_into('<H', expected, 14, 0x38)
struct.pack_into('<H', expected, 18, 0)
struct.pack_into('<H', expected, 18, (-sum(struct.unpack('<1024H', expected))) & 0xffff)
assert (root / 'erase.exe').read_bytes() == expected, 'Unexpected ERASE difference'
print('PASS: ERASE matches 4.11 except exact serial/header/zero-padding differences')
