#!/usr/bin/env python3
"""Whole-file identity, including MZ header, relocation, stack and padding."""
from pathlib import Path
import hashlib
expected="21072eff5a230c9dfb64dccbc09c36e4ca3dab3572fe1eb25cb49ad522dc7bad"
for name in ('../../base/ren.exe','ren.exe'):
    b=Path(name).read_bytes()
    assert len(b)==2048 and hashlib.sha256(b).hexdigest()==expected, name
s=Path('pcren.a86').read_text()
code=s[s.index('start:'):s.index('stackseg sseg')]
assert not any(line.split(';')[0].strip().lower().startswith(('db ', 'db\t')) for line in code.splitlines())
print('PASS: all 2048 REN.EXE bytes match OEM; no instructions hidden in DB')
