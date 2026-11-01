#!/usr/bin/env python3
"""Exercise assembled INT 24h recovery with synthetic BDOS and handler calls.

Only the interrupt handler and external BDOS/process lookup are stubbed.
The real frame construction, stack switching, restoration and retry run.
"""
from pctmp_recovery_check import RSP,syms,bases,near,asm
from fat_recovery_check import hook
from historical_check import word

def check():
 b=(RSP/'pctmp.rsp').read_bytes();base=bytearray(b[128:128+int.from_bytes(b[1:3],'little')*16])
 s1,s2=syms('ms1'),syms('ms2');c1,d1=bases('ms1');c2,d2=bases('ms2')
 C1=lambda n:c1+s1[n];D1=lambda n:d1+s1[n]
 C2=lambda n:c2+s2[n];D2=lambda n:d2+s2[n]
 setup=f'''mov [{C1('SYSDAT')}],ds
 mov word [68h],0e000h
 mov word [0e02eh],0e100h
 mov word [0e104h],0e200h
 mov byte [0e200h],1
 mov byte [9dh],3
 mov byte [{D1('CUR_DSK')}],2
'''
 count=0
 for drive,cat,hds,physical in [(2,0xe100,0xe200,1),(0x82,0xe100,0xe200,1),(255,0xe100,0xe200,1),(2,0,0,2),(15,0,0,3)]:
  for error,expect in [(0x2ff,0),(0x4ff,2),(0x6ff,None),(0,None)]:
   code=bytearray(base)
   hook(code,C1('BDOS'),f'mov ax,{error}\nret')
   hook(code,C1('DO_CRITICAL_ERROR'),'mov [0f000h],ax\nmov [0f002h],di\npop di\nret')
   near(code,C1('CHECK_ERROR'),setup+f'''mov word [0e02eh],{cat}
 mov word [0e104h],{hds}
 mov word [0f000h],0ffffh
 mov word [0f002h],0ffffh
 mov di,5555h
 mov ax,{0x500+drive}
 call far [cs:target]
 cmp di,5555h
 jne failed
 cmp word [0f000h],{0xffff if expect is None else 0x500+physical}
 jne failed
 cmp word [0f002h],{0xffff if expect is None else expect}
 jne failed
''');count+=1
 print(f'PASS: {count} BDOS error/drive normalization and backing-drive mapping cases')
 for physical_error, expected in [(3,0),(0x80,2),(0x20,2),(1,3),(0x10,4),(0x40,6),(2,8),(4,8),(8,12),(9,12),(0x7f,12)]:
  code=bytearray(base)
  hook(code,C1('BDOS'),'mov ax,1ffh\nret')
  hook(code,C1('DO_CRITICAL_ERROR'),'mov [0f002h],di\npop di\nret')
  near(code,C1('CHECK_ERROR'),setup+f'''mov [0e010h],ds
 mov byte [67h],{physical_error}
 mov ax,502h
 call far [cs:target]
 cmp word [0f002h],{expected}
 jne failed
''')
 print('PASS: eleven physical error translations, including timeout and unknown error fallback')
 # Run both complete critical-error paths. Replace INT 24h + get_data_seg
 # with a near stub that observes the constructed application stack and
 # corrupts the context slots, as DOS console reentry would. The real code
 # must restore every saved register and both outer stack pairs.
 for dos2 in [False,True]:
  for action in [0,1,2]:
   code=bytearray(base);D=D2 if dos2 else D1;prefix='MS2_' if dos2 else 'MS_'
   frame=['AX','BX','CX','DX','SI','DI','BP','DS','ES']
   hook(code,C1('GET_DATA_SEG'),'ret')
   retries=1 if dos2 and action==0 or action==2 else 12
   hook(code,C1('BDOS'),f'''inc word [0f010h]
 cmp word [0f010h],{retries}
 ja success
 mov ax,2ffh
 ret
success: xor ax,ax
 ret''')
   start=C2('MS2_CRITICAL_ERROR') if dos2 else C1('CRITICAL_DOS1')
   at=code.index(b'\xcd\x24',start)
   stub=len(code)
   body='mov bp,sp\n'
   for i,name in enumerate(frame):
    body+=f'cmp word [ss:bp+{2*i+2}],{0x100+i}\njne bad\n'
   body+='inc word [0f012h]\n'
   for name in frame:body+=f'mov word [{D(prefix+name)}],0ddddh\n'
   body+=f'mov word [{D1("MS_SP")}],0f700h\n'
   if dos2:body+=f'mov word [{D2("MS2_SP")}],0f600h\n'
   body+=f'mov al,{action}\nret\nbad: mov byte [0f014h],1\nmov al,2\nret'
   code+=asm(body);code[at:at+5]=b'\xe8'+word((stub-at-3)&65535)+b'\x90\x90'
   # Abort never returns to the interrupted call; model INT22 by restoring
   # the harness caller's far frame and record that termination was selected.
   at=code.index(b'\xcd\x22',start)
   stub=len(code);code+=asm('mov byte [0f016h],1\ncli\nmov ss,[0f042h]\nmov sp,[0f040h]\nsub sp,4\nretf')
   code[at:at+3]=b'\xe9'+word((stub-at-3)&65535)
   body=setup+f'''mov byte [{D1('DOS1_CALL')}],{0 if dos2 else 255}
 mov [{D1('MS_SS')}],ds
 mov word [{D1('MS_SP')}],0f800h
 mov [{D2('MS2_SS')}],ds
 mov word [{D2('MS2_SP')}],0f900h
 mov word [{D1('RET_AX')}],1234h
 mov word [{D2('MS2_RET_AX')}],5678h
 mov word [0f800h],9999h
 mov word [0f010h],0
 mov word [0f012h],0
 mov word [0f014h],0
 mov word [0f016h],0
 mov [0f040h],sp
 mov [0f042h],ss
'''
   for i,name in enumerate(frame):body+=f'mov word [{D(prefix+name)}],{0x100+i}\n'
   body+='mov ax,502h\ncall far [cs:target]\n'
   body+=f'''cmp sp,[0f040h]
 jne failed
 cmp byte [0f014h],0
 jne failed
 cmp byte [0f016h],{int(action==2)}
 jne failed
 cmp word [0f012h],{retries}
 jne failed
 cmp word [0f010h],{retries+int(action!=2 and not(dos2 and action==0))}
 jne failed
 cmp word [{D1('MS_SP')}],0f800h
 jne failed
 cmp word [{D2('MS2_SP')}],0f900h
 jne failed
 cmp word [{D1('RET_AX')}],1234h
 jne failed
 cmp word [{D2('MS2_RET_AX')}],5678h
 jne failed
'''
   for i,name in enumerate(frame):body+=f'cmp word [{D(prefix+name)}],{0x100+i}\njne failed\n'
   near(code,C1('CHECK_ERROR'),body)
 print('PASS: DOS 1.x/2.x INT24 frames, register/stack restoration, ignore/retry/abort, retry beyond ten failures')
 # Test cleanup against real state-changing routines; no INT21 recursion.
 for owners in [0,1,2]:
  code=bytearray(base)
  hook(code,C2('GET_PD'),'push ds\npop es\nmov bx,0e000h\nret')
  worker=len(code);code+=asm(f'''org {worker}
 call {C2('SWAP_PDRIVE')}
 mov bx,0bad0h
 call {C1('CRITICAL_CLEANUP')}
 call {C1('CRITICAL_CLEANUP')}
 ret''')
  near(code,worker,f'''mov word [0e02eh],{0xe100 if owners else 0}
 mov word [0e120h],{owners}
 mov word [0e11eh],1111h
 mov bx,0e300h
 mov word [bx+{s2['HCB_PATH_PTR']}],2222h
 mov byte [{D2('PDRIVE_STATE')}],1
 mov byte [{D2('DTA_STATE')}],2
 mov word [{D2('SAVE_DTA_OFF')}],3333h
 mov word [{D2('SAVE_DTA_SEG')}],4444h
 mov word [{D1('MS_DMAADR')}],5555h
 mov word [{D1('MS_DMABASE')}],6666h
 mov ax,7777h
 call far [cs:target]
 cmp ax,7777h
 jne failed
 cmp bx,0bad0h
 jne failed
 cmp word [0e11eh],1111h
 jne failed
 cmp word [0e300h+{s2['HCB_PATH_PTR']}],2222h
 jne failed
 cmp byte [{D2('PDRIVE_STATE')}],1
 jne failed
 cmp byte [{D2('DTA_STATE')}],1
 jne failed
 cmp word [{D1('MS_DMAADR')}],3333h
 jne failed
 cmp word [{D1('MS_DMABASE')}],4444h
 jne failed
''')
 print('PASS: temporary DTA/P: cleanup, missing/shared CAT, saved HCB despite handler BX changes, repeated cleanup')
if __name__=='__main__':check()
