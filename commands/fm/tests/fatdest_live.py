"""FAT directory-copy picker against isolated images and exact binary fixtures."""
from pathlib import Path
import argparse,re,shutil,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--boot-image',type=Path,required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fm-fatdest-'));print(F,flush=True)
shutil.copy(a.boot_image,F/'cdos86.img')
def run(*cmd):
 r=subprocess.run(cmd,cwd=F,capture_output=True,timeout=30)
 if r.returncode:raise RuntimeError(str(cmd)+': '+r.stderr.decode(errors='replace'))
 return r.stdout
contents={'AONE.BIN':bytes(range(256)),'BREAD.BIN':bytes(reversed(range(256))),
          'CTAIL.BIN':bytes(range(128))}
old={'AONE.BIN':b'old writable target'.ljust(128,b'!'),
     'BREAD.BIN':b'protected destination'.ljust(256,b'?')}
run('mformat','-C','-i','data.img','-t','40','-h','2','-n','8','-c','2','::')
run('mmd','-i','data.img','::SUB')
for name,data in contents.items():
 (F/name).write_bytes(data);run('mcopy','-i','data.img',str(F/name),'::')
for name,data in old.items():
 (F/'old.bin').write_bytes(data);run('mcopy','-i','data.img',str(F/'old.bin'),'::SUB/'+name)
run('mattrib','-i','data.img','+r','::SUB/BREAD.BIN')
program=(R/'commands/fm/fmview.cmd').read_bytes()
run('mcopy','-i','data.img',str(R/'commands/fm/fmview.cmd'),'::')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','data.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg)
(F/'cdos86.cfg').write_text(cfg)
c=['c f000000'];labels=[]
def keys(*seq):
 for k in seq:c.extend(['key '+k,'c 1000000'])
def command(s):
 for ch in s:keys({' ': 'Space',':':'+Shift Semicolon -Shift','*':'+Shift 8 -Shift'}.get(ch,ch))
 keys('Return')
def snap(name):labels.append(name);c.extend(['c 1000000','save "'+name+'.bin" bin b800:0000 fa0'])
def directorycopy():keys('Tab','Home',*(['Down']*6),'Return','End','Up','Return')
command('b:');command('fmview');c.append('c 8000000')
keys('Home','Comma','Right','Comma','Right','Comma');directorycopy();snap('picker')
keys('Home','Return');snap('same_location');keys('Esc');snap('cancel')
directorycopy();keys('Home','Right','Return');c.append('c 8000000');snap('copied')
keys('End');snap('retained');keys('Esc');snap('exit')
# A fresh FM process must still see the root, not the transient destination.
command('fmview');c.append('c 8000000');snap('reopen');keys('Esc');snap('exit_again');c.append('q')
with (F/'pce.log').open('wb') as log:
 subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={};vga={}
for name in labels:
 b=(F/(name+'.bin')).read_bytes();vga[name]=b
 screens[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
 (F/(name+'.txt')).write_text(screens[name])
assert 'SUB' in screens['picker']
assert 'Destination must be different than source' in screens['same_location']
assert all(name in screens['cancel'] for name in contents)
assert 'NOT COPIED' in screens['copied']
assert all(name in screens['retained'] for name in contents)
assert all(name in screens['reopen'] for name in contents)
assert 'FMVIEW.CMD' in screens['reopen']
for state in ['exit','exit_again']:assert 'FMVIEW: closed' in screens[state] and 'B>' in screens[state]
def attr(state,name):
 b=vga[state];chars=bytes(b[:3840:2]);i=chars.index(name.encode());return b[i*2+1]
assert attr('retained','BREAD.BIN')==attr('retained','CTAIL.BIN')!=attr('retained','AONE.BIN')
for name,data in contents.items():assert run('mtype','-i','data.img','::'+name)==data,name
assert run('mtype','-i','data.img','::FMVIEW.CMD')==program
assert run('mtype','-i','data.img','::SUB/AONE.BIN')==contents['AONE.BIN']
assert run('mtype','-i','data.img','::SUB/BREAD.BIN')==old['BREAD.BIN']
listing=run('mdir','-b','-s','-i','data.img','::').decode().upper()
assert '/SUB/CTAIL.BIN' not in listing and not re.search(r'FMC[PB][0-9]{4}',listing)
print('PASS: FAT directory picker, same-location refusal, cancellation, binary writable replacement, RO batch stop, retained marks, source root and fresh-process restoration')
