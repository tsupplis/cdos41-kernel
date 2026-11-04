"""Cold-boot DOS floppy geometries with the unmodified distribution CCPM.SYS.

Only newly created temporary images are written. The formatter checks test
actual formatting separately; this matrix isolates bootstrap compatibility.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
from dskmaint_live_check import cold_boot

ROOT=Path(__file__).resolve().parent.parent
folder=Path(tempfile.mkdtemp(prefix='cdos-floppy-boot-'))
print('Diagnostics:',folder,flush=True)
boot=(ROOT/'commands/dskmaint/dosbootx.bin').read_bytes()
assert len(boot)==512 and boot[-2:]==b'\x55\xaa'
for capacity,cylinders,heads,spt,spc in [(180,40,1,9,1),(360,40,2,9,2),(720,80,2,9,2),(1200,80,2,15,1),(1440,80,2,18,1)]:
    image=folder/f'empty-{capacity}.img'
    subprocess.run(['mformat','-C','-i',str(image),'-t',str(cylinders),'-h',str(heads),'-n',str(spt),'-c',str(spc),'::'],check=True,capture_output=True)
    b=bytearray(image.read_bytes())
    bpb=b[11:32]
    b[:512]=boot
    b[11:32]=bpb
    image.write_bytes(b)
    cold_boot(folder,image,f'boot-{capacity}','CCPM.SYS',ROOT/'kernel/sysgen/ccpm.sys',['Concurrent','A>'])
    print(f'PASS: DOS {capacity}K cold boot with normal distribution CCPM.SYS',flush=True)
shutil.rmtree(folder)
