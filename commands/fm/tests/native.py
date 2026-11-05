"""Run the actual DR C test executable, rather than trusting host arithmetic."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
r=subprocess.run(['emu2',str(root/'fmcheck.cmd')],env=dict(os.environ,EMU2_CPM_VER='4.1'),capture_output=True,timeout=15)
out=r.stdout.decode(errors='replace')
assert r.returncode==0 and 'FM configuration core: PASS' in out and 'FAIL' not in out,(r.returncode,out,r.stderr)
print('PASS: native DR C configuration regression')
