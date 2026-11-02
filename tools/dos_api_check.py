#!/usr/bin/env python3
"""Execute local DOS services and XIOS verification with synthetic devices."""
from pctmp_recovery_check import RSP, syms, bases, near
from fat_recovery_check import hook, separate_near
from historical_check import symbols, payload


def check():
    binary = (RSP / 'pctmp.rsp').read_bytes()
    original = bytearray(binary[128:128 + int.from_bytes(binary[1:3], 'little') * 16])
    names = syms('ms2')
    code_base, data_base = bases('ms2')
    code1, data1 = bases('ms1')
    names1 = syms('ms1')
    c = lambda name: code_base + names[name]
    d = lambda name: data_base + names[name]
    c1 = lambda name: code1 + names1[name]
    d1 = lambda name: data1 + names1[name]
    frame = f'''mov word [{d('MS2_SP')}],0f800h
 mov word [{d('MS2_SS')}],ds
 mov word [0f804h],0
'''
    count = 0
    for kind in ['disk', 'CON', 'NUL', 'AUX', 'COM1', 'LPT1']:
        for function in [0, 6, 7, 255]:
            for ready in [False, True]:
                code = bytearray(original)
                for entry in [c1('GETSTAT'), c1('PRINTER_READY'), c('CCPM')]:
                    hook(code, entry, f'mov al,{255 if ready else 0}\nor al,al\nret')
                flags = 3 if kind == 'disk' else 7
                position = 0 if ready else 1
                body = frame + f'''mov word [{d('MS2_BX')}],5
 mov word [{d('MS2_AX')}],{0x4400+function}
 mov word [{d('HCB_LIST')+10}],0f000h
 mov byte [0f000h],{flags}
 mov word [0f004h],0f100h
 mov word [0f110h],1
 mov word [0f112h],0
 mov word [0f121h],{position}
 mov word [0f123h],0
 mov byte [0f100h],2
'''
                body += 'mov byte [0f104h],32\n'  # parsed FCB names are space padded
                for i, byte in enumerate(kind.encode()):
                    body += f'mov byte [{0xf101+i}],{byte}\n'
                body += 'call far [cs:target]\n'
                if function == 255:
                    body += f'cmp word [{d("MS2_RET_AX")}],1\njne failed\ncmp word [0f804h],1\njne failed\n'
                elif function == 0:
                    status = 0x41 if kind == 'disk' else 0x80d3 if kind == 'CON' else 0x80c4 if kind == 'NUL' else 0x80c0
                    body += f'cmp word [{d("MS2_DX")}],{status}\njne failed\n'
                else:
                    expected = ready
                    if kind == 'disk' and function == 7 or kind == 'NUL' or kind == 'CON' and function == 7:
                        expected = True
                    if kind == 'LPT1' and function == 6:
                        expected = False
                    body += f'cmp word [{d("MS2_RET_AX")}],{255 if expected else 0}\njne failed\n'
                near(code, c('MS2_IO_CTRL'), body)
                count += 1
    print(f'PASS: {count} IOCTL cases covering file/CON/NUL/AUX/printer, EOF, readiness and unsupported selectors')
    for error, classification, locus in [(0,0,0),(1,0x704,1),(2,0x803,2),(3,0x803,2),(5,0x303,2),(6,0x704,1),(8,0x104,5),(15,0x803,2),(18,0x803,2),(21,0x502,2),(23,0xb01,2)]:
        near(original, c('MS2_EXTENDED_ERROR'), frame + f'''mov word [{d('MS2_BX')}],0
 mov word [{d('DOS_ERROR_CODE')}],{error}
 call far [cs:target]
 cmp word [{d('MS2_RET_AX')}],{error}
 jne failed
 cmp word [{d('MS2_BX')}],{classification}
 jne failed
 cmp byte [{d('MS2_CX')+1}],{locus}
 jne failed
 cmp word [{d('DOS_ERROR_CODE')}],{error}
 jne failed
''')
    print('PASS: extended-error code/class/action/locus and persistent query state (11 cases)')
    for state in [0,1]:
        for char in [0,3,65,0x4800]:
            code = bytearray(original)
            hook(code, c1('GETSTAT'), f'mov ax,{char}\nor ax,ax\nret')
            hook(code, c1('CONIN'), f'mov ax,{char}\nret')
            hook(code, c1('BDOS'), 'ret')
            near(code, c1('EXTENDED_BREAK_POLL'), f'''mov byte [{d1('EXT_CHAR')}],{255 if state else 0}
 mov word [{d1('ROS_CHAR')}],0
 call far [cs:target]
 mov ax,0
 adc ax,0
 cmp ax,{int(not state and char==3)}
 jne failed
''')
    print('PASS: Ctrl-C polling, no input, ordinary input and pending extended-key tails (8 cases)')
    for failure in ['none','partial','flush']:
        code = bytearray(original)
        hook(code, c('SWAP_PDRIVE'), 'inc byte [0f020h]\nret')
        hook(code, c1('MS_COMMIT'), f'mov al,{255 if failure=="partial" else 0}\nret')
        hook(code, c('CCPM'), f'mov al,{255 if failure=="flush" else 0}\nret')
        near(code, c('MS2_COMMIT'), frame + f'''mov word [{d('MS2_BX')}],5
 mov word [{d('HCB_LIST')+10}],0f000h
 mov byte [0f000h],3
 mov word [0f004h],0f100h
 mov byte [0f020h],0
 call far [cs:target]
 cmp byte [0f020h],2
 jne failed
 cmp word [{d('HCB_LIST')+10}],0f000h
 jne failed
 cmp word [0f804h],{int(failure!='none')}
 jne failed
''')
    print('PASS: commit retains handle and restores directory context on partial-close/flush success and failure')
    xnames = symbols('squid')
    for configured in [0,1]:
        for forced in [0,1]:
            code = payload('xios')
            hook(code, xnames['FLPIO'], 'inc byte [0f000h]\nxor ax,ax\nret')
            separate_near(code, xnames['WRITEFLOP'], f'''mov byte [{xnames['VERIFYFLAG']}],{configured}
 mov byte [{xnames['FORCEWRITEVERIFY']}],{forced}
 mov byte [0f000h],0
 call far [cs:target]
 cmp byte [0f000h],{2 if configured or forced else 1}
 jne failed
''')
    print('PASS: floppy write verification runs for configured or DOS policy, and skips only when both are off')

    for configured in [0, 1]:
        for forced in [0, 1]:
            for mismatch in [False, True]:
                code = payload('xios')
                for name, source in {
                    'HDXLATEREQUEST': 'ret',
                    'HDDMACHECK': 'clc\nret',
                    'HDDMAIO': 'xor ax,ax\nret',
                    'HDLOCALIO': 'inc byte [0f000h]\nxor ax,ax\nret',
                    'HDERRORHANDLER': 'inc byte [0f001h]\nmov al,1\nret',
                }.items():
                    hook(code, xnames[name], source)
                active = bool(configured or forced)
                separate_near(code, xnames['HDWRITE'], f'''mov si,0f100h
 mov word [si+{xnames['HDINFLABELOFS']}],0f200h
 mov byte [0f200h+{xnames['HDLBCPMOPTIONS']}],{configured}
 mov byte [{xnames['FORCEWRITEVERIFY']}],{forced}
 mov word [{xnames['BLOCKBYTECNT']}],1
 mov word [{xnames['AUXLONGWORD']}],0f500h
 mov word [{xnames['AUXLONGWORD']+2}],ds
 mov byte [0f500h],0
 mov byte [{xnames['HDLOCALBUF']}],{int(mismatch)}
 mov word [0f000h],0
 call far [cs:target]
 cmp byte [0f000h],{int(active)}
 jne failed
 cmp byte [0f001h],{int(active and mismatch)}
 jne failed
''')
    print('PASS: hard-disk read-back verification, configured/DOS policies and data-mismatch error delivery (8 cases)')

if __name__ == '__main__':
    check()
