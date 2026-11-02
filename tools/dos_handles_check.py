#!/usr/bin/env python3
"""Run assembled DOS handle ownership, duplication and PSP table routines."""
from pctmp_recovery_check import RSP, syms, bases, near
from fat_recovery_check import hook


def check():
    binary = (RSP / 'pctmp.rsp').read_bytes()
    original = bytearray(binary[128:128+int.from_bytes(binary[1:3], 'little')*16])
    names = syms('ms2')
    cb, db = bases('ms2')
    c = lambda n: cb + names[n]
    d = lambda n: db + names[n]
    frame = f'''mov word [{d('MS2_SP')}],0f800h
 mov word [{d('MS2_SS')}],ds
 mov word [0f804h],0
 mov word [{d('DOS_CRITICAL_CODE')}],0
'''
    for target in [0,1,2,5,19,20,0x7fff,0xffff]:
        for mode in ['empty','device','same','file','failed-close']:
            code = bytearray(original)
            hook(code, c('SWAP_PDRIVE'), 'inc byte [0f010h]\nret')
            hook(code, c('CLOSE_FCB'), 'inc byte [0f011h]\nmov al,5\n' + ('stc' if mode=='failed-close' else 'clc') + '\nret')
            source, other = 0xf100, 0xf200
            old = 0 if mode=='empty' else source if mode=='same' else other
            count = 2 if target==5 or mode=='same' else 1
            failed = target>=20 or mode=='failed-close' and target!=5
            body = frame + f'''mov word [{d('MS2_BX')}],5
 mov word [{d('MS2_CX')}],{target}
 mov word [{d('HCB_LIST')+10}],{source}
 mov byte [{source}],3
 mov byte [{source+1}],{count}
 mov byte [{other}],{7 if mode=='device' else 3}
 mov byte [{other+1}],1
 mov word [0f010h],0
'''
            if target<20 and target!=5:
                body += f'mov word [{d("HCB_LIST")+2*target}],{old}\n'
            body += f'''call far [cs:target]
 cmp word [0f804h],{int(failed)}
 jne failed
 cmp byte [{source+1}],{count if failed or mode=='same' or target==5 else count+1}
 jne failed
'''
            if target<20:
                expected = source if not failed or target==5 else old
                body += f'cmp word [{d("HCB_LIST")+2*target}],{expected}\njne failed\n'
            near(code, c('MS2_FORCE_DUP'), body)
    print('PASS: 40 forced-duplication cases: standard handles, alias/self, file/device targets, failed close and bounds')
    # Overflow preflight considers repeated aliases to the same HCB.
    for count, aliases in [(1,1),(253,2),(254,2),(255,1)]:
        address = d('HCB5')
        body = f'''mov di,{d('HCB_LIST')}
 mov cx,20
 xor ax,ax
 rep stosw
 mov byte [{address+1}],{count}
'''
        for i in range(aliases):
            body += f'mov word [{d("HCB_LIST")+2*i}],{address}\n'
        body += f'''call far [cs:target]
 mov ax,0
 adc ax,0
 cmp ax,{int(count+aliases>255)}
 jne failed
 cmp byte [{address+1}],{count}
 jne failed
'''
        near(original, c('CHECK_HANDLE_INHERITANCE'), body)
    print('PASS: inheritance preflight accepts the byte-count boundary and rejects overflow without mutation')
    # Saving the parent adds references per slot, including redirected stdout.
    body = f'''mov di,{d('HCB_LIST')}
 mov cx,20
 xor ax,ax
 rep stosw
 mov word [{d('PARENTS_PSP')}],ds
 mov ax,ds
 add ax,1000h
 mov word [{d('NEW_PSP')}],ax
 mov word [{d('HCB_LIST')+2}],{d('HCB5')}
 mov word [{d('HCB_LIST')+10}],{d('HCB5')}
 mov byte [{d('HCB5')+1}],2
 call far [cs:target]
 cmp byte [{d('HCB5')+1}],4
 jne failed
 cmp byte [19h],5
 jne failed
 cmp byte [1dh],5
 jne failed
 mov es,[{d('NEW_PSP')}]
 cmp byte [es:19h],5
 jne failed
'''
    near(original, c('INHERIT_HANDLES'), body)
    print('PASS: parent/child PSP tables and ownership for two aliases to redirected stdout')

    for failure in [False, True]:
        code = bytearray(original)
        hook(code, c('SWAP_PDRIVE'), 'ret')
        hook(code, c('CLOSE_FCB'), 'inc byte [0f010h]\nmov al,5\n' + ('stc' if failure else 'clc') + '\nret')
        body = f'''mov di,{d('HCB_LIST')}
 mov cx,20
 xor ax,ax
 rep stosw
 mov word [{d('HCB_LIST')}],0f100h
 mov word [{d('HCB_LIST')+2}],0f100h
 mov word [{d('HCB_LIST')+4}],0f200h
 mov word [{d('HCB_LIST')+10}],0f300h
 mov word [0f100h],0203h
 mov word [0f200h],0107h
 mov word [0f300h],0103h
 mov byte [0f010h],0
 mov word [{d('DOS_ERROR_CODE')}],0
 call far [cs:target]
 cmp byte [0f010h],2
 jne failed
 cmp byte [0f101h],0
 jne failed
 cmp byte [0f201h],0
 jne failed
 cmp byte [0f301h],0
 jne failed
 cmp word [{d('DOS_ERROR_CODE')}],{5 if failure else 0}
 jne failed
 mov si,{d('HCB_LIST')}
 mov cx,20
all_closed:
 lodsw
 test ax,ax
 jnz failed
 loop all_closed
'''
        near(code, c('MS2_CLOSE_HANDLES'), body)
    print('PASS: all-handle termination cleanup includes standard aliases and continues after failed closes')
    names1 = syms('ms1')
    c1, d1 = bases('ms1')
    for size in [0, 4, 127, 128, 129, 65536]:
        for start in sorted({0, max(0,size-1), size}):
            for requested in [1,2,5]:
                last = start + requested - 1
                expected = 1 if start>=size else 3 if start+requested>size else 0
                body = f'''mov word [{d1+names1['MS_FCB_PTR']}],0f100h
 mov word [{d1+names1['MS_FCB_PTR']+2}],ds
 mov word [0f110h],{size&65535}
 mov word [0f112h],{size>>16}
 mov word [{d1+names1['START_BYTE_LO']}],{start&65535}
 mov word [{d1+names1['START_BYTE_HI']}],{start>>16}
 mov word [{d1+names1['END_BYTE_LO']}],{last&65535}
 mov word [{d1+names1['END_BYTE_HI']}],{last>>16}
 mov word [{d1+names1['CPM_FIRST_REC_LO']}],{start//128}
 call far [cs:target]
 cmp byte [{d1+names1['RET_AL']}],{expected}
 jne failed
'''
                near(original,c1+names1['CHECK_FILE_SIZE'],body)
    print('PASS: DOS read boundaries for empty/short/record-boundary/64-KiB files, including size-plus-one requests')


if __name__ == '__main__':
    check()
