"""Compare whole kernel files after scripted saves by N and NKEY."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent / 'base'


def scripted_command(original, language, keyboard):
    # Substitute the menu choices in a disposable copy of the verified CMD.
    # Keep the loader, allocator, MSG reader, complete save and BDOS I/O.
    image = bytearray(original)
    def patch(offset, code):
        image[128 + offset:128 + offset + len(code)] = code
    def jump(offset, target):
        patch(offset, b'\xe9' + struct.pack('<h', target - offset - 3))

    jump(0x1ee, 0x638)  # Enter configure_system after runtime startup.
    struct.pack_into('<H', image, 0x1be0 + 0x53a, 0xc3c)
    struct.pack_into('<H', image, 0x1be0 + 0x48c, language)
    patch(0xb33, b'\xc7\x06\xfe\x04' + struct.pack('<H', keyboard) + b'\xc3')
    jump(0x118d, 0x11d3)  # Accept Save, retaining the BP frame.
    return image


def run():
    kernel = Path(sys.argv[1]).read_bytes()
    original = (BASE / 'n.cmd').read_bytes()
    if hashlib.sha256(original).hexdigest() != '4a47452157dd652cade919bbd10862200a3e6f6aaef770d825e9269b2c72223d':
        raise ValueError('Expected the original 4.11 N.CMD')
    base = 128 + 16 * struct.unpack_from('<H', kernel, 1)[0]
    signature, directory = struct.unpack_from('<HH', kernel, base + 0xc3c)
    if signature != 0x574a:
        raise ValueError('Expected a national-capable 4.11 kernel')
    slots = struct.unpack_from('<24H', kernel, base + directory)
    with TemporaryDirectory() as temp:
        folder = Path(temp)
        (folder / 'national.msg').write_bytes((BASE / 'national.msg').read_bytes())
        (folder / 'nkey.cmd').write_bytes((HERE / 'nkey.cmd').read_bytes())
        for variant in range(2):
            seed = bytearray(kernel)
            seed[base + slots[18]] = variant
            for language in range(9):
                for keyboard in range(5):
                    (folder / 'ccpm.sys').write_bytes(seed)
                    (folder / 'ntest.sys').write_bytes(seed)
                    (folder / 'orig.cmd').write_bytes(scripted_command(original, language, keyboard))
                    for args in [('orig',), ('nkey', str(keyboard), str(language))]:
                        result = subprocess.run(['cpm86', *args], cwd=temp, capture_output=True,
                                                timeout=10, check=True)
                    if b'saved' not in result.stdout or (folder / 'ccpm.sys').read_bytes() != (folder / 'ntest.sys').read_bytes():
                        raise ValueError((variant, language, keyboard))
    print('90 complete kernel saves match')


if __name__ == '__main__':
    run()
