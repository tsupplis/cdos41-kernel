#!/usr/bin/env python3
"""Generate/check an annotated reference listing, not an assembler rebuild.

NDISASM is used only as an instruction decoder. Inline strings/padding are
classified explicitly. The byte column preserves the complete CMD container.
"""
from pathlib import Path
import bisect, hashlib, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parent
META=json.loads((ROOT/'symbols.json').read_text())
ORIGINAL=ROOT/'reference/chkdsk.cmd'
OUTPUT=ROOT/'chkdosorg.dis'
ROW=re.compile(r'^([0-9A-F]{8})  ([0-9A-F]+)\s+(.+)$')

def generate():
    binary=ORIGINAL.read_bytes()
    assert hashlib.sha256(binary).hexdigest()==META['sha256'], 'Reference changed'
    size=int.from_bytes(binary[1:3],'little')*16
    data_size=int.from_bytes(binary[10:12],'little')*16
    assert size==9152 and data_size==2464
    code=binary[128:128+size]; data=binary[128+size:128+size+data_size]
    funcs={int(a,16):n for a,n in META['functions'].items()}
    globals_={int(a,16):n for a,n in META['globals'].items()}
    inline=[(int(a,16),int(b,16),n) for a,b,n in META['inline_data']]
    cuts=sorted({0,size,*[a for a,b,n in inline],*[b for a,b,n in inline]})
    instructions={}
    for start,end in zip(cuts,cuts[1:]):
        if any(start>=a and end<=b for a,b,n in inline):continue
        decoded=subprocess.run(['ndisasm','-b','16','-o',str(start),'-'],input=code[start:end],capture_output=True,check=True).stdout.decode()
        for line in decoded.splitlines():
            m=ROW.match(line);assert m,line
            address=int(m[1],16);raw=bytes.fromhex(m[2]);asm=m[3]
            assert code[address:address+len(raw)]==raw
            assert not asm.startswith('db '), 'Undecoded instruction at '+hex(address)
            instructions[address]=(raw,asm)
    labels=dict(funcs);targets=set()
    for raw,asm in instructions.values():
        m=re.fullmatch(r'(?:j\w+|call|loop\w*) 0x([0-9a-f]+)',asm)
        if m:targets.add(int(m[1],16))
    assert targets<=instructions.keys(), 'Branch into data/mid-instruction: '+str(targets-instructions.keys())
    assert funcs.keys()<=instructions.keys(), 'Invalid function boundary'
    starts=sorted(funcs)
    for target in sorted(targets-funcs.keys()):
        owner=funcs[starts[bisect.bisect_right(starts,target)-1]]
        labels[target]=owner+'_at_'+f'{target:04x}'
    out=['; CHKDOSFS — DOS Plus / Concurrent DOS CHKDSK reference disassembly',
         '; Original: CHKDSK 1.0, 20-Mar-86, Digital Research; preserved without modification.',
         '; First-pass analysis for a C recreation. This file is NOT assembler input.',
         '; Columns: CMD file offset, original bytes, decoded instruction/data.',
         '; CODE labels use segment-relative addresses; DATA references are near DS offsets.',
         '; Semantic names are analyst-assigned. Local *_at_ labels retain traceability.',
         '; make check verifies complete byte coverage and direct branch boundaries,',
         '; NOT assembler equivalence or functional correctness. No CMD is built yet.',
         '; SHA256 '+META['sha256'],'']
    def row(offset,raw,text):out.append(f'{offset:08X}  {raw.hex().upper():<20}  {text}')
    def blob(offset,raw,name):
        out.extend(['',name+':'])
        # Keep printable runs whole; numeric bytes are data, never disguised code.
        pos=0
        while pos<len(raw):
            m=re.match(rb'[\x20-\x7e]{4,}',raw[pos:])
            if m:
                chunk=m[0];row(offset+pos,chunk,'db '+repr(chunk.decode('ascii')));pos+=len(chunk)
            else:
                end=pos+1
                while end<min(len(raw),pos+16) and not re.match(rb'[\x20-\x7e]{4,}',raw[end:]):end+=1
                chunk=raw[pos:end];row(offset+pos,chunk,'db '+','.join(f'{v:02x}h' for v in chunk));pos=end
    blob(0,binary[:128],'cmd_header')
    out.extend(['','; CODE group: 9152 stored bytes.'])
    pos=0
    ranges={a:(b,n) for a,b,n in inline}
    while pos<size:
        if pos in ranges:
            end,name=ranges[pos];blob(128+pos,code[pos:end],name);pos=end;continue
        raw,asm=instructions[pos]
        if pos in labels:
            if pos in funcs:
                out.extend(['','; '+ '-'*72,'; '+funcs[pos]+f' (CODE {pos:04X}h)'])
                note=META['notes'].get(f'{pos:04x}')
                if note:out.append('; '+note)
            out.append(labels[pos]+':')
        m=re.fullmatch(r'(j\w+|call|loop\w*) 0x([0-9a-f]+)',asm)
        if m:asm=m[1]+' '+labels[int(m[2],16)]
        comments=[]
        for m in re.finditer(r'\[0x([0-9a-f]+)\]',asm):
            a=int(m[1],16)
            if a in globals_:comments.append(globals_[a])
        m=re.fullmatch(r'mov (?:ax|dx),0x([0-9a-f]+)',asm)
        if m:
            a=int(m[1],16)
            if 0x106<=a<len(data):
                msg=data[a:].split(b'\0')[0]
                if len(msg)>=4 and all(v in (10,13) or 32<=v<127 for v in msg):comments.append('DATA '+repr(msg.decode('ascii')))
        if comments:asm+=' ; '+'; '.join(comments)
        row(128+pos,raw,asm);pos+=len(raw)
    out.extend(['','; DATA group: 2464 stored bytes. Base page occupies offsets 0000h..00FFh.'])
    boundaries=sorted({0,len(data),*globals_})
    for start,end in zip(boundaries,boundaries[1:]):
        blob(128+size+start,data[start:end],globals_.get(start,'data_'+f'{start:04x}'))
    if 128+size+data_size<len(binary):blob(128+size+data_size,binary[128+size+data_size:],'file_padding')
    return '\n'.join(out)+'\n',binary,len(instructions),len(targets)

def check(text,binary):
    recovered=bytearray()
    for line in text.splitlines():
        m=ROW.match(line)
        if not m:continue
        assert int(m[1],16)==len(recovered),'Missing/overlapping bytes at '+m[1]
        recovered.extend(bytes.fromhex(m[2]))
    assert recovered==binary,'Listing does not reproduce the original byte column'

text,binary,n,t=generate()
check(text,binary)
if '--check' in sys.argv:
    assert OUTPUT.read_text()==text,'Stale reference listing: run make'
    check(OUTPUT.read_text(),binary)
else:OUTPUT.write_text(text)
print(f'PASS: {len(binary)} original bytes covered; {n} instructions; {t} direct branch targets on instruction boundaries')
