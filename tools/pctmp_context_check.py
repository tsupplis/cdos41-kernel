#!/usr/bin/env python3
"""Exercise assembled DOS FCB directory preservation; BDOS I/O is stubbed."""
from pctmp_recovery_check import RSP,syms,bases,near
from fat_recovery_check import hook

def check():
 b=(RSP/'pctmp.rsp').read_bytes();base=bytearray(b[128:128+int.from_bytes(b[1:3],'little')*16])
 s1,s2=syms('ms1'),syms('ms2');c1,d1=bases('ms1');c2,d2=bases('ms2')
 C1=lambda n:c1+s1[n];D1=lambda n:d1+s1[n]
 C2=lambda n:c2+s2[n]
 # Use a synthetic system-data segment at the payload's segment, with CAT
 # and HDS outside the loaded code. This stubs only process lookup, leaving
 # the recovered CAT/HDS traversal and context exchange intact.
 def setup():
  code=bytearray(base)
  hook(code,C2('GET_PD'),'push ds\npop es\nmov bx,0e000h\nret')
  return code
 initial='''mov word [0e02eh],0e100h
 mov word [0e104h],0e200h
 mov word [0e206h],1234h
 mov bx,5678h
 mov cx,0ab02h
'''
 count=0
 for cat,hds in [(0,0),(0xe100,0),(0xe100,0xe200)]:
  for value in [0xffff,0,0x4567]:
   code=setup()
   near(code,C2('SET_FCB_DIRECTORY'),initial+f'''mov word [0e02eh],{cat}
 mov word [0e104h],{hds}
 mov ax,{value}
 mov [0f030h],sp
 mov [0f032h],es
 call far [cs:target]
 cmp sp,[0f030h]
 jne failed
 mov dx,es
 cmp dx,[0f032h]
 jne failed
 cmp bx,5678h
 jne failed
 cmp word [0e206h],{value if cat and hds and value!=0xffff else 0x1234}
 jne failed
 cmp ax,{(0x1234 if value==0xffff else value) if cat and hds else 0}
 jne failed
''');count+=1
 code=setup()
 near(code,C1('SAVE_FCB_DIRECTORY'),initial+'''mov di,0e300h
 mov byte [di],3
 mov word [di+1ah],0aaaah
 mov word [di+1ch],0
 mov word [di+1eh],0bbbbh
 call far [cs:target]
 cmp word [di+1ch],1234h
 jne failed
 cmp word [di+1ah],0aaaah
 jne failed
 cmp word [di+1eh],0bbbbh
 jne failed
''')
 # Exercise the actual close decision and its common exit, including errors
 # before/after BDOS close. Stubs record which directory disk I/O observes.
 for written in [0,255]:
  for failure in [False,True]:
   for saved in [0,0x4567,0xffff]:
    code=setup()
    hook(code,C1('CHECK_FILE_DEVICE'),'xor ax,ax\nret')
    hook(code,C1('FIND_FCB'),'xor ax,ax\nret')
    hook(code,C1('RDDIV128'),'xor cx,cx\nret')
    hook(code,C1('CLOSE_FILE'),f'''mov ax,[0e206h]
 mov [0f000h],ax
 mov al,{255 if failure else 0}
 ret''')
    hook(code,C1('CHECK_ERROR'),'ret')
    hook(code,C1('KILL_FCB'),'''mov ax,[0e206h]
 mov [0f002h],ax
 ret''')
    near(code,C1('MS_CLOSE2'),initial+f'''mov di,0e300h
 mov si,di
 mov byte [di],3
 mov word [di+1ch],{saved}
 mov word [di+10h],0
 mov word [di+12h],0
 mov word [{D1('MS_FCB')}],di
 mov [{D1('MS_FCB')+2}],es
 mov word [{D1('CPM_FCB')}],0e400h
 mov byte [0e400h],3
 mov byte [0e400h+{s1['CPM_WRITTEN']}],{written}
 mov word [{D1('BUFFER_FCB')}],0
 mov word [0f000h],0ffffh
 mov word [0f002h],0ffffh
 mov [0f030h],sp
 call far [cs:target]
 cmp sp,[0f030h]
 jne failed
 cmp word [0f000h],{0x1234 if saved==0xffff else saved}
 jne failed
 cmp word [0f002h],1234h
 jne failed
 cmp word [0e206h],1234h
 jne failed
 cmp byte [{D1('RET_AL')}],{255 if failure else 0}
 jne failed
''');count+=1
 print(f'PASS: FCB opening-directory capture and {count} HDS/close cases (missing CAT/HDS, root/subdirectory, rename sentinel, written/unwritten, success/error, balanced stack)')
if __name__=='__main__':check()
