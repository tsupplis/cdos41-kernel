from pathlib import Path
import sys

if sys.argv[1] == 'merge':
    records = []
    for name in ('lbdos', 'cpmboot3'):
        data = Path(name + '.h86').read_bytes()
        records.append(data.split(b':00000001FF', 1)[0])
    Path('cpmlod.h86').write_bytes(b''.join(records) + b':00000001FF\r\n')
else:
    def raw(name): return Path(name + '.cmd').read_bytes()
    primary = raw('pcboot1')
    secondary = raw('cpmboot2')
    fat = raw('pcboot2')
    assert len(primary) == len(secondary) == 640
    assert not any(primary[512:]) and not any(secondary[512:])
    assert not any(fat[:0x7c00]) and len(fat[0x7c00:]) == 640
    cpm = secondary[:512] * 2 + raw('hsetup') + raw('label') + raw('cpmlod')
    assert len(cpm) == 8192
    tertiary = Path('pcboot3.bin').read_bytes()
    assert len(tertiary) == 1280
    bundle = primary[:512] + cpm + fat[0x7c00:] + tertiary.ljust(2048, b'\0')
    assert len(bundle) == 0x2c80
    output = bytearray(raw('h70'))
    start = output.index(b'XTLBL DEFAULT FILE GOES HERE')
    assert output[start+len(bundle):].startswith(b'CPM/DOS SYSTEM TRACKS SHOULD HAVE ENDED BY NOW!')
    output[start:start+len(bundle)] = bundle
    # GENCMD emits empty auxiliary groups for the source's reserved ESEG
    # and SSEG. The OEM SID save omitted their descriptors. No body bytes
    # are changed by restoring that historical header representation.
    for offset, kind in ((36, 5), (63, 8)):
        assert output[offset:offset+9] == bytes((kind, 1, 0, 0, 0, 1, 0, 0, 0))
        output[offset:offset+9] = bytes(9)
    Path('hdmaint.cmd').write_bytes(output)
