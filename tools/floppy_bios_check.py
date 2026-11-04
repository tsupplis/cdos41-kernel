"""Exercise DOS BIOS floppy reads on newly created disposable images only."""
from pathlib import Path
import tempfile,subprocess,re,shutil,argparse
parser=argparse.ArgumentParser(description='Read the last sector and cross head/cylinder boundaries through DOS INT 13h.')
parser.add_argument('--format',type=int,choices=(360,720,1200,1440),default=1440)
capacity=parser.parse_args().format
cylinders,spt,spc={360:(40,9,2),720:(80,9,2),1200:(80,15,1),1440:(80,18,1)}[capacity]
R=Path(__file__).resolve().parent.parent;F=Path(tempfile.mkdtemp(prefix='cdos-floppy-bios-'));print(F,flush=True)
def run(*args,**kw):return subprocess.run(args,cwd=F,check=True,capture_output=True,**kw)
(F/'probe.asm').write_text(f'''bits 16
cpu 8086
org 100h
push cs
pop ds
push cs
pop es
mov dl,2
mov ah,36h
int 21h
cmp ax,0ffffh
je failed
mov dx,stage1
mov ah,9
int 21h
mov ax,0201h
mov bx,buffer
mov cx,{((cylinders-1)<<8)|spt:04x}h
mov dx,1
int 13h
jc failed
mov di,buffer
mov al,0d3h
mov cx,512
repe scasb
jne failed
mov dx,stage2
mov ah,9
int 21h
mov ax,0202h
mov bx,buffer
mov cx,{((cylinders-1)<<8)|spt:04x}h
mov dx,1
int 13h
jc failed
mov di,buffer
mov al,0d3h
mov cx,1024
repe scasb
jne failed
mov dx,stage3
mov ah,9
int 21h
mov ax,0202h
mov bx,buffer
mov cx,{((cylinders-2)<<8)|spt:04x}h
mov dx,0101h
int 13h
jc failed
mov di,buffer
mov al,0d3h
mov cx,1024
repe scasb
jne failed
mov dx,passed
jmp report
failed:
mov dx,failure
report:
mov ah,9
int 21h
mov ax,4c00h
int 21h
stage1 db 13,10,'BIOS last-sector read...',13,10,'$'
stage2 db 'BIOS cross-head read...',13,10,'$'
stage3 db 'BIOS cross-cylinder read...',13,10,'$'
passed db 'DOS BIOS floppy probe PASSED',13,10,'$'
failure db 'DOS BIOS floppy probe FAILED',13,10,'$'
buffer times 1024 db 0
''')
run('nasm','-f','bin','probe.asm','-o','bioprobe.com')
(F/'diskdefs').write_bytes((R/'media/diskdefs').read_bytes())
run('python3',str(R/'tools/cpm86twist.py'),'untwist',str(R/'media/cdos86base.img'),'logical.img')
run('cpmcp','-f','ccpm86-320','logical.img',str(R/'kernel/sysgen/ccpm.sys'),'0:CCPM.SYS')
run('cpmcp','-f','ccpm86-320','logical.img','bioprobe.com','0:BIOPROBE.COM')
run('python3',str(R/'tools/cpm86twist.py'),'twist','logical.img','source.img')
run('mformat','-C','-i','target.img','-t',str(cylinders),'-h','2','-n',str(spt),'-c',str(spc),'::')
b=bytearray((F/'target.img').read_bytes());last=(cylinders-1)*2*spt+spt-1; b[last*512:(last+2)*512]=bytes([0xd3])*1024; last=(cylinders-1)*2*spt-1; b[last*512:(last+2)*512]=bytes([0xd3])*1024;(F/'target.img').write_bytes(b)
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('sdl:lowpass=5000','null').replace('cdos86.img','source.img').replace('cdostools.img','target.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg);(F/'test.cfg').write_text(cfg)
c=['c f000000']
for ch in 'bioprobe':c+=['key '+ch,'c 200000']
c+=['key Return','c 40000000','save "screen.bin" bin b800:0000 fa0','q']
p=run('pce-ibmpc','-c','test.cfg','-t','null','-g','vga',input=('\n'.join(c)+'\n').encode(),timeout=120)
(F/'pce.log').write_bytes(p.stdout+p.stderr)
b=(F/'screen.bin').read_bytes();s='\n'.join(b[i:i+160:2].decode('cp437').rstrip() for i in range(0,4000,160));print(s);(F/'screen.txt').write_text(s)
assert 'DOS BIOS floppy probe PASSED' in s

print(f'PASS: DOS INT 13h {capacity}K last-sector, cross-head and cross-cylinder reads')
shutil.rmtree(F)
