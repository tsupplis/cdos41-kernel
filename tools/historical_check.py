#!/usr/bin/env python3
"""Execute recovered BDOS/XIOS code with synthetic FCBs, BCBs and dispatch targets.

NASM builds only the disposable DOS test driver; the production payload is
assembled by the project's normal ASM86/RASM86 recipes. No disks are accessed.
"""
from pathlib import Path
import os,re,subprocess,tempfile
ROOT=Path(os.environ.get('CDOS_TEST_ROOT',Path(__file__).resolve().parent.parent))
CON=ROOT/'kernel/con'
def symbols(name):
 return {n:int(v,16) for v,n in re.findall(r'\b([0-9A-F]{4})\s+([A-Z][A-Z0-9_]*)',(CON/(name+'.sym')).read_text(errors='replace'))}
def payload(name):
 b=(CON/(name+'.con')).read_bytes();return bytearray(b[128:128+int.from_bytes(b[1:3],'little')*16])
def word(n):return n.to_bytes(2,'little')
def run(code,entry,body):
 with tempfile.TemporaryDirectory(prefix='cdos-historical-') as tmp:
  p=Path(tmp);(p/'payload.bin').write_bytes(code)
  (p/'test.asm').write_text('''bits 16
cpu 8086
org 100h
 mov ax,cs
 add ax,(payload-$$+100h)/16
 mov [target+2],ax
 mov ds,ax
 mov es,ax
 cld
'''+body+'''
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
target: dw '''+str(entry)+''',0
align 16
payload: incbin "payload.bin"
''')
  subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=p,check=True,capture_output=True)
  r=subprocess.run(['emu2','test.com'],cwd=p,capture_output=True,timeout=5)
  assert r.returncode==0,(entry,r.returncode,r.stdout,r.stderr)
def check():
 s=symbols('pcbdos');code=payload('bdos');code[s['RETMON6']]=0xcb
 for length in [0,1,36]:
  for directory in [0,255]:
   run(code,s['RETMON'],f'''
 mov byte [{s['PARLG']}],{length}
 mov byte [{s['HDIRFX']}],{directory}
 mov word [{s['INFO']}],0f100h
 mov word [{s['PARAMETERSEGMENT']}],ax
 mov di,0f100h
 mov cx,38
 mov al,055h
 rep stosb
 mov di,{s['INFO_FCB']}
 mov cx,36
 mov al,022h
 rep stosb
 call far [cs:target]
 cmp byte [0f100h],{(0x22|(0x80 if directory else 0)) if length else 0x55}
 jne failed
 cmp byte [0f100h+{length}],055h
 jne failed
''')
 print('PASS: FCB return, directory flag and copy boundaries (6 cases)')
 code=payload('bdos')
 # Replace only external dependencies: selection, media I/O and return to caller.
 for name,data in [('DISK_SELECT',b'\xa2'+word(s['ADRIVE'])+b'\xc3'),('CHECK_MEDIA',b'\xff\x06\x00\xf0\xc3'),('CURSELECTX',b'\xcb'),('RET20',b'\xcb')]:
  code[s[name]:s[name]+len(data)]=data
 for drives,pending,expected in [([2],[255],0),([1],[255],1),([1],[0],0),([2,1],[255,255],1),([2,1],[255,0],0),([],[],0)]:
  body=f'mov byte [{s["MEDIA_FLAG"]}],1\nmov word [{s["DLOG"]}],2\nmov word [{s["DAT_BCBA"]}],0f010h\nmov word [0f010h],{0xf100 if drives else 0}\nmov word [0f000h],0\n'
  for i,(drive,dirty) in enumerate(zip(drives,pending)):
   a=0xf100+16*i;body+=f'mov byte [{a}],{drive}\nmov byte [{a+4}],{dirty}\nmov word [{a+12}],{a+16 if i+1<len(drives) else 0}\n'
  run(code,s['CHECK_ALL_MEDIA'],body+f'call far [cs:target]\ncmp word [0f000h],{expected}\njne failed\n')
 print('PASS: shared buffer chains, selected/other drive and clean/dirty buffers (6 cases)')
 s=symbols('squid');code=payload('xios');stub=len(code);code+=b'\xb8\x34\x12\xc3'
 for i in range(39):code[s['FUNCTIONTABLE']+2*i:s['FUNCTIONTABLE']+2*i+2]=word(stub)
 run(code,s['ENTRY'],'''xor si,si
next_function:
 mov ax,si
 call far [cs:target]
 mov dx,0ffffh
 cmp si,38
 ja expect_result
 mov dx,1234h
expect_result:
 cmp ax,dx
 jne failed
 cmp bx,dx
 jne failed
 inc si
 cmp si,256
 jb next_function
''')
 print('PASS: all 256 XIOS function bytes, valid dispatch and invalid AX/BX results')
if __name__=='__main__':check()
