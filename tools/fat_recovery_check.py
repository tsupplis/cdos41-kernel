#!/usr/bin/env python3
"""Execute recovered FAT and directory ownership code with synthetic dependencies."""
from historical_check import CON,symbols,payload,word
from pctmp_recovery_check import RSP,syms,bases,near,asm

def separate_near(code,entry,body):
 # BDOS code and data overlap in offset space: keep their segments distinct.
 near(code,entry,'mov ax,ds\nadd ax,1000h\nmov ds,ax\nmov es,ax\n'+body)

def hook(code,at,source):
 dest=len(code);code+=asm(source);code[at:at+3]=b'\xe9'+word((dest-at-3)&65535)

def fat():
 data=symbols('pcbdos');bs=symbols('black')
 # LINK86 concatenates code without an implied even-byte boundary.
 black=symbols('bdos')['PCSEARCH']-bs['PCSEARCH']
 C=lambda n:black+bs[n]
 D=lambda n:data[n]
 base=payload('bdos')
 # Stop exactly at the two outcomes of the allocation-boundary decision.
 count=0
 for limit in [0x300,0xff0,0x6000]:
  for successor in [limit-1,limit,limit+1,0xff7,0xff8,0xffff]:
   for reading in [0,1]:
    code=bytearray(base)
    hook(code,C('CNPR7'),'mov byte [0f000h],1\nret')
    hook(code,C('CNPR8'),'mov byte [0f000h],2\nret')
    separate_near(code,C('CNPR6'),f'''mov byte [{D('BDRWFLG')}],{reading}
 mov word [{D('NCLSTRS')}],{limit}
 mov ax,{successor}
 call far [cs:target]
 cmp byte [0f000h],{1 if not reading and successor>limit else 2}
 jne failed
''');count+=1
 print(f'PASS: {count} FAT12/FAT16 successor/volume-limit/read-write boundary cases')
 for initial in [0,0xf0,0x80,0xff]:
  code=bytearray(base)
  separate_near(code,C('TESTFILE'),f'''mov byte [{D('RD_DIR_FLAG')}],{initial}
 mov byte [{D('DONT_CLOSE')}],0
 call far [cs:target]
 cmp byte [{D('RD_DIR_FLAG')}],{initial|15}
 jne failed
''')
 count=0
 for mult,extended in [(1,128),(2,128),(1,0)]:
  for cks in [0,0x1000,0x4000,0x8000,0x5000]:
   for missing in [False,True]:
    code=bytearray(base);active=mult==1 and extended!=0
    # getdir records the invalidation policy and returns a different directory.
    hook(code,C('GETDIR'),f'''cmp word [{D('DCNT')}],0ffffh
 jne bad
 cmp word [{D('CHDBLK')}],0
 jne bad
 cmp cx,2
 jne bad
 mov al,[{D('RD_DIR_FLAG')}]
 mov [0f002h],al
 mov word [{D('DIRP')}],0f200h
 mov ax,{0 if missing else 0xf200}
 ret
bad:
 mov byte [0f003h],1
 xor ax,ax
 ret
''')
    hook(code,C('SET_SDCNT'),'ret')
    hook(code,data['SEARCH_OLIST'],'mov ax,1\nor ax,ax\nret')
    hook(code,data['WRDIR'],'inc byte [0f010h]\nret')
    worker=len(code)
    code+=asm(f'org {worker}\ncall {C("EXTENDF")}\nmov byte [0f020h],1\nret')
    body=f'''mov byte [{D('MULT_CNT')}],{mult}
 mov byte [{D('HIGH_EXT')}],{extended}
 mov word [{D('CHKSIZ')}],{cks}
 mov word [{D('DCNT')}],99
 mov word [{D('CHDBLK')}],123
 mov word [{D('DIRP')}],0f100h
 mov byte [{D('RD_DIR_FLAG')}],0
 mov byte [{D('LRET')}],0
 mov word [0f002h],0
 mov byte [0f010h],0
 mov byte [0f020h],0
 mov word [0f11ah],05555h
 mov word [0f11ch],06666h
 mov word [0f11eh],07777h
 mov word [0f21ah],0
 mov word [0f21ch],1
 mov word [0f21eh],0
 mov byte [0f20bh],0
 mov word [{D('INFO_FCB')+26}],1234h
 mov word [{D('INFO_FCB')+28}],2345h
 mov word [{D('INFO_FCB')+30}],2
 mov [0f030h],sp
 call far [cs:target]
 cmp sp,[0f030h]
 jne failed
 cmp byte [0f003h],0
 jne failed
 cmp byte [0f002h],{(15 if cks&0x5000 else 255) if active else 0}
 jne failed
 cmp byte [0f010h],{int(active and not missing)}
 jne failed
 cmp byte [0f020h],{int(not(active and missing))}
 jne failed
 cmp byte [{D('LRET')}],{11 if active and missing else 0}
 jne failed
 cmp word [0f11ah],05555h
 jne failed
 cmp word [0f11ch],06666h
 jne failed
 cmp word [0f11eh],07777h
 jne failed
'''
    if active and not missing:
     body+='cmp word [0f21ah],1234h\njne failed\ncmp word [0f21ch],2345h\njne failed\ncmp word [0f21eh],2\njne failed\n'
    separate_near(code,worker,body);count+=1
 print(f'PASS: directory lookup forcing and {count} extension cases: fresh/stale buffers, CKS flags, skipped updates, error 11 and balanced error unwind')

def ownership():
 s=syms('ms2');cb,db=bases('ms2');b=(RSP/'pctmp.rsp').read_bytes();base=bytearray(b[128:128+int.from_bytes(b[1:3],'little')*16]);count=0
 for owners in [1,2,5]:
  for mode in ['existing-empty','existing-full','no-cat']:
   code=bytearray(base)
   body=f'''mov word [{db+s['SAVE_PD_OFF']}],0f000h
 mov word [0f02eh],0f200h
 mov word [0f12eh],{0 if mode=='no-cat' else 0xf300}
 mov word [0f200h],0f400h
 mov word [0f202h],0
 mov word [0f220h],1
 mov word [0f300h],{0xf500 if mode=='existing-full' else 0}
 mov word [0f320h],{owners}
 mov word [0f408h],7
 mov word [0f508h],9
 mov si,0f100h
 xor bx,bx
 call far [cs:target]
 cmp si,0f100h
 jne failed
 cmp word [0f408h],{7+(owners if mode=='existing-empty' else 1 if mode=='no-cat' else 0)}
 jne failed
 cmp word [0f508h],9
 jne failed
 cmp word [0f220h],{2 if mode=='no-cat' else 1}
 jne failed
 cmp word [0f12eh],{0xf200 if mode=='no-cat' else 0xf300}
 jne failed
'''
   if mode=='no-cat':
    # Zero all remaining drive entries; no unrelated HDS may be incremented.
    body='mov di,0f204h\nmov cx,14\nxor ax,ax\nrep stosw\n'+body
   else:body+=f'cmp word [0f300h],{0xf500 if mode=="existing-full" else 0xf400}\njne failed\n'
   separate_near(code,cb+s['GIVE_PARENT'],body);count+=1
 print(f'PASS: {count} CAT/HDS inheritance cases, shared-owner counts and unchanged already-owned/no-CAT paths')

if __name__=='__main__':fat();ownership()
