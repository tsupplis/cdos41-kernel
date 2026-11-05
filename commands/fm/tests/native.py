"""Run the actual DR C test on a disposable host directory."""
from pathlib import Path
import os, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp)
    shutil.copyfile(root/'fmcheck.cmd',folder/'fmcheck.cmd')
    (folder/'fmprobe.txt').write_bytes(b'FM read-only fixture\r\n')
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    r=subprocess.run(['emu2','fmcheck.cmd'],cwd=folder,
        env=dict(os.environ,EMU2_CPM_VER='4.1'),capture_output=True,timeout=15)
    out=r.stdout.decode(errors='replace')
    assert r.returncode==0 and 'FM configuration core: PASS' in out and 'FAIL' not in out,(r.returncode,out,r.stderr)
    assert before=={p.name:p.read_bytes() for p in folder.iterdir()}
print('PASS: native DR C core regression and read-only directory search')
