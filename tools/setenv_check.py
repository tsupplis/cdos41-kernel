#!/usr/bin/env python3
"""Exercise SETENV.EXE on disposable CP/M/FAT media under PCE."""
from pathlib import Path
import subprocess,tempfile,shutil
R=Path(__file__).resolve().parent.parent
F=Path(tempfile.mkdtemp(prefix='cdos-utils-'));print(F,flush=True)
def run(*a): return subprocess.run(a,cwd=F,capture_output=True,check=True).stdout
shutil.copyfile(R/'media/diskdefs',F/'diskdefs')
twist=str(R/'tools/cpm86twist.py')
run('python3',twist,'untwist',str(R/'media/cdos86base.img'),'a.logical')
for p in [R/'kernel/sysgen/ccpm.sys',R/'commands/setenv/setenv.exe']:
 run('cpmcp','-f','ccpm86-320','a.logical',str(p),'0:')
run('python3',twist,'twist','a.logical','cdos86.img')
run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
run('mmd','-i','fat.img','::FIRST')
run('mcopy','-i','fat.img',str(R/'commands/path/path.exe'),'::PATH.EXE')
run('mmd','-i','fat.img','::SECOND')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('file     = "cdostools.img"','file     = "fat.img"')
(F/'cdos86.cfg').write_text(cfg)
c=['c f000000']; keys={' ':'Space',':':'+Shift Semicolon -Shift','.':'Period','-':'Minus','=':'Equal','\\':'Backslash'}
def cmd(s,name):
 for ch in s:c.extend(['key '+keys.get(ch, '+Shift '+ch.lower()+' -Shift' if ch.isupper() else ch),'c 200000'])
 c.extend(['key Return','c 1000000',f'save "{name}.bin" bin b800:0000 fa0'])
cmd('setenv temp=Mixed Case','add')
cmd('setenv temp','query')
cmd('setenv path=B:\\TOOLS','pathset')
cmd('b:path','dospath')
cmd('setenv longone='+'x'*100,'longone')
cmd('setenv longtwo='+'y'*100,'longtwo')
cmd('setenv longtwo','capacity')
cmd('setenv temp=','delete')
cmd('setenv temp','missing')
c += ['q']
with (F/'log').open('wb') as log:subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=240,check=True)
for n in ['query','dospath','missing','capacity']:
 b=(F/(n+'.bin')).read_bytes();s='\n'.join(bytes(b[i:i+160:2]).decode('ascii','replace').rstrip() for i in range(0,3840,160));(F/(n+'.txt')).write_text(s)
 assert s.rstrip().endswith('A>'), s
 if n=='capacity': assert 'LONGTWO='+'y'*60 in s, s
 if n=='query': assert 'TEMP=Mixed Case' in s, s
 if n=='dospath': assert 'PATH=B:\\TOOLS' in s, s
 if n=='missing': assert 'Environment variable not found.' in s, s
print('PASS: SETENV mixed-case persistence, deletion, >128-byte environment and DOS PATH interoperability')
shutil.rmtree(F)
