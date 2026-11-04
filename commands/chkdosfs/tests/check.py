#!/usr/bin/env python3
"""Exercise the production checker core against disposable FAT12/FAT16 images."""
from pathlib import Path
import hashlib, struct, subprocess, tempfile
ROOT=Path(__file__).resolve().parent.parent

def fixture(bits=12,clusters=None,spc=1):
    clusters=clusters or (700 if bits==12 else 6000)
    limit=clusters+2
    fatsiz=((limit*bits+7)//8+511)//512
    root=32; base=1; data=base+2*fatsiz+2
    total=data+clusters*spc
    assert total<65536
    b=bytearray(total*512)
    struct.pack_into('<HBHBHHBHHH',b,11,512,spc,base,2,root,total,0xf8,fatsiz,17,4)
    b[510:512]=b'\x55\xaa'
    def fat(c,v,copy=None):
        for k in range(2) if copy is None else [copy]:
            off=(base+k*fatsiz)*512+(c*bits//8)
            old=int.from_bytes(b[off:off+2],'little')
            if bits==16:new=v
            elif c&1:new=(old&15)|(v<<4)
            else:new=(old&0xf000)|(v&4095)
            b[off:off+2]=new.to_bytes(2,'little')
    end=0xfff if bits==12 else 0xffff
    fat(0,0xff8 if bits==12 else 0xfff8);fat(1,end)
    def entry(slot,name,start,size=0,attr=0,sector=None):
        off=(base+2*fatsiz if sector is None else sector)*512+slot*32
        b[off:off+11]=name.ljust(11,b' ')
        b[off+11]=attr
        struct.pack_into('<H',b,off+26,start);struct.pack_into('<I',b,off+28,size)
    return b,fat,entry,end,data

with tempfile.TemporaryDirectory(prefix='chkdosfs-') as temp:
    temp=Path(temp); exe=temp/'check'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type','-Wno-deprecated-non-prototype',
                    '-I',str(ROOT),str(ROOT/'fat.c'),str(ROOT/'check.c'),
                    str(ROOT/'tests/host.c'),'-o',str(exe)],check=True)
    count=0
    def run(name,b,status,needle,fail=None):
        global count
        image=temp/(name+'.img');image.write_bytes(b)
        before=hashlib.sha256(b).digest()
        args=[str(exe),str(image)]+([] if fail is None else [str(fail)])
        p=subprocess.run(args,capture_output=True,text=True,timeout=10)
        assert p.returncode==status,(name,p.returncode,p.stdout,p.stderr)
        assert needle in p.stdout,(name,p.stdout)
        assert hashlib.sha256(image.read_bytes()).digest()==before,name+' wrote to image'
        count+=1
    for bits in (12,16):
        b,f,e,end,data=fixture(bits)
        f(2,end);e(0,b'FILE    TXT',2,100)
        run(f'fat{bits}-clean',b,0,'Consistency errors: 0')
        f(4,end);e(1,b'SUBDIR',4,attr=16)
        f(5,end);e(0,b'CHILD   TXT',5,512,sector=data+2)
        run(f'fat{bits}-nested',b,0,'directories: 1')
        e(2,b'SHARED  TXT',2,100)
        run(f'fat{bits}-crosslink',b,1,'Cross-linked')
        e(2,b'SHARED  TXT',0,0)
        f(6,end)
        run(f'fat{bits}-lost',b,1,'Lost clusters: 1')
        f(6,0);f(2,2)
        run(f'fat{bits}-loop',b,1,'looping chain')
        f(2,end);e(0,b'FILE    TXT',2,1024)
        run(f'fat{bits}-size',b,1,'File size disagrees')
        e(0,b'FILE    TXT',2,100);f(2,0)
        run(f'fat{bits}-broken',b,1,'Broken cluster link')
        f(2,end);f(2,0,copy=1)
        run(f'fat{bits}-mirror',b,1,'FAT copies differ')
        f(2,end)
        run(f'fat{bits}-io-error',b,2,'',fail=1)
        run(f'fat{bits}-directory-io-error',b,2,'',fail=data+2)
    # Odd FAT12 entries straddling a physical sector boundary (341*3/2=511).
    b,f,e,end,data=fixture();f(341,end);e(0,b'BOUNDARYTXT',341,1)
    run('fat12-sector-boundary',b,0,'Consistency errors: 0')
    # Upper-range FAT16 cluster numbers must remain unsigned on the 16-bit target.
    b,f,e,end,data=fixture(16,64000);f(64001,end);e(0,b'HIGH    TXT',64001,512)
    run('fat16-upper-range',b,0,'Consistency errors: 0')
    b,f,e,end,data=fixture(16,6000,4);f(2,end);e(0,b'CLUSTER TXT',2,2048)
    run('fat16-multisector-cluster',b,0,'Consistency errors: 0')
    print(f'PASS: {count} FAT12/FAT16 checker cases; all images unchanged')
