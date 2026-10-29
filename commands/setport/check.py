"""Compare complete CMDs, allowing only documented same-length encodings.

The expected image is adjusted in memory for comparison only. Neither the
reference nor the built CMD is modified. No ranges are ignored or masked.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

REFERENCE_SHA256 = '0facfea0a25a91a5182799fec4612a0f5f1eb9e2cdffe362b39ff5ff2efcde01'
ROOT = Path(__file__).resolve().parent


def equivalent(old, new):
    # Reverse the register/register D bit and the ModR/M register fields.
    if len(old) == len(new) == 2 and old[0] in (0x88, 0x89, 0x31):
        if old[1] & 0xc0 != 0xc0:
            return False
        return new == bytes((old[0] | 2,
                             0xc0 | ((old[1] & 7) << 3) | ((old[1] >> 3) & 7)))
    # CMP AX, sign-extended imm8 versus CMP AX, imm16: both occupy 3 bytes.
    return old == bytes.fromhex('83f83f') and new == bytes.fromhex('3d3f00')


def expected_image(reference):
    original = reference.read_bytes()
    if hashlib.sha256(original).hexdigest() != REFERENCE_SHA256:
        raise ValueError('historical SETPORT reference has changed')
    expected = bytearray(original)
    entries = json.loads((ROOT / 'encodings.json').read_text())
    if len(entries) != 39:
        raise ValueError('expected precisely 39 documented encoding exceptions')
    used = set()
    for entry in entries:
        offset = 128 + int(entry['offset'], 16)
        old, new = (bytes.fromhex(entry[key]) for key in ('original', 'assembled'))
        span = set(range(offset, offset + len(old)))
        if used & span or not equivalent(old, new):
            raise ValueError(f'invalid/overlapping encoding exception at {offset-128:04X}h')
        if original[offset:offset+len(old)] != old:
            raise ValueError(f'original instruction mismatch at {offset-128:04X}h')
        expected[offset:offset+len(old)] = new
        used.update(span)
    return bytes(expected)


def check_source(path):
    code = False
    instructions = 0
    data_label = None
    allowed = {'copyright', 'utility_alignment', 'help_copyright', 'code_padding'}
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.split(';', 1)[0].strip().lower()
        if not line:
            continue
        if line == 'cseg':
            code = True
            continue
        if line == 'dseg':
            code = False
        if not code:
            continue
        if line.startswith('org'):
            continue
        label = re.match(r'^(\w+):(?:\s|$)', line)
        if label:
            data_label = label[1]
            line = line[label.end():].strip()
        else:
            label = re.match(r'^(\w+)\s+(d[bw])\s', line)
            if label:
                data_label = label[1]
                line = line[len(label[1]):].strip()
        if not line:
            continue
        if line.split()[0] in ('db', 'dw', 'rb', 'rw'):
            if data_label not in allowed:
                raise ValueError(f'{path}:{number}: raw data inside executable code')
        else:
            instructions += 1
    if instructions != 2950:
        raise ValueError(f'{path}: expected 2950 mnemonic instructions, found {instructions}')


def main():
    reference = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '../../base/setport.cmd'
    expected = expected_image(reference)
    for name in ('setporg', 'setport'):
        check_source(ROOT / (name + '.a86'))
        actual = (ROOT / (name + '.cmd')).read_bytes()
        if actual != expected:
            first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
                         min(len(actual), len(expected)))
            raise ValueError(f'{name}.cmd: unexpected difference at file offset {first:04X}h; '
                             f'length {len(actual)}, expected {len(expected)}')
    print('PASS: both complete SETPORT CMDs match the original with exactly 39 verified')
    print('same-length encoding exceptions; all other bytes and offsets are unchanged.')
    print('PASS: both sources contain 2950 mnemonic instructions and no raw code bytes.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        sys.exit(str(error))
