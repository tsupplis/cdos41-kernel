"""Rename only disposable files; verify collisions, cancellation and file bytes."""
from pathlib import Path
import argparse,re,shutil,subprocess,tempfile,sys
p=argparse.ArgumentParser()
p.add_argument('--boot-image',type=Path,required=True)
p.add_argument('--media',choices=['fat','cpm'],required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fm-rename-'+a.media+'-'));print(F,flush=True)
shutil.copy(R/'media/diskdefs',F/'diskdefs');shutil.copy(a.boot_image,F/'cdos86.img')
def run(*cmd):
 r=subprocess.run(cmd,cwd=F,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r.stdout
def twist(mode,src,dst):run(sys.executable,str(R/'tools/cpm86twist.py'),mode,str(F/src),str(F/dst))
contents={'ONE.TXT':b'First original\r\n\x1a','TWO.TXT':b'Destination must survive\r\n\x1a','THREE.TXT':b'Third original\r\n\x1a'}
for name,data in contents.items():(F/name).write_bytes(data)
if a.media=='fat':
 run('mformat','-C','-i','data.img','-t','40','-h','2','-n','8','-c','2','::')
 for file in [R/'commands/fm/fmview.cmd']+[F/n for n in contents]:run('mcopy','-i','data.img',str(file),'::')
else:
 shutil.copy(R/'media/base.img',F/'data.img');twist('untwist','data.img','data.logical')
 twist('untwist','cdos86.img','boot.logical')
 data=bytearray((F/'data.logical').read_bytes());data[:4096]=(F/'boot.logical').read_bytes()[:4096];(F/'data.logical').write_bytes(data)
 for file in [R/'commands/fm/fmview.cmd']+[F/n for n in contents]:run('cpmcp','-f','ccpm86-320','data.logical',str(file),'0:')
 twist('twist','data.logical','data.img')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','data.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg)
(F/'cdos86.cfg').write_text(cfg)
c=['c f000000'];labels=[]
def keys(*seq):
 for k in seq:c.extend(['key '+k,'c 1000000'])
def command(text):
 for ch in text:keys({' ': 'Space',':':'+Shift Semicolon -Shift','*':'+Shift 8 -Shift'}.get(ch,ch))
 keys('Return')
def snap(name):labels.append(name);c.extend(['c 1000000','save "'+name+'.bin" bin b800:0000 fa0'])
def rename():keys('Tab','Home',*(['Down']*7),'Return')
command('b:');command('fmview');c.append('c 8000000');keys('Home','Right');rename();snap('prompt')
command('two.txt');snap('collision')
rename();command('a:bad');snap('drive_rejected');command('*.txt');snap('wild_rejected');keys('Esc');snap('cancel')
rename();command('new.txt');snap('renamed')
keys('Home','Right','Comma','Right','Comma');rename();keys('Return','Esc');snap('skipped')
rename();keys('Return');command('third.txt');snap('partial')
keys('Esc');snap('exit');c.append('q')
with (F/'pce.log').open('wb') as log:
 subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={}
for name in labels:
 b=(F/(name+'.bin')).read_bytes();screens[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160));(F/(name+'.txt')).write_text(screens[name])
assert 'Rename, ONE.TXT to ?' in screens['prompt']
assert 'NOT RENAMED' in screens['collision'] and 'ONE.TXT' in screens['collision']
assert 'You cannot specify a drive.' in screens['drive_rejected']
assert 'Name is too long, or invalid' in screens['wild_rejected']
assert 'ONE.TXT' in screens['cancel'] and 'NEW.TXT' not in screens['cancel']
assert 'NEW.TXT' in screens['renamed'] and 'ONE.TXT' not in screens['renamed']
assert 'NOT RENAMED' in screens['skipped']
assert 'NEW.TXT' in screens['partial'] and 'THIRD.TXT' in screens['partial'] and 'THREE.TXT' not in screens['partial']
assert 'FMVIEW: closed' in screens['exit'] and 'B>' in screens['exit']
expected={'NEW.TXT':contents['ONE.TXT'],'TWO.TXT':contents['TWO.TXT'],'THIRD.TXT':contents['THREE.TXT'],'FMVIEW.CMD':(R/'commands/fm/fmview.cmd').read_bytes()}
if a.media=='fat':
 listing=run('mdir','-b','-i','data.img','::').decode().upper()
 for old in ['ONE.TXT','THREE.TXT']:assert old not in listing
 for name,data in expected.items():assert run('mtype','-i','data.img','::'+name)==data
else:
 twist('untwist','data.img','result.logical')
 listing=run('cpmls','-f','ccpm86-320','result.logical').decode().upper()
 for old in ['ONE.TXT','THREE.TXT']:assert old not in listing
 for name,data in expected.items():
  run('cpmcp','-f','ccpm86-320','result.logical','0:'+name,str(F/'result.bin'))
  actual=(F/'result.bin').read_bytes();assert actual[:len(data)]==data and len(actual)<len(data)+128
assert all(name in listing for name in expected)
print('PASS: '+a.media+' Rename, collision/no overwrite, invalid names, skip/cancel, retained selections, exact file contents and clean exit')
