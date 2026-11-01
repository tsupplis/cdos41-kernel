"""Compare the complete PATH.EXE against the 4.11 release."""
from pathlib import Path
import hashlib
import struct

here = Path(__file__).resolve().parent
original = (here / '../../base/path.exe').read_bytes()
assert hashlib.sha256(original).hexdigest() == 'e69ce810865ca8134b7a1ecb4def68b77033c7bab17f75dfe8964389e769bf3a'

expected = bytearray(original)
# The startup JMP skips the four LINK86 identification bytes in both builds.
assert original[0x300:0x302] == bytes.fromhex('eb10')
expected[0x30c:0x310] = bytes.fromhex('01010208')

# The backward group mover is entered only for nonzero paragraph displacement.
# Its descriptors give (stored, minimum, maximum) in paragraphs. Minimum equals
# stored for every group, and none requests extra space. Every displacement
# computed from the cumulative (allocated - stored) sizes is therefore zero.
groups = list(struct.iter_unpack('<HHH', original[0x200:0x230]))
assert groups == [(20,20,0),(24,24,0)] + [(0,0,0)] * 6
assert original[0x47b:0x47e] == bytes.fromhex('be0f00')
expected[0x47c] = 0x0e

# Five entry NOPs in the original. All branches/calls within the 314-byte
# command body are relative. Absolute operands refer to data or the PSP.
assert original[0x600:0x605] == b'\x90' * 5
expected[0x600:0x73f] = original[0x605:0x73f] + bytes(5)

struct.pack_into('<H', expected, 0x12, 0)
checksum = -sum(word for word, in struct.iter_unpack('<H', expected)) & 0xffff
struct.pack_into('<H', expected, 0x12, checksum)
assert (here/'path.exe').read_bytes() == expected, 'Unexpected difference from the 4.11 PATH executable'
print('PASS: complete PATH executable matches with documented startup, padding and checksum differences')
