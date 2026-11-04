#!/usr/bin/env python3
"""Copy/compare bootable FAT12 360K–1.44M disks through CDOS XIOS on PCE.

All I/O is confined to newly created disposable floppy images. The last
sector of each final head has a distinct pattern to catch truncated copies.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--format',type=int,choices=(360,720,1200,1440),default=360)
capacity=parser.parse_args().format
cylinders,spt={360:(40,9),720:(80,9),1200:(80,15),1440:(80,18)}[capacity]
ROOT=Path(__file__).resolve().parent.parent
F=Path(tempfile.mkdtemp(prefix='cdos-disk-live-'))
print('Diagnostics:',F,flush=True)
def run(*args,**kwargs):return subprocess.run(args,cwd=F,capture_output=True,check=True,**kwargs)
run('mformat','-C','-i','source.img','-t',str(cylinders),'-h','2','-n',str(spt),'-c',('2' if capacity in (360,720) else '1'),'::')
# Use the maintained floppy bootstrap and the normal distribution kernel;
# the source image is disposable.
b=bytearray((F/'source.img').read_bytes())
bpb=b[11:32]
b[:512]=(ROOT/'commands/dskmaint/dosbootx.bin').read_bytes()
b[11:32]=bpb
(F/'source.img').write_bytes(b)
run('mcopy','-i','source.img',str(ROOT/'kernel/sysgen/ccpm.sys'),'::CCPM.SYS')
for name in ['dcopy','dcomp']:
    run('mcopy','-i','source.img',str(ROOT/f'commands/disk/{name}.cmd'),'::')
# Set unused data bytes only: the kernel and utilities occupy the beginning
# of the image. Their filesystem sectors must remain valid until loaded.
b=bytearray((F/'source.img').read_bytes())
for track in range(cylinders*2-15,cylinders*2):
    start=(track*spt+spt-1)*512;b[start:start+512]=bytes([0xa0+track-(cylinders*2-15)])*512
(F/'source.img').write_bytes(b)
(F/'target.img').write_bytes(bytes([0xe5])*(capacity*1024))
cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('sdl:lowpass=5000','null').replace('cdos86.img','source.img').replace('cdostools.img','target.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/'media'/m[1]).resolve())+'"',cfg)
(F/'test.cfg').write_text(cfg)
c=['c f000000']
keys={':':'+Shift Semicolon -Shift',' ':'Space','[':'LeftBracket',']':'RightBracket'}
def text(s):
    for ch in s:c.extend(['key '+keys.get(ch,ch),'c 200000'])
    c.extend(['key Return','c 6000000'])
text('dcopy a: b:')
c.extend(['key Space','c 40000000','c 40000000','save "copy.bin" bin b800:0000 fa0','key n','c 4000000'])
text('dcomp a: b:')
c.extend(['key Space','c 40000000','c 40000000','save "compare.bin" bin b800:0000 fa0','key n','c 4000000','q'])
with (F/'pce.log').open('wb') as log:
    subprocess.run(['pce-ibmpc','-c','test.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=360,check=True)
def screen(n):
    b=(F/(n+'.bin')).read_bytes();s='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160));(F/(n+'.txt')).write_text(s);return s
s=screen('copy');assert 'Copy complete' in s,s
s=screen('compare');assert 'Diskettes compare ok' in s,s
assert (F/'source.img').read_bytes()==(F/'target.img').read_bytes(),'Physical FAT disk copy differs (including sector nine)'
print(f'PASS: native CDOS {capacity}K copy/compare; every physical byte including the final sector of every head matches')
shutil.rmtree(F)
