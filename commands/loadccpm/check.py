#!/usr/bin/env python3
"""Reject any deviation from the independent 4.11 LOADCCPM release."""
from pathlib import Path
import hashlib
root = Path(__file__).resolve().parent
original = (root / '../../base/loadccpm.com').read_bytes()
assert hashlib.sha256(original).hexdigest() == 'f4a72b60115ebfef88fc28c3d3c73e34b057b638751066d265091f7b3d327967'
assert (root / 'loadccpm.com').read_bytes() == original
print('PASS: LOADCCPM is byte-identical to 4.11 (1536 bytes)')
