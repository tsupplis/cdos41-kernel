#!/usr/bin/env python3
"""Run recovered PCTMP routines; stub file I/O/allocation for EXEC control-flow tests."""
from pathlib import Path
import re,subprocess,tempfile,os
from historical_check import run,word
ROOT=Path(os.environ.get('CDOS_TEST_ROOT',Path(__file__).resolve().parent.parent))
RSP=ROOT/'kernel/rsp3'
def syms(module):
 return {n:int(v,16) for v,n in re.findall(r'\b([0-9A-F]{4})\s+([A-Z][A-Z0-9_]*)',(RSP/(module+'.sym')).read_text(errors='replace'))}
def bases(module):
 text=(RSP/'pctmp.map').read_text();part=text.split('map for module:  '+module.upper())[1].split('map for module:')[0]
 return [int(v,16) for v in re.findall(r'\(0000:([0-9A-F]+)-',part)]
def near(code,entry,body):
 code=bytearray(code);at=len(code);code+=b'\xe8'+word((entry-at-3)&65535)+b'\xcb';run(code,at,body)
def asm(source):
 with tempfile.TemporaryDirectory() as td:
  p=Path(td);(p/'stub.asm').write_text('bits 16\ncpu 8086\n'+source)
  subprocess.run(['nasm','-f','bin','stub.asm','-o','stub.bin'],cwd=p,check=True,capture_output=True)
  return (p/'stub.bin').read_bytes()
def check():
 b=(RSP/'pctmp.rsp').read_bytes();base=bytearray(b[128:128+int.from_bytes(b[1:3],'little')*16]);s1=syms('ms1');s2=syms('ms2');c1,d1=bases('ms1');c2,d2=bases('ms2')
 C=lambda n:c2+s2[n];D=lambda n:d2+s2[n]
 near(base,c1+s1['PSP_DOS_ENTRY'],'''mov di,40h
 mov cx,32
 mov al,055h
 rep stosb
 call far [cs:target]
 cmp word [50h],21cdh
 jne failed
 cmp byte [52h],0cbh
 jne failed
 cmp byte [4fh],055h
 jne failed
 cmp byte [53h],055h
 jne failed
''')
 print('PASS: assembled PSP call stub and neighbouring bytes')
 # Ensure the real DOS dispatch table selects the recovered handlers.
 for function,name in [(0x50,'MS2_SET_PSP'),(0x51,'MS2_GET_PSP')]:
  at=C('MS2_FUNC_TABLE')+2*(function-0x2f)
  assert int.from_bytes(base[at:at+2],'little')==C(name)
 for value in [0,0x1234,0xffff]:
  near(base,C('MS2_SET_PSP'),f'mov word [{D("MS2_BX")}],{value}\ncall far [cs:target]\ncmp word [{D("ACTIVE_PSP")}],{value}\njne failed\n')
  near(base,C('MS2_GET_PSP'),f'mov word [{D("ACTIVE_PSP")}],{value}\ncall far [cs:target]\ncmp word [{D("MS2_BX")}],{value}\njne failed\n')
 print('PASS: PSP 50h/51h dispatch and six get/set boundary cases')
 cases=0
 for com in [False,True]:
  for function in [0,1,2,3,255]:
   for fail in [False,True]:
    code=bytearray(base)
    stubs={
     'SAVE_SET_DTA':'ret',
     'FILE_PATH_PREP':('mov al,2\nstc\nret' if fail else 'clc\nret'),
     'OPEN_FCB':'clc\nret',
     'COM_CHECK':('xor ax,ax\nret' if com else 'mov ax,1\nor ax,ax\nret'),
     'CALC_PSP':'ret','COM_LOAD':'clc\nret',
     'EXE_READ_HEADER':f'mov word [{D("EXE_HDR_SP")}],0a100h\nmov word [{D("EXE_HDR_SS")}],3\nmov word [{D("EXE_HDR_IP")}],0123h\nmov word [{D("EXE_HDR_CS")}],4\nclc\nret',
     'EXE_LOAD_RELOC':'clc\nret',
     'SET_UP_PSP':'mov dx,2000h\nret',
     'SET_COM_REGS':f'mov word [{D("EXE_HDR_SP")}],0fffeh\nmov word [{D("EXE_HDR_SS")}],2000h\nmov word [{D("EXE_HDR_IP")}],100h\nmov word [{D("EXE_HDR_CS")}],2000h\nret',
     'GO_TO_CHILD':'mov byte [0f000h],1\nret',
     'RESTORE_DTA':'inc byte [0f006h]\nret',
     'MS2_ERROR_RET':'mov [0f002h],al\nmov byte [0f003h],1\nret',
    }
    for name,source in stubs.items():
     at=C(name);dest=len(code);code+=asm(source);code[at:at+3]=b'\xe9'+word((dest-at-3)&65535)
    error=fail or function not in [0,1,3]
    body=f'''mov word [{D('MS2_AX')}],{0x4b00+function}
 mov word [{D('MS2_ES')}],ax
 mov word [{D('MS2_BX')}],0f100h
 mov word [0f100h],2000h
 mov word [0f102h],2100h
 mov word [0f000h],0
 mov word [0f002h],0
 mov word [0f006h],0
 mov word [0f10ch],05555h
 mov word [0f116h],05555h
 call far [cs:target]
 cmp byte [0f000h],{int(not error and function==0)}
 jne failed
 cmp byte [0f003h],{int(error)}
 jne failed
 cmp byte [0f006h],{int(error or function==3)}
 jne failed
 cmp word [0f10ch],05555h
 jne failed
 cmp word [0f116h],05555h
 jne failed
'''
    if error:body+=f'cmp byte [0f002h],{2 if fail else 1}\njne failed\n'
    if not error and function==1:
     for i,v in enumerate([0xfffe,0x2000,0x100,0x2000] if com else [0xa100,0x2013,0x123,0x2014]):body+=f'cmp word [{0xf10e+2*i}],{v}\njne failed\n'
    near(code,C('MS2_EXEC'),body);cases+=1
 print(f'PASS: {cases} assembled EXEC cases: COM/EXE, execute/load-only/overlay, invalid subfunctions and failure cleanup (I/O/loaders stubbed)')
if __name__=='__main__':check()
