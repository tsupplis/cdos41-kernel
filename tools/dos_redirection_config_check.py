#!/usr/bin/env python3
"""Run private stream validation with distinct code/data segments."""
from pctmp_recovery_check import RSP,syms,bases,near
from fat_recovery_check import hook


def check():
    raw=(RSP/'pctmp.rsp').read_bytes()
    base=bytearray(raw[128:128+int.from_bytes(raw[1:3],'little')*16])
    s=syms('ms2');c,d=bases('ms2');s1=syms('ms1');_,d1=bases('ms1')
    C=lambda n:c+s[n]
    D=lambda n:d+s[n]
    for flags,same,owner,error in [(0,False,0,0),(1,False,0,0),(2,False,0,0),
                                    (3,False,0,0),(3,True,0,13),(32,False,0,13),
                                    (3,False,0x4567,5)]:
        code=bytearray(base)
        hook(code,C('GET_PD'),'mov bx,1234h\npush ds\npop es\nret')
        # Native BDOS may alter ES/DI. Configuration must preserve its packet.
        hook(code,C('CCPM'),'mov ax,0\nmov di,0ffffh\nmov es,ax\nret')
        body=f'''mov ax,ds
 add ax,1000h
 mov ds,ax
 mov es,ax
 mov word [{d1+s1['CLI_DS']}],ds
 mov word [{D('REDIR_OWNER')}],{owner}
 mov word [{D('REDIR_PENDING_FLAGS')}],0
 mov word [0f000h],1
 mov word [0f002h],{flags}
 mov word [0f004h],0f100h
 mov word [0f006h],ds
 mov word [0f008h],{0xf100 if same else 0xf140}
 mov word [0f00ah],ds
 mov byte [0f100h],2
 mov byte [0f140h],2
 mov word [0f101h],'ST'
 mov word [0f103h],'RE'
 mov word [0f105h],'AM'
 mov word [0f107h],'  '
 mov word [0f109h],'IN'
 mov byte [0f10bh],' '
 mov word [0f141h],'ST'
 mov word [0f143h],'RE'
 mov word [0f145h],'AM'
 mov word [0f147h],'  '
 mov word [0f149h],'OU'
 mov byte [0f14bh],'T'
 mov dx,0f000h
 call far [cs:target]
 cmp ax,{error}
 jne failed
 cmp word [{D('REDIR_PENDING_FLAGS')}],{0 if error else flags}
 jne failed
'''
        near(code,C('MS2_REDIR_CONFIG'),body)
    print('PASS: separate-segment stream packets: input/output/dual, same-file rejection, reserved flags and caller ownership')


if __name__=='__main__':
    check()
