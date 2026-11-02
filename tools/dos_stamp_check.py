#!/usr/bin/env python3
"""Exercise assembled DOS timestamp handlers with synthetic disk dependencies."""
from pctmp_recovery_check import RSP, syms, bases, near
from fat_recovery_check import hook, separate_near
from historical_check import symbols, payload

def handles():
    binary = (RSP / 'pctmp.rsp').read_bytes()
    original = bytearray(binary[128:128 + int.from_bytes(binary[1:3], 'little') * 16])
    # Load actual initialized DATA (including calendar tables) separately from code.
    data_at=128+int.from_bytes(binary[1:3],'little')*16
    initialized=binary[data_at:data_at+int.from_bytes(binary[10:12],'little')*16]
    names = syms('ms2')
    code_base, data_base = bases('ms2')
    c = lambda name: code_base + names[name]
    d = lambda name: data_base + names[name]
    names1 = syms('ms1')
    code1, _ = bases('ms1')
    cases = 0
    for fat in [False, True]:
        for failure in ['none', 'lookup', 'date', 'seconds', 'time', 'write']:
            code = bytearray(original)
            for name, source in {
                'SWAP_PDRIVE': 'inc byte [0f000h]\nret',
                'SAVE_SET_DTA': 'inc byte [0f001h]\nret',
                'RESTORE_DTA': 'inc byte [0f002h]\nret',
                'MS2_ERROR_RET': 'mov [0f003h],al\nret',
            }.items():
                hook(code, c(name), source)
            hook(code, code1 + names1['FIND_FCB_PUB'],
                 'mov si,0f200h\n' + ('stc' if failure == 'lookup' else 'clc') + '\nret')
            hook(code, code1 + names1['CHECK_ERROR'],
                 'mov byte [0f004h],1\nmov ax,' + ('255' if failure == 'write' else '0') + '\nret')
            expected = 0x747d if fat else 0x7460
            reached_write = failure in ['none', 'write']
            at=len(code)
            code+=initialized
            body = f'''
 push ds
 mov ax,ds
 sub ax,1000h
 mov ds,ax
 mov si,{at}
 xor di,di
 mov cx,{len(initialized)}
 rep movsb
 pop ds
 mov di,0f000h
 mov cx,16
 xor ax,ax
 rep stosb
 mov bx,0f100h
 mov word [bx+{names['HCB_FCB_BASE']}],0f300h
 mov word [0f210h],{0x8080 if fat else 0}
 mov word [{d('MS2_DX')}],{0 if failure == 'date' else 0x5d7c}
 mov word [{d('MS2_CX')}],{0x747f if failure == 'seconds' else 0xffff if failure == 'time' else 0x747d}
 mov word [0f300h+{names['FCB_TIME']}],1234h
 call far [cs:target]
 cmp byte [0f000h],1
 jne failed
 cmp byte [0f001h],{int(reached_write)}
 jne failed
 cmp byte [0f002h],{int(reached_write)}
 jne failed
 cmp byte [0f003h],{0 if failure == 'none' else 5}
 jne failed
 cmp byte [0f004h],{int(reached_write)}
 jne failed
 cmp word [0f300h+{names['FCB_TIME']}],{expected if failure == 'none' else 0x1234}
 jne failed
'''
            if reached_write:
                body += f'cmp word [{d("TEMP_DTA_BUF")}],3854h\njne failed\n'
                body += f'cmp word [{d("TEMP_DTA_BUF")+2}],0feddh\njne failed\n'
                if fat:
                    body += f'cmp word [{d("TEMP_DTA_BUF")+4}],747dh\njne failed\n'
                    body += f'cmp word [{d("TEMP_DTA_BUF")+6}],5d7ch\njne failed\n'
                else:
                    body += f'cmp word [{d("TEMP_DTA_BUF")+6}],3514h\njne failed\n'
            separate_near(code, c('MS2_F_SETDATE'), body)
            cases += 1
    print(f'PASS: {cases} assembled FAT/CPM handle timestamp success/error and DTA/drive restoration cases')

def cpm():
    names = symbols('pcbdos')
    for tagged in [False, True]:
        for failure in ['none', 'file', 'disabled', 'slot']:
            code = payload('bdos')
            stubs = {
                'COND_CHECK_FCB': 'ret',
                'COPY_DMA_IN_8': 'ret',
                'CHECKWRITE': 'ret',
                'SEARCH_1_NAME': 'mov ax,' + ('0' if failure == 'file' else '1') + '\nor ax,ax\nret',
                'QSTAMP': 'mov ax,' + ('1' if failure == 'disabled' else '0') + '\nor ax,ax\nret',
                'GET_DTBA': 'mov al,' + ('1' if failure == 'slot' else '0') + '\nret',
                'STAMP45': 'inc byte [0f000h]\nret',
            }
            for name, source in stubs.items():
                hook(code, names[name], source)
            body = f'''
 mov byte [{names['HIGH_EXT']}],0
 mov byte [{names['MEDIA_FORMAT']}],0
 mov byte [{names['LRET']}],0
 mov byte [0f000h],0
 mov word [{names['COMMON_DMA']}],{0x3854 if tagged else 1}
 mov word [{names['COMMON_DMA']+2}],{0xfedd if tagged else 0}
 call far [cs:target]
 cmp byte [{names['LRET']}],{255 if tagged and failure != 'none' else 0}
 jne failed
 cmp byte [0f000h],{(1 if tagged else 2) if failure == 'none' else 0}
 jne failed
'''
            separate_near(code, names['FUNC116'], body)
    print('PASS: 8 assembled CPM update-only/native request cases, missing file/stamps and disabled timestamp errors')

if __name__ == '__main__':
    handles()
    cpm()
