"""Check the compiled command's parameter rejection before disk access."""
from pathlib import Path
import subprocess
import os

command = Path(__file__).resolve().parents[1]
name = command.name.upper()
usage = (f"USAGE: {name} drive: [BDFLRV]\n"
         "  drive: A:..P:\n"
         "  B      read file/directory data\n"
         "  D      find erased-directory remnants\n"
         "  F      repair\n"
         "  L      find contiguous-chain candidates\n"
         "  R      find orphaned first-level directories\n"
         "  V      verbose\n")
cases = [([], None)]
for tail in ("A", "Q:", "1:", "AA:", "/V A:", "[F] A:", "4A:"):
    cases.append((tail.split(), "Invalid command line."))
for tail in ("A: B:", "A: [HELP]", "A: /Z",
             "A: [", "A: []", "A: /", "A: /F]", "A: [FV]X",
             "A: /V /F", "A: [FV] B:", "A: 4", "A: [USER=4]"):
    cases.append((tail.split(), "Invalid command option."))
for args, error in cases:
    result = subprocess.run(["emu2", str(command / (name.lower()+".cmd")), *args],
                            capture_output=True, timeout=5)
    output = result.stdout.decode(errors="replace").replace("\r", "")
    assert usage in output, (args, output)
    if error:
        assert "ERROR: " + error in output, (args, output)
    assert "Scans ordinary" not in output and "data clusters" not in output, (args, output)
print(f"PASS: {len(cases)} {name} compiled parameter cases")

for option in ('[D]','[D','/d','[DF]','[FD]','/df','[DFV]','/vfd'):
    result=subprocess.run(['emu2',str(command/(name.lower()+'.cmd')),'A:',option],
                          env=dict(os.environ,EMU2_CPM_VER='1.1'),
                          capture_output=True,timeout=5)
    output=result.stdout.decode(errors='replace')
    assert 'requires Concurrent DOS 4.1' in output and 'USAGE:' not in output,(option,output)
print('PASS: 8 compiled D/DF option forms accepted before OS guard')

for option in ('[L]','[L','/l','[LF]','[FL]','/lf','[DFLV]','/vlfd'):
    result=subprocess.run(['emu2',str(command/(name.lower()+'.cmd')),'A:',option],
                          env=dict(os.environ,EMU2_CPM_VER='1.1'),capture_output=True,timeout=5)
    output=result.stdout.decode(errors='replace')
    assert 'requires Concurrent DOS 4.1' in output and 'USAGE:' not in output,(option,output)
print('PASS: 8 compiled L/LF option forms accepted before OS guard')

for option in ('[R]','[R','/r','[RF]','[FR]','/rf','[DRF]','/vfrd'):
    result=subprocess.run(['emu2',str(command/(name.lower()+'.cmd')),'A:',option],
                          env=dict(os.environ,EMU2_CPM_VER='1.1'),capture_output=True,timeout=5)
    output=result.stdout.decode(errors='replace')
    assert 'requires Concurrent DOS 4.1' in output and 'USAGE:' not in output,(option,output)
print('PASS: 8 compiled R/RF option forms accepted before OS guard')

for option in ('[B]','[B','/b','[BF]','[FB]','/bf','[RB]','[RBF]','/brfv','[BDFLRV]'):
    result=subprocess.run(['emu2',str(command/(name.lower()+'.cmd')),'A:',option],
                          env=dict(os.environ,EMU2_CPM_VER='1.1'),capture_output=True,timeout=5)
    output=result.stdout.decode(errors='replace')
    assert 'requires Concurrent DOS 4.1' in output and 'USAGE:' not in output,(option,output)
print('PASS: 10 compiled B/BF/RB/RBF option forms accepted before OS guard')
