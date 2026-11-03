#!/usr/bin/env python3
"""Copy/compare a bootable FAT12 360K disk using actual CDOS XIOS on PCE.

All I/O is confined to newly created disposable floppy images. The ninth
sector of every head has a distinct pattern, so an eight-sector copy fails.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from dskmaint_live_check import build_low_kernel

ROOT=Path(__file__).resolve().parent.parent
F=Path(tempfile.mkdtemp(prefix='cdos-disk-live-'))
print('Diagnostics:',F,flush=True)
def run(*args,**kwargs):return subprocess.run(args,cwd=F,capture_output=True,check=True,**kwargs)
run('mformat','-C','-i','source.img','-t','40','-h','2','-n','9','-c','2','::')
# Use the existing, checked 4.11 bootstrap and a separately generated matching
# low-linked kernel; the normal CP/M media remains untouched.
b=bytearray((F/'source.img').read_bytes());b[:512]=(ROOT/'commands/dskmaint/dosboot.bin').read_bytes();(F/'source.img').write_bytes(b)
run('mcopy','-i','source.img',str(build_low_kernel(F)),'::CCPM.SYS')
for name in ['dcopy','dcomp']:
    run('mcopy','-i','source.img',str(ROOT/f'commands/disk/{name}.cmd'),'::')
# Set unused data bytes only: the kernel and utilities occupy the beginning
# of the image. Their filesystem sectors must remain valid until loaded.
b=bytearray((F/'source.img').read_bytes())
for track in range(65,80):
    start=(track*9+8)*512;b[start:start+512]=bytes([0xa0+track-65])*512
(F/'source.img').write_bytes(b)
(F/'target.img').write_bytes(bytes([0xe5])*368640)
cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('sdl:lowpass=5000','null').replace('cdos86.img','source.img').replace('cdostools.img','target.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/'media'/m[1]).resolve())+'"',cfg)
(F/'test.cfg').write_text(cfg)
c=['c f000000']
keys={':':'+Shift Semicolon -Shift',' ':'Space','[':'LeftBracket',']':'RightBracket'}
def text(s):
    for ch in s:c.extend(['key '+keys.get(ch,ch),'c 200000'])
    c.extend(['key Return','c 6000000'])
text('dcopy a: b:')
c.extend(['key Space','c 40000000','save "copy.bin" bin b800:0000 fa0','key n','c 4000000'])
text('dcomp a: b:')
c.extend(['key Space','c 40000000','save "compare.bin" bin b800:0000 fa0','key n','c 4000000','q'])
with (F/'pce.log').open('wb') as log:
    subprocess.run(['pce-ibmpc','-c','test.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=360,check=True)
def screen(n):
    b=(F/(n+'.bin')).read_bytes();s='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160));(F/(n+'.txt')).write_text(s);return s
s=screen('copy');assert 'Copy complete' in s,s
s=screen('compare');assert 'Diskettes compare ok' in s,s
assert (F/'source.img').read_bytes()==(F/'target.img').read_bytes(),'Physical FAT disk copy differs (including sector nine)'
print('PASS: real CDOS 360K FAT12 copy/compare through native XIOS; every physical byte including ninth sectors matches')
shutil.rmtree(F)
