#!/usr/bin/env python3
"""Run assembled version and CON-mode routines with separate code/data."""
from pctmp_recovery_check import RSP,syms,bases
from fat_recovery_check import hook,separate_near


def check():
    raw=(RSP/'pctmp.rsp').read_bytes()
    base=bytearray(raw[128:128+int.from_bytes(raw[1:3],'little')*16])
    s=syms('ms2');c,d=bases('ms2');s1=syms('ms1');c1,d1=bases('ms1')
    C=lambda n:c+s[n]
    D=lambda n:d+s[n]
    for bx,cx in [(0,0),(0xffff,0x1234),(0x1357,0x2468)]:
        separate_near(base,C('MS2_GET_VERSION'),f'''mov word [{D('MS2_BX')}],{bx}
 mov word [{D('MS2_CX')}],{cx}
 call far [cs:target]
 cmp word [{D('MS2_RET_AX')}],2
 jne failed
 cmp word [{D('MS2_BX')}],0ff00h
 jne failed
 cmp word [{D('MS2_CX')}],0
 jne failed
''')
    print('PASS: DOS 2.0 version, generic OEM FFh and zero serial replace all caller inputs')
    for kind,flags in [('CON',5),('COM1',7),('NUL',7),('AUX',7),('disk',3)]:
        for mode in [0,0x20,0xd3,0xf3,0x120]:
            for old in [0,0x40]:
                valid=kind=='CON' and mode<256
                frame=f'''mov word [{D('MS2_SP')}],0f800h
 mov word [{D('MS2_SS')}],ds
 mov word [{D('DOS_CRITICAL_CODE')}],0
 mov word [0f804h],0
 mov word [{D('MS2_BX')}],5
 mov word [{D('MS2_AX')}],4401h
 mov word [{D('MS2_DX')}],{mode}
 mov word [{D('HCB_LIST')+10}],0f000h
 mov byte [0f000h],{flags|old}
 mov word [0f004h],0f100h
 mov byte [0f100h],0
 mov word [0f101h],2020h
 mov word [0f103h],2020h
 mov word [0f105h],2020h
 mov word [0f107h],2020h
'''
                for i,value in enumerate(kind.encode()):frame+=f'mov byte [{0xf101+i}],{value}\n'
                frame+=f'''call far [cs:target]
 cmp word [0f804h],{int(not valid)}
 jne failed
 cmp byte [0f000h],{flags|(0x40 if mode&0x20 else 0) if valid else flags|old}
 jne failed
'''
                if not valid:frame+=f'cmp word [{D("MS2_RET_AX")}],1\njne failed\n'
                separate_near(base,C('MS2_IO_CTRL'),frame)
    print('PASS: 50 CON mode set/clear, read-only flags, invalid DH/file/device and unchanged-state cases')
    for count in [0,1,7,128]:
        for writing in [False,True]:
            code=bytearray(base)
            at=c1+s1['NATIVE_RAWOUT'] if writing else c1+s1['NATIVE_CONIN']
            if writing:stub='push bx\nmov bx,[0f010h]\nmov [bx],cl\ninc bx\nmov [0f010h],bx\npop bx\nret'
            else:stub='push bx\nmov bx,[0f010h]\nmov al,[bx]\ninc bx\nmov [0f010h],bx\npop bx\nret'
            hook(code,at,stub)
            body=f'''mov word [{D('MS2_RET_AX')}],0
 mov word [{D('MS2_CX')}],{count}
 mov word [{D('MS2_DX')}],0f200h
 mov word [{D('MS2_DS')}],ds
 mov word [0f010h],0f300h
 mov bx,0f000h
 mov byte [bx],45h
 mov word [bx+4],0f100h
 mov byte [0f100h],0
 mov word [0f101h],4f43h
 mov word [0f103h],204eh
 mov byte [0f1ffh],0a5h
 mov byte [0f200h+{count}],0a5h
'''
            for i in range(count):body+=f'mov byte [{0xf200+i if writing else 0xf300+i}],{[0,3,8,13,26,254,255][i%7]}\n'
            body+=f'''call far [cs:target]
 jc failed
 cmp word [{D('MS2_RET_AX')}],{count}
 jne failed
 cmp word [0f010h],{0xf300+count}
 jne failed
 cmp byte [0f1ffh],0a5h
 jne failed
 cmp byte [0f200h+{count}],0a5h
 jne failed
'''
            for i in range(count):body+=f'cmp byte [{0xf300+i if writing else 0xf200+i}],{[0,3,8,13,26,254,255][i%7]}\njne failed\n'
            separate_near(code,C('WRITE_DEVICE' if writing else 'READ_DEVICE'),body)
    print('PASS: raw CON reads/writes, 0/1/7/128-byte transfers, control/high bytes and buffer guards')
    # Entry uses BX supplied by the application before MS2 has saved a frame.
    for number,raw_mode,device,name in [(0,1,1,'CON '),(5,1,1,'CON '),(19,1,1,'CON '),(20,1,1,'CON '),
                                      (0xffff,1,1,'CON '),(0,0,1,'CON '),(0,1,0,'CON '),(0,1,1,'COM1')]:
        wanted=number<20 and raw_mode and device and name=='CON '
        body=f'''mov bx,{number}
 mov si,0f123h
 mov byte [0f000h],{1+4*device+0x40*raw_mode}
 mov word [0f004h],0f100h
'''
        if number<20:body+=f'mov word [{D("HCB_LIST")+2*number}],0f000h\n'
        for i,value in enumerate(name.encode()):body+=f'mov byte [{0xf101+i}],{value}\n'
        body+=f'''call far [cs:target]
 mov ax,0
 adc ax,0
 cmp ax,{int(wanted)}
 jne failed
 cmp bx,{number}
 jne failed
 cmp si,0f123h
 jne failed
'''
        separate_near(base,C('RAW_CONSOLE_HANDLE'),body)
    print('PASS: pre-dispatch BREAK bypass recognizes only a valid raw CON handle and preserves caller registers')


if __name__=='__main__':check()
