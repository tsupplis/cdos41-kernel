#!/usr/bin/env python3
"""Exercise the production checker core against disposable FAT12/FAT16 images."""
from pathlib import Path
import hashlib, struct, subprocess, tempfile
ROOT=Path(__file__).resolve().parent.parent

from fixtures import fixture

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

# Repairs use the same production FAT writer and checker as the native build.
with tempfile.TemporaryDirectory(prefix='chkdosfs-repair-') as temp:
    temp=Path(temp); exe=temp/'check'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type',
                    '-Wno-deprecated-non-prototype','-I',str(ROOT),
                    str(ROOT/'fat.c'),str(ROOT/'check.c'),str(ROOT/'tests/host.c'),
                    '-o',str(exe)],check=True)
    total=0
    def repairing(name,b,expected,status=0,answer=1,failread=-1,failwrite=-1):
        global total
        image=temp/(name+'.img');image.write_bytes(b)
        p=subprocess.run([str(exe),str(image),str(failread),str(answer),str(failwrite)],
                         capture_output=True,text=True,timeout=10)
        assert p.returncode==status,(name,p.returncode,p.stdout,p.stderr)
        after=image.read_bytes()
        if expected is not None: assert after==expected,(name,'unexpected changes')
        else:
            # Injected failure may affect only the targeted primary FAT sector.
            assert after[:512]==b[:512] and after[1024:]==b[1024:],name
            assert 'Repair incomplete' in p.stdout,(name,p.stdout)
        total+=1
    for bits in (12,16):
        for cluster in (340,341):
            b,fat,entry,end,data=fixture(bits)
            entry(0,b'OWNED   TXT',339,512);fat(339,end)
            entry(1,b'NEXT    TXT',342,512);fat(342,end)
            fat(cluster,end)
            b[(data+cluster-2)*512:(data+cluster-1)*512]=bytes([0xa5])*512
            original=bytes(b)
            fat(cluster,0);expected=bytes(b)
            repairing(str(bits)+'-packed-'+str(cluster),original,expected)
            repairing(str(bits)+'-cancel-'+str(cluster),original,original,1,answer=0)
        b,fat,entry,end,data=fixture(bits)
        fat(40,41);fat(41,40);original=bytes(b)
        fat(40,0);fat(41,0)
        repairing(str(bits)+'-cycle',original,bytes(b))
        b,fat,entry,end,data=fixture(bits)
        entry(0,b'FIRST   TXT',2,512);entry(1,b'SECOND  TXT',2,512);fat(2,end);fat(40,end)
        repairing(str(bits)+'-crosslink',b,bytes(b),2)
        b,fat,entry,end,data=fixture(bits)
        fat(40,end,copy=0)
        repairing(str(bits)+'-mirror-conflict',b,bytes(b),2)
        b,fat,entry,end,data=fixture(bits)
        fat(40,end);original=bytes(b)
        repairing(str(bits)+'-read-error',original,original,2,failread=1)
        repairing(str(bits)+'-first-write-error',original,original,2,failwrite=0)
        repairing(str(bits)+'-mirror-write-error',original,None,2,failwrite=1)
        b,fat,entry,end,data=fixture(bits)
        repairing(str(bits)+'-clean',b,bytes(b))
    print('PASS: %d repair/cancellation/conflict/I/O-failure cases; exact image changes checked'%total)

    extra=total
    for bits in (12,16):
        for length,clusters in ((1,2),(1200,1),(0,2),(0x80000000,1)):
            b,fat,entry,end,data=fixture(bits)
            entry(0,b'SIZED   TXT',2,length,attr=7)
            fat(2,3 if clusters==2 else end)
            if clusters==2: fat(3,end)
            b[data*512:(data+clusters)*512]=bytes([0x5a])*(clusters*512)
            original=bytes(b)
            entry(0,b'SIZED   TXT',2,clusters*512,attr=7)
            repairing(str(bits)+'-size-'+str(length),original,bytes(b),answer='Y')
            repairing(str(bits)+'-size-cancel-'+str(length),original,original,1,answer='N')
        for link in (0,1,65000 if bits==12 else 65001):
            b,fat,entry,end,data=fixture(bits)
            if bits==12 and link>4095: link=4000
            entry(0,b'EOF     TXT',2,13);fat(2,link);original=bytes(b)
            fat(2,end)
            repairing(str(bits)+'-eof-'+str(link),original,bytes(b),answer='Y')
        b,fat,entry,end,data=fixture(bits)
        entry(0,b'SUB',2,attr=16);original=bytes(b);fat(2,end)
        repairing(str(bits)+'-directory-eof',original,bytes(b),answer='Y')
        b,fat,entry,end,data=fixture(bits)
        entry(0,b'BAD     TXT',2,512);fat(2,0xff7 if bits==12 else 0xfff7)
        repairing(str(bits)+'-bad-marker',b,bytes(b),2,answer='Y')
        # Ordinary recovered chain, including a name collision.
        b,fat,entry,end,data=fixture(bits)
        entry(0,b'FILE0028CHK',0,0);fat(40,41);fat(41,end)
        b[(data+38)*512:(data+40)*512]=bytes([0xa7])*1024
        original=bytes(b);entry(1,b'FILE0029CHK',40,1024,attr=32)
        repairing(str(bits)+'-recover-collision',original,bytes(b),answer='Y')
        # A cycle is recovered once, cut at its last cluster.
        b,fat,entry,end,data=fixture(bits)
        fat(40,41);fat(41,40);original=bytes(b)
        fat(41,end);entry(0,b'FILE0028CHK',40,1024,attr=32)
        repairing(str(bits)+'-recover-cycle',original,bytes(b),answer='Y')
        # Orphan components sharing a tail become distinct, disjoint files.
        b,fat,entry,end,data=fixture(bits)
        fat(40,42);fat(41,42);fat(42,end);original=bytes(b)
        fat(41,end);entry(0,b'FILE0028CHK',40,1024,attr=32);entry(1,b'FILE0029CHK',41,512,attr=32)
        repairing(str(bits)+'-recover-join',original,bytes(b),answer='Y')
        # A dangling pointer into a free cluster is not adopted as file data.
        b,fat,entry,end,data=fixture(bits)
        fat(40,41);original=bytes(b)
        fat(40,end);entry(0,b'FILE0028CHK',40,512,attr=32)
        repairing(str(bits)+'-recover-free-tail',original,bytes(b),answer='Y')
        # Capacity failure is preflighted for the whole recovery, no writes.
        b,fat,entry,end,data=fixture(bits)
        for slot in range(31): entry(slot,('F%07dTXT'%slot).encode(),0)
        fat(40,end);fat(41,end)
        repairing(str(bits)+'-recover-root-full',b,bytes(b),2,answer='Y')
        # An end marker followed by stale data remains correctly terminated.
        b,fat,entry,end,data=fixture(bits)
        root=1+2*((((702 if bits==12 else 6002)*bits+7)//8+511)//512)
        b[root*512+32:root*512+64]=b'Z'*32
        fat(40,end);original=bytes(b)
        entry(0,b'FILE0028CHK',40,512,attr=32);b[root*512+32]=0
        repairing(str(bits)+'-recover-end-marker',original,bytes(b),answer='Y')
        # Combined EOF, size and recovery changes with two confirmations.
        b,fat,entry,end,data=fixture(bits)
        entry(0,b'BROKEN  TXT',2,900);fat(40,end);original=bytes(b)
        fat(2,end);entry(0,b'BROKEN  TXT',2,512);entry(1,b'FILE0028CHK',40,512,attr=32)
        repairing(str(bits)+'-combined',original,bytes(b),answer='YY')
    print('PASS: %d size/EOF/recovery cases; exact directory/FAT changes checked'%(total-extra))
