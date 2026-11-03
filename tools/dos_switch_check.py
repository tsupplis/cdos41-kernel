#!/usr/bin/env python3
"""Exercise the assembled DOS 37h handler with separate code/data segments."""
from pctmp_recovery_check import RSP,syms,bases
from fat_recovery_check import separate_near


def check():
    raw=(RSP/'pctmp.rsp').read_bytes()
    code=bytearray(raw[128:128+int.from_bytes(raw[1:3],'little')*16])
    s=syms('ms2');c,d=bases('ms2')
    C=lambda n:c+s[n]
    D=lambda n:d+s[n]
    assert int.from_bytes(code[C('MS2_FUNC_TABLE')+2*(0x37-0x2f):][:2],'little')==C('MS2_UNDOC37')
    assert raw[128+int.from_bytes(raw[1:3],'little')*16+D('SWITCH_CHARACTER')]==ord('/')
    # All byte values are valid switch characters; the saved caller frame,
    # high DX byte, AH and unrelated status are protected throughout.
    separate_near(code,C('MS2_UNDOC37'),f'''xor bx,bx
switch_value:
 mov word [{D('MS2_AX')}],3701h
 mov dx,bx
 or dx,0a500h
 mov [{D('MS2_DX')}],dx
 mov word [{D('MS2_RET_AX')}],375ah
 call far [cs:target]
 cmp word [{D('MS2_RET_AX')}],3700h
 jne failed
 cmp [{D('MS2_DX')}],dx
 jne failed
 cmp byte [{D('SWITCH_CHARACTER')}],bl
 jne failed
 mov word [{D('MS2_AX')}],3700h
 mov word [{D('MS2_DX')}],05a00h
 call far [cs:target]
 mov ax,bx
 or ax,05a00h
 cmp [{D('MS2_DX')}],ax
 jne failed
 cmp word [{D('MS2_AX')}],3700h
 jne failed
 inc bx
 cmp bx,256
 jb switch_value
''')
    for old in [ord('/'),ord('-'),255]:
        separate_near(code,C('MS2_UNDOC37'),f'''mov byte [{D('SWITCH_CHARACTER')}],{old}
 mov bx,2
invalid_selector:
 mov ax,bx
 or ax,3700h
 mov [{D('MS2_AX')}],ax
 mov word [{D('MS2_DX')}],0a55ah
 mov word [{D('MS2_RET_AX')}],375ah
 mov word [{D('DOS_ERROR_CODE')}],1234h
 mov word [{D('MS2_SS')}],ds
 mov word [{D('MS2_SP')}],0f800h
 mov word [0f804h],0a5a4h
 call far [cs:target]
 cmp word [{D('MS2_RET_AX')}],37ffh
 jne failed
 cmp word [{D('MS2_DX')}],0a55ah
 jne failed
 cmp byte [{D('SWITCH_CHARACTER')}],{old}
 jne failed
 cmp word [{D('DOS_ERROR_CODE')}],1234h
 jne failed
 cmp word [0f804h],0a5a4h
 jne failed
 inc bx
 cmp bx,256
 jb invalid_selector
''')
    # The same code accesses two independent console DATA segments.
    separate_near(code,C('MS2_UNDOC37'),f'''mov byte [{D('SWITCH_CHARACTER')}],2fh
 mov ax,ds
 add ax,1000h
 mov es,ax
 mov byte [es:{D('SWITCH_CHARACTER')}],2dh
 mov word [{D('MS2_AX')}],3701h
 mov word [{D('MS2_DX')}],2bh
 call far [cs:target]
 cmp byte [{D('SWITCH_CHARACTER')}],2bh
 jne failed
 cmp byte [es:{D('SWITCH_CHARACTER')}],2dh
 jne failed
''')
    print('PASS: DOS 37h default/dispatch, 256 switch values, 762 invalid-selector cases, saved-frame/status preservation and console DATA isolation')


if __name__=='__main__':check()
