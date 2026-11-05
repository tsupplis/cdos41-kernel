"""Reference-derived name fixtures, attribute masking and ordering checks."""
from pathlib import Path
import ctypes as C
import itertools
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    lib = Path(tmp) / 'directory.so'
    subprocess.run(['cc', '-std=c89', '-shared', '-fPIC',
                    '-Wno-deprecated-non-prototype', str(root/'dirlist.c'),
                    '-o', str(lib)], check=True)
    dll = C.CDLL(str(lib))
    name = dll.fm_directory_name
    name.argtypes = [C.c_char_p, C.c_void_p, C.c_int]
    fixtures = [(b'TEST    CMD', b'TEST.CMD    '),
                (b'README     ', b'README      '),
                (b'ABCDEFGHXYZ', b'ABCDEFGH.XYZ'),
                (b'A       C  ', b'A.C         '),
                (b'AB CD   TXT', b'AB.TXT      '),
                (b'..         ', b'..          ')]
    for raw, expected in fixtures:
        output = C.create_string_buffer(15)
        output.raw = b'!' * 15
        assert name(b'\0' + raw, output, 13) == 1
        assert output.raw == expected + b'\0!!', (raw, output.raw)
    # All name/type attribute combinations with a nonblank extension.
    raw = b'ABCDEFGHXYZ'
    for bits in range(2048):
        entry = bytes([4] + [v | (128 if bits & (1 << i) else 0)
                             for i, v in enumerate(raw)])
        output = C.create_string_buffer(13)
        assert name(entry, output, 13) == 1
        assert output.raw == b'ABCDEFGH.XYZ\0'
    # Historical raw-byte dot test: high-bit blank differs from plain blank.
    output = C.create_string_buffer(13)
    assert name(b'\0README  \xa0  ', output, 13) == 1
    assert output.raw == b'README.     \0'
    output.raw = b'!' * 13
    assert name(b'\0' + raw, output, 12) == 0
    assert output.raw == b'!' * 13
    assert name(None, output, 13) == 0
    sort = dll.fm_directory_sort
    sort.argtypes = [C.POINTER(C.c_char_p), C.c_int]
    values = [b'A.CMD       ', b'A.TXT       ', b'AA          ',
              b'Z.CMD       ', b'a.CMD       ']
    for permutation in itertools.permutations(values):
        items = (C.c_char_p * 5)(*permutation)
        assert sort(items, 5) == 1
        assert list(items) == sorted(values)
    for values in ([b'A           '] * 1000,
                   [('%08d    ' % i).encode() for i in range(1000)],
                   [('%08d    ' % i).encode() for i in range(999, -1, -1)]):
        items = (C.c_char_p * len(values))(*values)
        assert sort(items, len(values)) == 1
        assert list(items) == sorted(values)
    assert sort(None, 0) == 1
    assert sort(None, 1) == 0 and sort(None, -1) == 0
print('PASS: filename fixtures, 2048 attribute combinations, 120 orderings and large duplicate/sorted/reversed lists')
