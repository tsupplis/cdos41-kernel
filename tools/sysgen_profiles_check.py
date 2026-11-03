#!/usr/bin/env python3
"""Check the two GENCCPM profiles differ only by CONFIDD selection."""
from pathlib import Path
from sysgen_check import check, resident_names

ROOT = Path(__file__).resolve().parent.parent
folder = ROOT/'kernel/sysgen'
lean_recipe = (folder/'genccpm.in').read_text()
fidd_recipe = (folder/'genfidd.in').read_text()
assert lean_recipe.count('exclude=confid.rsp\n') == 1
assert lean_recipe.replace('exclude=confid.rsp\n','') == fidd_recipe, 'System profiles differ beyond CONFIDD selection'
a = (folder/'ccpm.sys').read_bytes()
b = (folder/'ccpmfidd.sys').read_bytes()
check(folder/'ccpm.sys',0)
check(folder/'ccpmfidd.sys',1)
w = lambda b,o: int.from_bytes(b[o:o+2],'little')
assert w(a,1)==w(b,1)
assert a[128:128+w(a,1)*16] == b[128:128+w(b,1)*16], 'Kernel CODE differs between profiles'
lean_names, fidd_names = resident_names(a), resident_names(b)
assert sorted(lean_names+['CONFIDD']) == sorted(fidd_names), 'Unexpected resident-process difference'
component = (ROOT/'kernel/rsp3/confid.rsp').read_bytes()
resident = (w(component,1)+w(component,10))*16
assert abs((len(b)-len(a))-resident)<128, 'Unexpected image-size difference'
print(f'PASS: identical kernel CODE, matched GENCCPM settings; ccpm.sys {len(a)} bytes, ccpmfidd.sys {len(b)} bytes; CONFIDD is the only resident difference')
