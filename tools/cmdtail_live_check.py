#!/usr/bin/env python3
"""Opt-in native CMD tails, CHSET and mixed-case DOS redirection on disposable media."""
from pathlib import Path
import subprocess,shutil,re,struct,tempfile
R=Path(__file__).resolve().parent.parent;F=Path(tempfile.mkdtemp(prefix='cdos-tail-'));print('Diagnostics:',F,flush=True)
def run(*a):
 p=subprocess.run(a,cwd=F,capture_output=True);assert p.returncode==0,(a,p.stdout,p.stderr);return p
shutil.copyfile(R/'media/diskdefs',F/'diskdefs')
run('python3',str(R/'tools/cpm86twist.py'),'untwist',str(R/'media/cdos86.img'),'boot.logical')
run('cpmrm','-f','ccpm86-320','boot.logical','0:ED.CMD','0:SDIR.CMD','0:CCPM.SYS')
for source in [R/'kernel/sysgen/ccpm.sys']+[R/f'commands/putget/{n}.cmd' for n in ['put','get','rdr']]:run('cpmcp','-f','ccpm86-320','boot.logical',str(source),'0:')
run('python3',str(R/'tools/cpm86twist.py'),'twist','boot.logical','cdos86.img')
run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
run('nasm','-DNATIVE','-f','bin',str(R/'kernel/rsp3/tests/cmd_tail.asm'),'-o','upper.cmd')
b=bytearray((F/'upper.cmd').read_bytes());b[127]|=2;(F/'keep.cmd').write_bytes(b)
for name in ['upper.cmd','keep.cmd']:run('mcopy','-i','fat.img',name,'::')
run('mcopy','-i','fat.img',str(R/'commands/chset/chset.cmd'),'::')
run('nasm','-f','bin',str(R/'kernel/rsp3/tests/cmd_tail.asm'),'-o','tail.com');run('mcopy','-i','fat.img','tail.com','::')
image=(F/'tail.com').read_bytes();n=len(image)+32
(F/'tail.exe').write_bytes(struct.pack('<14H',0x5a4d,n%512,(n+511)//512,0,2,0x100,0xffff,0,0x800,0,0,0,0x1c,0)+b'\0'*4+image)
run('mcopy','-i','fat.img','tail.exe','::')
(F/'input.txt').write_bytes(b'INPUT\r\n');run('mcopy','-i','fat.img','input.txt','::')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('sdl:lowpass=5000','null').replace('cdostools.img','fat.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg);(F/'test.cfg').write_text(cfg)
c=['c f000000'];cases=[('b:upper MiXeD','upper'),('b:keep MiXeD','keep'),('b:chset b:upper [tail=keep]','setkeep'),('b:upper MiXeD','kept'),('b:chset b:upper [tail=upper]','setupper'),('b:upper MiXeD','upperagain'),('b:chset b:keep [suspend=on]','otherfield'),('b:chset b:keep','query'),('PuT [B:PuT.TxT,eO] b:TaIl.CoM MiXeD hello','put'),('put [b:put.txt,a] b:tail.exe NextCase','append'),('gEt [B:InPuT.TxT,eI] b:TaIl.ExE MiXeD hello','get'),('rDr [B:InPuT.TxT,B:RdR.TxT,e] b:TaIl.CoM MiXeD hello','rdr'),('put [b:native.txt] b:upper MiXeD hello','native')]
keys={':':'+Shift Semicolon -Shift',' ':'Space','.':'Period','[':'LeftBracket',']':'RightBracket','=':'Equal',',':'Comma'}
for text,label in cases:
 for ch in 'cls\n'+text+'\n':
  key='Return' if ch=='\n' else ('+Shift '+ch.lower()+' -Shift' if ch.isupper() else keys.get(ch,ch));c+=['key '+key,'c 200000']
 c+=['c 8000000',f'save "{label}.bin" bin b800:0000 fa0']
c+=['q']
with(F/'pce.log').open('wb')as log:subprocess.run(['pce-ibmpc','-c','test.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={}
for _,label in cases:
 b=(F/(label+'.bin')).read_bytes();s='\n'.join(bytes(b[i:i+160:2]).decode('latin1').rstrip() for i in range(0,3840,160));screens[label]=s;(F/(label+'.txt')).write_text(s);print(label+'\n'+s.strip(),flush=True)
for name in ['put.txt','rdr.txt','native.txt']:
 print(name,run('mtype','-i','fat.img','::'+name).stdout,flush=True)
assert '[204D49584544]' in screens['upper'],screens['upper']
assert '[204D69586544]' in screens['keep'],screens['keep']
assert '[204D69586544]' in screens['kept'],screens['kept']
assert '[204D49584544]' in screens['upperagain'],screens['upperagain']
assert run('mtype','-i','fat.img','::put.txt').stdout==b' MiXeD hello\r\n NextCase\r\n'
assert run('mtype','-i','fat.img','::rdr.txt').stdout==b' MiXeD hello\r\n'
assert 'MiXeD hello' in screens['put']
assert 'MiXeD hello' in screens['get'],screens['get']
assert b'4D495845442048454C4C4F' in run('mtype','-i','fat.img','::native.txt').stdout
print('PASS: CMD opt-in, CHSET toggles, DOS COM/EXE wrapper case, ordinary native uppercase',flush=True)

run('mcopy','-i','fat.img','::upper.cmd','final.cmd')
assert (F/'final.cmd').read_bytes()[127]==0
run('mcopy','-i','fat.img','::keep.cmd','keep-final.cmd')
assert (F/'keep-final.cmd').read_bytes()[127]==10
assert 'TAIL=KEEP' in ''.join(screens['query'].split())
assert 'SUSPEND=ON' in ''.join(screens['query'].split())
shutil.rmtree(F)
