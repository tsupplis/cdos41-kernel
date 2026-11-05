#!/usr/bin/env python3
"""Annotated, lossless first-pass listing; not an assembler-equivalence check.

Uses NDISASM only as a decoder, following direct control flow. Unvisited bytes
are explicitly unclassified, never presented as proven data or fake code.
"""
from pathlib import Path
import hashlib, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parent
META=json.loads((ROOT/'symbols.json').read_text())
ROW=re.compile(r'^([0-9A-F]{8})  ([0-9A-F]+)\s+(.+)$')
REF=ROOT/'../../extra/fm.cmd'
OUTPUT=ROOT/'fmorg.dis'

def generate():
    binary=REF.read_bytes()
    assert hashlib.sha256(binary).hexdigest()==META['sha256'],'FM reference changed'
    size=int.from_bytes(binary[1:3],'little')*16
    dsize=int.from_bytes(binary[10:12],'little')*16
    assert len(binary)==128+size+dsize+48
    code=binary[128:128+size]; data=binary[128+size:128+size+dsize]
    funcs={int(a,16):n for a,n in META['functions'].items()}
    for table in META.get('dispatch_tables',[]):
        base=int(table['data_offset'],16)
        for offset,target in table['entries'].items():
            pos=base+int(offset,16)
            assert int.from_bytes(data[pos:pos+2],'little')==int(target,16), 'Dispatch table changed'
            assert int(target,16) in funcs

    cache={}; ins={}; occupied={}; pending=list(funcs); edges=[]; indirect=[]
    def decode(a):
        if a not in cache:
            result=subprocess.run(['ndisasm','-b','16','-o',str(a),'-'],input=code[a:a+256],capture_output=True,check=True)
            for line in result.stdout.decode().splitlines():
                m=ROW.match(line)
                if m and (int(m[1],16)<a+240 or a+256>=size): cache.setdefault(int(m[1],16),(bytes.fromhex(m[2]),m[3]))
        return cache[a]
    while pending:
        a=pending.pop()
        while 0<=a<size and a not in ins:
            assert a not in occupied, 'Conflicting instruction at '+hex(a)
            raw,asm=decode(a)
            assert not asm.startswith('db '), 'Undecoded reachable instruction '+hex(a)
            assert code[a:a+len(raw)]==raw
            assert all(i not in occupied for i in range(a,a+len(raw)))
            ins[a]=(raw,asm)
            for i in range(a,a+len(raw)): occupied[i]=a
            m=re.fullmatch(r'(j\w+|call|loop\w*) (?:short )?0x([0-9a-f]+)',asm)
            if m:
                target=int(m[2],16)
                if target<size: pending.append(target);edges.append((a,target))
            elif asm.startswith(('call ','jmp ')): indirect.append((a,asm))
            a+=len(raw)
            if asm.startswith(('ret','iret','jmp ','hlt')) or asm == 'call 0x26':break
    labels=dict(funcs)
    for a,b in edges:
        assert b in ins
        labels.setdefault(b,'code_%04x'%b)
    out=['; FM — Concurrent DOS file manager reference',
         '; First-pass control-flow disassembly, NOT ASM86 source.',
         '; Byte columns preserve the complete CMD, including header and padding.',
         '; Unclassified CODE ranges may contain indirect functions or inline data.',
         '; Only named functions in symbols.json have analyst-assigned meanings.',
         '; make check-ref checks byte coverage and direct branch boundaries.']
    def row(a,b,s):out.append('%08X  %-32s %s'%(a,b.hex().upper(),s))
    def blob(a,b,title):
        out.append('\n; '+title)
        for i in range(0,len(b),16):
            part=b[i:i+16]; visible=''.join(chr(v) if 32<=v<127 else '.' for v in part)
            row(a+i,part,'bytes ; '+visible)
    blob(0,binary[:128],'CMD header')
    a=0;unknown=0
    while a<size:
        if a in ins:
            raw,asm=ins[a]
            if a in labels:
                out.append('')
                if '%04x'%a in META['notes']: out.append('; '+META['notes']['%04x'%a])
                out.append(labels[a]+':')
            m=re.fullmatch(r'(j\w+|call|loop\w*) (?:short )?0x([0-9a-f]+)',asm)
            if m and int(m[2],16) in labels:asm=m[1]+' '+labels[int(m[2],16)]
            row(128+a,raw,asm);a+=len(raw)
        else:
            end=a+1
            while end<size and end not in ins:end+=1
            blob(128+a,code[a:end],'UNCLASSIFIED CODE %04X..%04X'%(a,end-1))
            unknown+=end-a;a=end
    blob(128+size,data,'DATA group; first 256 bytes are loader base page')
    blob(128+size+dsize,binary[128+size+dsize:],'CMD record padding')
    out.append('\n; Unresolved indirect control transfers:')
    out.extend('; CODE %04X: %s'%p for p in indirect)
    stats={'instructions':len(ins),'decoded_code_bytes':size-unknown,'unclassified_code_bytes':unknown,'indirect_transfers':len(indirect)}
    return '\n'.join(out)+'\n',binary,stats

def check(text,binary):
    recovered=bytearray()
    for line in text.splitlines():
        m=ROW.match(line)
        if m:
            assert int(m[1],16)==len(recovered),'Missing/overlapping byte coverage'
            recovered.extend(bytes.fromhex(m[2]))
    assert recovered==binary,'Reference bytes differ'

if __name__=='__main__':
    text,binary,stats=generate();check(text,binary)
    if '--check' in sys.argv:
        assert OUTPUT.read_text()==text,'Listing stale'
        check(OUTPUT.read_text(),binary)
    else: OUTPUT.write_text(text)
    print('PASS: complete %d-byte reference coverage; %s'%(len(binary),stats))
