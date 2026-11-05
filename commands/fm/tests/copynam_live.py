"""Named-copy UI on disposable images: validation, cancellation and exact binary copies."""
from pathlib import Path
import argparse,re,shutil,subprocess,tempfile,sys
p=argparse.ArgumentParser()
p.add_argument('--boot-image',type=Path,required=True)
p.add_argument('--media',choices=['fat','cpm'],required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fm-copynam-'+a.media+'-'));print(F,flush=True)
shutil.copy(R/'media/diskdefs',F/'diskdefs');shutil.copy(a.boot_image,F/'cdos86.img')
def run(*cmd):
 r=subprocess.run(cmd,cwd=F,capture_output=True,timeout=30)
 if r.returncode:raise RuntimeError(str(cmd)+': '+r.stderr.decode(errors='replace'))
 return r.stdout
def twist(mode,src,dst):run(sys.executable,str(R/'tools/cpm86twist.py'),mode,str(F/src),str(F/dst))
# Exact multiples of 128 avoid ambiguities in CP/M logical record lengths.
contents={'AONE.BIN':bytes(range(256))*3,
          'BTWO.BIN':bytes(reversed(range(256)))*2,
          'CRO.BIN':b'SOURCE RO TARGET '+bytes(range(111)),
          'DTAIL.BIN':bytes(range(128))}
assert all(len(v)%128==0 and b'\x1a' in v for v in contents.values())
old={'OTHER.BIN':b'old writable destination'.ljust(128,b'!'),
     'LOCK.BIN':b'protected target'.ljust(256,b'?')}
for name,data in contents.items():(F/name).write_bytes(data)
twist('untwist','cdos86.img','boot.logical')
for name,data in old.items():
 (F/'old.bin').write_bytes(data)
 run('cpmcp','-f','ccpm86-320','boot.logical',str(F/'old.bin'),'0:'+name)
run('cpmchattr','-f','ccpm86-320','boot.logical','r','0:LOCK.BIN')
twist('twist','boot.logical','cdos86.img')
if a.media=='fat':
 run('mformat','-C','-i','data.img','-t','40','-h','2','-n','8','-c','2','::')
 for file in [R/'commands/fm/fmview.cmd']+[F/n for n in contents]:run('mcopy','-i','data.img',str(file),'::')
else:
 shutil.copy(R/'media/base.img',F/'data.img');twist('untwist','data.img','data.logical')
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
def named():keys('Tab','Home',*(['Down']*6),'Return','End','Return')
command('b:');command('fmview');c.append('c 8000000');keys('Home');named();snap('prompt')
command('*.bin');snap('invalid');command('aone.bin');snap('same_name')
keys('Esc');snap('cancel')
named();command('new.bin');c.append('c 8000000');snap('same_drive_copy')
# Successful fallback copy removed its mark. Select two original files.
keys('Home','Comma','Right','Comma');named();keys('Return');snap('second_prompt')
command('a:other.bin');c.append('c 8000000');snap('crossdrive')
# Only skipped AONE remains selected, despite cursor position/resorting.
keys('End');snap('retained');named();command('a:lock.bin')
c.append('c 8000000');snap('read_only')
if a.media=='cpm':
 def usercopy():keys('Tab','Home',*(['Down']*6),'Return','End','Up','Return')
 usercopy();snap('users');keys('Return');snap('same_user')
 keys('Esc');snap('user_cancel');usercopy();keys('Right','Return')
 c.append('c 8000000');snap('user_copied')
keys('Esc');snap('exit');c.append('q')
with (F/'pce.log').open('wb') as log:
 subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={};vga={}
for name in labels:
 b=(F/(name+'.bin')).read_bytes();vga[name]=b
 screens[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
 (F/(name+'.txt')).write_text(screens[name])
assert 'Copy AONE.BIN to ?' in screens['prompt']
assert 'Name is too long, or invalid' in screens['invalid']
assert 'Source and destination are the same file' in screens['same_name']
assert 'Copy aborted' in screens['cancel'] and 'NEW.BIN' not in screens['cancel']
assert 'Copy done' in screens['same_drive_copy'] and 'NEW.BIN' in screens['same_drive_copy']
assert 'Copy BTWO.BIN to ?' in screens['second_prompt']
assert 'Copy done' in screens['crossdrive']
assert 'NOT COPIED' in screens['read_only']
if a.media=='cpm':
 assert 'User 00' in screens['users'] and 'User 15' in screens['users']
 assert 'Destination must be different than source' in screens['same_user']
 assert 'AONE.BIN' in screens['user_cancel']
 assert 'Copy done' in screens['user_copied']
 assert all(name in screens['user_copied'] for name in contents)
assert 'FMVIEW: closed' in screens['exit'] and 'B>' in screens['exit']
def attr(name):
 b=vga['retained'];chars=bytes(b[:3840:2]);i=chars.index(name.encode());return b[i*2+1]
assert attr('AONE.BIN')!=attr('BTWO.BIN')
assert attr('BTWO.BIN')==attr('CRO.BIN')==attr('DTAIL.BIN')
# Check source names and complete payloads, including bytes after Ctrl-Z.
expected=dict(contents);expected['NEW.BIN']=contents['AONE.BIN'];expected['FMVIEW.CMD']=(R/'commands/fm/fmview.cmd').read_bytes()
if a.media=='fat':
 listing=run('mdir','-b','-i','data.img','::').decode().upper()
 for name,data in expected.items():assert run('mtype','-i','data.img','::'+name)==data,name
else:
 twist('untwist','data.img','source.logical')
 listing=run('cpmls','-f','ccpm86-320','source.logical').decode().upper()
 for name,data in expected.items():
  run('cpmcp','-f','ccpm86-320','source.logical','0:'+name,str(F/'extracted.bin'))
  actual=(F/'extracted.bin').read_bytes()
  if name!='FMVIEW.CMD':assert actual==data,name
  else:assert actual[:len(data)]==data and len(actual)<len(data)+128
assert all(name in listing for name in expected)
twist('untwist','cdos86.img','destination.logical')
listing=run('cpmls','-f','ccpm86-320','destination.logical').decode().upper()
for name,data in {'OTHER.BIN':contents['BTWO.BIN'],'LOCK.BIN':old['LOCK.BIN']}.items():
 run('cpmcp','-f','ccpm86-320','destination.logical','0:'+name,str(F/'extracted.bin'))
 assert (F/'extracted.bin').read_bytes()==data,name
assert all(name not in listing for name in ['AONE.BIN','BTWO.BIN','NEW.BIN','DTAIL.BIN'])
assert not re.search(r'FMC[PB][0-9]{4}',listing)
print('PASS: '+a.media+' named Copy: wildcard/same-name retry, Escape retention, same-drive binary copy, batch skip, cross-drive writable replacement and read-only refusal')

if a.media=='cpm':
 run('cpmcp','-f','ccpm86-320','source.logical','1:AONE.BIN',str(F/'user1.bin'))
 assert (F/'user1.bin').read_bytes()==contents['AONE.BIN']
 print('PASS: CP/M user 0 to user 1 copy, same-user refusal, picker cancellation, exact binary destination and restored source user')
