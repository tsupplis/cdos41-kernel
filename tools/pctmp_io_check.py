#!/usr/bin/env python3
"""Exercise assembled DOS console, label-search and allocation-info recoveries.

Console/disk dependencies are synthetic; tested routines come from PCTMP.RSP.
"""
from pctmp_recovery_check import RSP,syms,bases,near,asm,word
b=(RSP/'pctmp.rsp').read_bytes()
BASE=bytearray(b[128:128+int.from_bytes(b[1:3],'little')*16])
S=syms('ms1');CB,DB=bases('ms1')
C=lambda n:CB+S[n]
D=lambda n:DB+S[n]

def stub(code,name,source):
 at=C(name);dest=len(code);code+=asm(source)
 code[at:at+3]=b'\xe9'+word((dest-at-3)&65535)

def setbytes(address,data):
 return ''.join(f'mov byte [{address+i}],{v}\n' for i,v in enumerate(data))

def console():
 cases=[(0,b'ignored\r',None),(1,b'abc\r',b''),(2,b'abc\r',b'a'),
        (5,b'abcdXYZ\r',b'abcd'),(5,b'ab\x08c\r',b'ac'),
        (5,b'ab\x7fc\r',b'ac'),(5,b'\x7f\x08A\r',b'A'),
        (5,b'abcd\x7fZ\r',b'abcZ'),(255,b'x'*260+b'\r',b'x'*254)]
 for capacity,keys,wanted in cases:
  code=bytearray(BASE)
  stub(code,'CONIN','push bx\nmov bx,[0f000h]\nmov al,[bx]\ninc bx\nmov [0f000h],bx\npop bx\nret')
  stub(code,'CONBRK','xor ax,ax\nret');stub(code,'PUTCHAR','ret')
  ms2=syms('ms2');_,data2=bases('ms2')
  body=f'''mov word [{D('LEGACY_IO_FLAGS')}],0
 mov byte [{D('LINE_SKIP_LF')}],0
 mov word [{data2+ms2['HCB_LIST']}],0
 mov word [{data2+ms2['LINE_INPUT_HCB']}],0
 mov word [0f000h],0f100h
 mov word [{D('RDBUF_DX')}],0f400h
 mov byte [{D('COLUMN')}],0
 mov byte [{D('COMPCOL')}],0
 mov byte [{D('LISTCP')}],0
 mov di,0f400h
 mov cx,260
 mov al,055h
 rep stosb
 mov byte [0f400h],{capacity}
'''+setbytes(0xf100,keys)+'call far [cs:target]\n'
  expected=b'\x55' if wanted is None else bytes([len(wanted)])+wanted+b'\r'
  for i,v in enumerate(expected):body+=f'cmp byte [{0xf401+i}],{v}\njne failed\n'
  body+=f'cmp byte [{0xf402+capacity}],055h\njne failed\n'
  body+=f'cmp word [0f000h],{0xf100 if wanted is None else 0xf100+len(keys)}\njne failed\n'
  near(code,C('READ'),body)
 for char in [3,0,65,127]:
  code=bytearray(BASE);stub(code,'CONECH',f'mov al,{char}\nret')
  stub(code,'C_TERM','mov byte [0f010h],1\nret')
  near(code,C('MS_CONIN'),f'''mov byte [0f010h],0
 mov byte [{D('RET_AL')}],055h
 call far [cs:target]
 cmp byte [0f010h],{int(char==3)}
 jne failed
 cmp byte [{D('RET_AL')}],{0x55 if char==3 else char}
 jne failed
''')
 print('PASS: DOS console capacity 0/1/2/5/255, CR bounds, overflow input, Backspace/DEL and function 01h Ctrl-C (13 cases)')

