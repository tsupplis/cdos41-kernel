"""Drive-copy UI against disposable images, with binary records and collisions."""
from pathlib import Path
import argparse,re,shutil,subprocess,tempfile,sys
p=argparse.ArgumentParser()
p.add_argument('--boot-image',type=Path,required=True)
p.add_argument('--media',choices=['fat','cpm'],required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fm-copy-'+a.media+'-'));print(F,flush=True)
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
old={'BTWO.BIN':b'old writable destination'.ljust(128,b'!'),
     'CRO.BIN':b'protected target'.ljust(256,b'?')}
for name,data in contents.items():(F/name).write_bytes(data)
twist('untwist','cdos86.img','boot.logical')
for name,data in old.items():
 (F/'old.bin').write_bytes(data)
 run('cpmcp','-f','ccpm86-320','boot.logical',str(F/'old.bin'),'0:'+name)
run('cpmchattr','-f','ccpm86-320','boot.logical','r','0:CRO.BIN')
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
 for ch in text:keys({' ': 'Space',':':'+Shift Semicolon -Shift'}.get(ch,ch))
 keys('Return')
def snap(name):labels.append(name);c.extend(['c 1000000','save "'+name+'.bin" bin b800:0000 fa0'])
def copy():keys('Tab','Home',*(['Down']*6),'Return')
command('b:');command('fmview');c.append('c 8000000');keys('Home');copy();snap('menu')
keys('F4');snap('same_drive');keys('Esc');snap('cancel')
# AONE and BTWO succeed; CRO fails, and DTAIL remains unprocessed.
keys('Home','Comma','Right','Comma','Right','Comma','Right','Comma')
copy();keys('F3');c.append('c 8000000');snap('copied')
# Move the cursor away so retained mark attributes can be distinguished.
keys('End');snap('retained');keys('Esc');snap('exit');c.append('q')
with (F/'pce.log').open('wb') as log:
 subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={};vga={}
for name in labels:
 b=(F/(name+'.bin')).read_bytes();vga[name]=b
 screens[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
 (F/(name+'.txt')).write_text(screens[name])
assert 'Destination must be different than source' in screens['same_drive']
assert 'NOT COPIED' in screens['copied']
assert all(name in screens['retained'] for name in contents)
assert 'FMVIEW: closed' in screens['exit'] and 'B>' in screens['exit']
def attr(name):
 b=vga['retained'];chars=bytes(b[:3840:2]);i=chars.index(name.encode());return b[i*2+1]
assert attr('AONE.BIN')==attr('BTWO.BIN')
assert attr('CRO.BIN')==attr('DTAIL.BIN')!=attr('AONE.BIN')
# Check source names and complete payloads, including bytes after Ctrl-Z.
expected=dict(contents);expected['FMVIEW.CMD']=(R/'commands/fm/fmview.cmd').read_bytes()
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
for name,data in {'AONE.BIN':contents['AONE.BIN'],'BTWO.BIN':contents['BTWO.BIN'],'CRO.BIN':old['CRO.BIN']}.items():
 run('cpmcp','-f','ccpm86-320','destination.logical','0:'+name,str(F/'extracted.bin'))
 assert (F/'extracted.bin').read_bytes()==data,name
assert 'DTAIL.BIN' not in listing
assert not re.search(r'FMC[PB][0-9]{4}',listing)
print('PASS: '+a.media+' source to CPM destination: same-drive refusal, binary records, writable overwrite, read-only refusal, retained selections and unchanged sources')
