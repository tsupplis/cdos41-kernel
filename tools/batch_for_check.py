#!/usr/bin/env python3
"""Live BATCH FOR on disposable CP/M/FAT media, including search isolation."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
FOLDER=Path(tempfile.mkdtemp(prefix='cdos-batch-for-'))
print('Diagnostics:',FOLDER,flush=True)
def run(*args):
    return subprocess.run(args,cwd=FOLDER,capture_output=True,check=True)
shutil.copyfile(ROOT/'media/diskdefs',FOLDER/'diskdefs')
run('python3',str(ROOT/'tools/cpm86twist.py'),'untwist',str(ROOT/'media/cdos86.img'),'a.logical')
run('cpmrm','-f','ccpm86-320','a.logical','0:ED.CMD','0:SDIR.CMD','0:BATCH.CMD','0:SHOW.CMD','0:SET.CMD','0:TYPE.CMD','0:DATE.CMD')
run('cpmcp','-f','ccpm86-320','a.logical',str(ROOT/'commands/batch/batch.cmd'),'0:BATCH.CMD')
run('cpmchattr','-f','ccpm86-320','a.logical','s','0:BATCH.CMD')
run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
for source in ['setenv/setenv.cmd','echo/echo.cmd']:
    run('mcopy','-i','fat.img',str(ROOT/'commands'/source),'::')
for name in ['SUB','EMPTY','SUB/DIR.COM']:
    run('mmd','-i','fat.img','::'+name)
for name in ['A.COM','B.COM','HIDE.COM']:
    (FOLDER/name).write_bytes(b'fixture\r\n\x1a')
    run('mcopy','-i','fat.img',name,'::SUB/')
run('mattrib','-i','fat.img','+h','+s','::SUB/HIDE.COM')
for name,size in [('ONE.ZZZ',1),('TWO.ZZZ',128),('MANY.ZZZ',18000)]:
    (FOLDER/name).write_bytes(b'X'*size)
    run('cpmcp','-f','ccpm86-320','a.logical',name,'0:')
shutil.copyfile(ROOT/'commands/batch/tests/exittest.a86',FOLDER/'forstat.a86')
run('pcdev_rasm86','forstat.a86')
run('pcdev_linkcmd','forstat=forstat[data[origin[0],max[0]]]')
run('mcopy','-i','fat.img','forstat.cmd','::')
# Test-only DOS child prints its tail, then returns status 7 through real 4Ch.
(FOLDER/'dosfor.asm').write_text('''bits 16
cpu 8086
org 100h
mov bx,1
mov dx,81h
xor cx,cx
mov cl,[80h]
mov ah,40h
int 21h
mov dx,newline
mov ah,9
int 21h
mov ax,4c07h
int 21h
newline db 13,10,'$'
''')
run('nasm','-f','bin','dosfor.asm','-o','DOSFOR.COM')
run('mcopy','-i','fat.img','DOSFOR.COM','::')
scripts={
'FLIST.BAT':'''@ECHO=OFF
B:SETENV VAL=Mixed Value
FOR %%I IN (A, B, "%VAL%", "AA AA", "A,B", "A)B", "") DO ECHO List=[%%I]
FOR %%I IN () DO ECHO WRONG-empty
FOR %%I IN (*.ZZZ) DO ECHO Literal=%%I
IF EXIST A:ONE.ZZZ FOR %%J IN (x y) DO IF "%%J"=="y" ECHO Conditional=%%J
ECHO ListDone
''',
'FRANGE.BAT':'''@ECHO=OFF
FOR %%I IN (1..3) DO ECHO Up=%%I
FOR %%I IN (3..1) DO ECHO Down=%%I
FOR %%I IN (-1..1) DO ECHO Signed=%%I
FOR %%I IN (32767..32767) DO ECHO Max=%%I
FOR %%I IN (-32768..-32768) DO ECHO Min=%%I
FOR %%I IN ("1..3") DO ECHO Quoted=%%I
ECHO RangeDone
''',
'FFILES.BAT':r'''@ECHO=OFF
FOR %%I IN (FILES A:*.ZZZ) DO IF EXIST A:ONE.ZZZ ECHO CPM=[%%I]
FOR %%I IN (FILES B:\SUB\*.COM) DO IF EXIST %%I ECHO FAT=[%%I]
FOR %%I IN (FILES B:\EMPTY\*.COM) DO ECHO WRONG-empty
FOR %%I IN (FILES A:*.NONE) DO ECHO WRONG-missing
IF DIREXIST B:SUB ECHO MappingPreserved
ECHO FilesDone
''',
'FPATH.BAT':r'''@ECHO=OFF
FOR %%I IN (FILES B:SUB\*.COM) DO ECHO Relative=[%%I]
FOR %%I IN (FILES B:\SUB\..\SUB\A.COM) DO IF EXIST %%I ECHO Parent=[%%I]
FOR %%I IN (FILES B:\SUB\*.COM) DO B:ECHO.CMD Native=%%I
ECHO PathDone
''',
'FEXEC.BAT':'''@ECHO=OFF
FOR %%I IN (1..3) DO B:DOSFOR.COM DosValue=%%I
IF ERRORLEVEL 7 ECHO DosStatus
FOR %%I IN (A B) DO B:ECHO.CMD NativeValue=%%I
ECHO ExecDone
''',
'FERROR.BAT':'''@ECHO=OFF
FOR %%I IN (32768..1) DO ECHO WRONG-overflow
FOR %%I IN (A) DO
FOR %%1 IN (A) DO ECHO WRONG-variable
FOR %%I IN ("A) DO ECHO WRONG-quote
FOR %%I IN (FILES L:*.COM) DO ECHO WRONG-drive
FOR %%I IN (A B) DO IF VALUE==%MISSING% ECHO WRONG-missing
FOR %%I IN (A B) DO FOR %%J IN (C) DO ECHO WRONG-nested
ECHO ErrorsContinue
''',
'FJUMP.BAT':'''@ECHO=OFF
FOR %%I IN (1..3) DO GOTO DONE
ECHO WRONG-goto
:DONE
ECHO GotoLeavesLoop
FOR %%I IN (1..3) DO B:FCHAIN.BAT
ECHO WRONG-chain
''',
'FCHAIN.BAT':'''@ECHO=OFF
ECHO ChainLeavesLoop
FOR %%I IN (1..3) DO EXIT 23
ECHO WRONG-exit
''',
}
for name,body in scripts.items():
    (FOLDER/name).write_bytes(body.replace('\n','\r\n').encode()+b'\x1a')
    run('cpmcp','-f','ccpm86-320','a.logical',name,'0:')
    if name in ['FLIST.BAT','FRANGE.BAT','FCHAIN.BAT']:
        run('mcopy','-i','fat.img',name,'::')
run('python3',str(ROOT/'tools/cpm86twist.py'),'twist','a.logical','cdos86.img')
cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('sdl:lowpass=5000','null').replace('cdostools.img','fat.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/'media'/m[1]).resolve())+'"',cfg)
(FOLDER/'test.cfg').write_text(cfg)
commands=['c f000000']
keys={':':'+Shift Semicolon -Shift',' ':'Space','\n':'Return'}
def command(text,label):
    for ch in text+'\n': commands.extend(['key '+keys.get(ch,ch),'c 200000'])
    commands.extend(['c 10000000',f'save "{label}.bin" bin b800:0000 fa0'])
for text,label in [('a:flist','list'),('b:flist','fat-list'),('a:frange','range'),('b:frange','fat-range'),('a:ffiles','files'),('a:fpath','paths'),('a:fexec','execute'),('a:ferror','errors'),('a:fjump','jump')]:
    command('cls','clear-'+label);command(text,label)
command('b:forstat 23','status')
commands.append('q')
with (FOLDER/'pce.log').open('wb') as log:
    subprocess.run(['pce-ibmpc','-c','test.cfg','-t','null','-g','vga'],cwd=FOLDER,input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,timeout=300,check=True)
def screen(name):
    v=(FOLDER/(name+'.bin')).read_bytes()
    text='\n'.join(bytes(v[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
    (FOLDER/(name+'.txt')).write_text(text)
    return text
for name in ['list','fat-list']:
    text=screen(name)
    for item in ['A','B','"Mixed Value"','"AA AA"','"A,B"','"A)B"','""']:
        assert 'List=['+item+']' in text,(name,item,text)
    assert 'Literal=*.ZZZ' in text and 'Conditional=y' in text and 'ListDone' in text,text
    assert 'WRONG' not in text,text
for name in ['range','fat-range']:
    text=screen(name)
    for item in ['Up=1','Up=2','Up=3','Down=3','Down=2','Down=1','Signed=-1','Signed=0','Signed=1','Max=32767','Min=-32768','Quoted="1..3"','RangeDone']:
        assert item in text,(item,text)
text=screen('files')
for item in ['ONE.ZZZ','TWO.ZZZ','MANY.ZZZ']:
    assert text.count('CPM=[A:'+item+']')==1,(item,text)
for item in ['A.COM','B.COM','HIDE.COM']:
    assert text.count('FAT=[B:\\SUB\\'+item+']')==1,(item,text)
assert 'DIR.COM' not in text and 'WRONG' not in text and 'MappingPreserved' in text and 'FilesDone' in text,text
text=screen('paths')
for item in ['Relative=[B:SUB\\A.COM]','Parent=[B:\\SUB\\..\\SUB\\A.COM]','Native=B:\\SUB\\A.COM','Native=B:\\SUB\\B.COM','Native=B:\\SUB\\HIDE.COM','PathDone']:
    assert item in text,(item,text)
text=screen('execute')
for item in ['DosValue=1','DosValue=2','DosValue=3','DosStatus','NativeValue=A','NativeValue=B','ExecDone']:
    assert item in text,(item,text)
text=screen('errors')
assert 'ErrorsContinue' in text and 'WRONG' not in text,text
assert text.count('IF [NOT]')==2,text
assert text.count('Nested FOR')==2,text
text=screen('jump')
assert 'GotoLeavesLoop' in text and 'ChainLeavesLoop' in text and 'WRONG' not in text,text
assert 'BATCH EXIT PASS' in screen('status'),screen('status')
print('PASS: FOR quoted lists, signed ranges, CP/M extent deduplication, FAT directories/hidden/system files, absolute/relative/parent paths, IF search isolation, native/DOS dispatch/status, errors, GOTO/BAT replacement and EXIT')
shutil.rmtree(FOLDER)