def labels():
 cases=[(0x11,b'VERIFY     ',b'VERIFY     ',0),(0x11,b'???????????',b'VERIFY     ',0),
        (0x11,b'V?RIFY     ',b'VERIFY     ',0),(0x11,b'VERIFY    X',b'VERIFY     ',255),
        (0x11,b'NO MATCH   ',b'VERIFY     ',255),(0x11,b'???????????',b'           ',255),
        (0x12,b'???????????',b'VERIFY     ',255)]
 for function,mask,label,expected in cases:
  for drive in [0,2]:
   code=bytearray(BASE)
   stub(code,'BDOS','inc byte [0f010h]\nret')
   stub(code,'ABDOS','inc byte [0f011h]\nret')
   stub(code,'SRCHF','mov si,0f200h\nxor ax,ax\nret')
   body=f'''mov byte [{D('MS_AH')}],{function}
 mov byte [{D('CUR_DSK')}],1
 mov word [{D('MS_FCB_PTR')}],0f100h
 mov word [{D('MS_FCB_PTR')+2}],ds
 mov word [0f010h],0
 mov byte [0f100h],{drive}
 mov byte [0f200h],32
 mov byte [0f300h],2
 mov byte [{D('DIR_ATTR')}],0
 mov di,0f300h
'''+setbytes(0xf101,mask)+setbytes(0xf201,label)+f'''call far [cs:target]
 cmp al,{expected}
 jne failed
 cmp byte [0f010h],{int(function==0x11)}
 jne failed
 cmp byte [0f011h],{int(function==0x11)}
 jne failed
'''
   if expected==0:body+=f'cmp byte [{D("DIR_ATTR")}],8\njne failed\ncmp byte [0f300h],2\njne failed\n'
   near(code,C('SRCH_LABEL'),body)
 print('PASS: volume-label exact/wildcard/mismatch/empty/find-next and explicit/default drive (14 cases)')


def allocation():
 count=0
 for kind in ['fat12','fat16','cpm','external-cpm']:
  for entry,drive in [('MS_GET_ALLOC',3),('MS_SPEC_ALLOC',0),('MS_SPEC_ALLOC',2),('MS_SPEC_ALLOC',3)]:
   for failure in ['none','select','dpb']:
    selected=(drive-1 if entry=='MS_SPEC_ALLOC' and drive else 1)
    switch=selected!=1
    error=failure=='dpb' or failure=='select' and switch
    code=bytearray(BASE)
    stub(code,'BDOS',f'mov [0f010h],dl\ninc byte [0f011h]\nmov al,{int(failure=="select")}\nret')
    stub(code,'ABDOS','mov [0f012h],dl\ninc byte [0f013h]\nret')
    stub(code,'BDOS_RETURN_ES',f'''inc byte [0f014h]
 mov ax,ds
 {'add ax,1000h' if kind=='external-cpm' else ''}
 mov es,ax
 mov bx,0f200h
 mov ax,{65535 if failure=='dpb' else 0}
 mov dx,0beefh
 mov cx,0beefh
 ret
''')
    body=f'''mov word [{C('SYSDAT')}],ds
 mov word [{D('MS_SS')}],ds
 mov word [{D('MS_SP')}],0f600h
 mov byte [{D('CUR_DSK')}],1
 mov word [0f010h],0
 mov word [0f012h],0
 mov word [0f014h],0
 mov word [0c1ah],0f100h
 mov word [0c1ch],0f100h
 mov word [0f108h],0f200h
 mov word [0f112h],1234h
 mov byte [{D('RET_AL')}],0
 mov ax,ds
 {'add ax,1000h' if kind=='external-cpm' else ''}
 mov es,ax
 mov word [es:0f200h],{0xfffe if kind=='fat12' else 0xffff if kind=='fat16' else 32}
'''
    if kind.startswith('fat'):
     body+='mov word [es:0f206h],640\nmov word [es:0f208h],4096\nmov byte [es:0f21bh],2\n';sectors,units=8,638
    else:
     body+='mov byte [es:0f202h],4\nmov word [es:0f205h],199\nmov byte [es:0f20fh],2\n';sectors,units=4,200
    body+=f'''mov dl,{drive}
 call far [cs:target]
 cmp byte [{D('RET_AL')}],{255 if error else sectors}
 jne failed
 cmp byte [0f011h],{int(switch)}
 jne failed
 cmp byte [0f013h],{int(switch and failure!='select')}
 jne failed
 cmp byte [0f014h],{int(not(switch and failure=='select'))}
 jne failed
'''
    if switch:
     body+=f'cmp byte [0f010h],{selected}\njne failed\n'
     if failure!='select':body+='cmp byte [0f012h],1\njne failed\n'
    if not error:
     body+=f'''cmp word [{D('MS_CX')}],512
 jne failed
 cmp word [{D('MS_DX')}],{units}
 jne failed
'''
     if kind!='external-cpm':body+=f'cmp word [{D("MS_BX")}],0\njne failed\ncmp word [0f600h],1234h\njne failed\n'
    near(code,C(entry),body);count+=1
 print(f'PASS: {count} DOS allocation-info cases: FAT12/FAT16/CP/M/external DPB, default/current/other drive, selection/DPB failures and drive restoration')

if __name__=='__main__':
 console();labels();allocation()
