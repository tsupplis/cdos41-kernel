"""B/BF/RB/RBF coverage and fail-closed repair tests, using production code."""
from pathlib import Path
from collections import Counter
import os,re,struct,subprocess,tempfile
from fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
count=0
with tempfile.TemporaryDirectory(prefix='chkdosfs-B-') as temporary:
    folder=Path(temporary);exe=folder/'check'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type',
                    '-Wno-deprecated-non-prototype','-I',str(ROOT),str(ROOT/'fat.c'),
                    str(ROOT/'check.c'),str(ROOT/'tests/host.c'),'-o',str(exe)],check=True)
    def run(image,*,b=True,fix=False,r=False,l=False,answers='Y',readsector=-1,readfail=-1,writefail=-1):
        global count
        path=folder/'disk.img';path.write_bytes(image)
        trace=folder/'writes.bin';reads=folder/'reads.bin'
        p=subprocess.run([str(exe),str(path),str(readsector),answers,str(writefail),'0',
                          str(int(fix)),str(readfail),str(int(l)),str(int(r)),str(int(b))],
                         env=dict(os.environ,CHKDOSFS_TRACE=str(trace),CHKDOSFS_READ_TRACE=str(reads)),
                         capture_output=True,text=True,timeout=10)
        raw=trace.read_bytes();assert len(raw)%516==0
        writes=[(struct.unpack_from('<I',raw,i)[0],raw[i+4:i+516]) for i in range(0,len(raw),516)]
        rd=reads.read_bytes();assert len(rd)%4==0
        sectors=[v[0] for v in struct.iter_unpack('<I',rd)]
        count+=1
        return p.returncode,p.stdout,path.read_bytes(),writes,sectors
    def allocated(bits,spc=1,clusters=None):
        image,fat,e,end,data=fixture(bits,spc=spc,clusters=clusters)
        def fill(c):
            at=(data+(c-2)*spc)*512
            image[at:at+spc*512]=bytes([0x60+c%32])*(spc*512)
        for c in (2,3,5,10,12):fill(c)
        e(0,b'FIRST   TXT',2,2*spc*512-100);fat(2,3);fat(3,end)
        e(1,b'HIDDEN  BIN',5,1,attr=2);fat(5,end)
        e(2,b'SUB',8,attr=16);fat(8,9);fat(9,end)
        e(0,b'.',8,attr=16,sector=data+6*spc)
        e(1,b'..',0,attr=16,sector=data+6*spc)
        e(2,b'INNER   TXT',10,2*spc*512-100,sector=data+6*spc);fat(10,12);fat(12,end)
        selected=[data+(c-2)*spc+off for c in (2,3,5,8,9,10,12) for off in range(spc)]
        return image,fat,e,end,data,selected
    for bits in (12,16):
        for spc in (1,4):
            image,fat,e,end,data,selected=allocated(bits,spc)
            original=bytes(image)
            rc,text,after,writes,base_reads=run(original,b=False)
            assert rc==0 and after==original and not writes
            for fix in (False,True):
                rc,text,after,writes,reads=run(original,fix=fix)
                assert rc==0 and after==original and not writes,(bits,spc,fix,text)
                assert f'File/directory data sectors read: {len(selected)}' in text
                assert Counter(reads)-Counter(base_reads)==Counter(selected),(bits,spc,'coverage')
                assert not Counter(base_reads)-Counter(reads),(bits,spc,'lost metadata read')
                for sector in selected:
                    rc,text,after,writes,reads=run(original,fix=fix,readsector=sector)
                    assert rc==2 and after==original and not writes,(bits,spc,fix,sector,text)
                    assert reads[-1]==sector and 'Data read test failed' in text
            # Unallocated gaps, unreferenced allocation and bad markers are
            # not a B free-space surface scan and must remain unchanged.
            fat(20,end);fat(30,0xff7 if bits==12 else 0xfff7)
            original=bytes(image)
            for c in (11,20,30,40):
                sector=data+(c-2)*spc
                rc,text,after,writes,reads=run(original,readsector=sector)
                assert rc==1 and after==original and not writes and sector not in reads,(bits,spc,c,text)
            # BF adoption checks every orphan cluster before making it live.
            sector=data+18*spc
            rc,text,after,writes,reads=run(original,fix=True,readsector=sector)
            assert rc==2 and after==original and not writes,(bits,spc,'orphan adoption',text)
            # Explicit release does not pretend to read or repair lost data.
            fat(20,0);expected=bytes(image)
            rc,text,after,writes,reads=run(original,fix=True,answers='NY',readsector=sector)
            assert rc==0 and after==expected and sector not in reads,(bits,spc,'release',text)
        # Large legal FAT12 cluster sizes must be streamed without an 8 KiB
        # limit or reading beyond the selected allocation.
        if bits==12:
            image,fat,e,end,data,selected=allocated(bits,spc=64,clusters=70)
            rc,text,after,writes,reads=run(image)
            assert rc==0 and after==image and not writes and len(selected)==448,text
            assert 'File/directory data sectors read: 448' in text
        image,fat,e,end,data,selected=allocated(bits)
        fat(2,0,copy=1);original=bytes(image)
        for fix in (False,True):
            rc,text,after,writes,reads=run(original,fix=fix)
            assert rc==(2 if fix else 1) and after==original and not writes,(bits,'B mirror conflict',fix,text)
        # A data error must block an otherwise permissible EOF correction.
        image,fat,e,end,data=fixture(bits);e(0,b'BROKEN  TXT',2,1);original=bytes(image)
        for fix in (False,True):
            rc,text,after,writes,reads=run(original,fix=fix,readsector=data)
            assert rc==2 and after==original and not writes,(bits,'EOF gated',text)
        # LB/LBF checks the whole inferred range, not only its first cluster.
        image,fat,e,end,data=fixture(bits)
        e(0,b'LOST    TXT',40,700);e(1,b'ANCHOR  TXT',42,1);fat(42,end);original=bytes(image)
        rc,text,after,writes,reads=run(original,l=True,readsector=data+39)
        assert rc==2 and after==original and not writes,(bits,'LB tail',text)
        fat(40,41);fat(41,end);expected=bytes(image)
        rc,text,after,writes,reads=run(original,fix=True,l=True)
        assert rc==0 and after==expected,(bits,'LBF',text)
        # RB checks candidate directory slack and child data before any root
        # entry is published; RF never changes those FAT/data sectors.
        image,fat,e,end,data=fixture(bits,spc=4)
        e(0,b'LIVE    TXT',2,1);fat(2,end)
        e(0,b'.',40,attr=16,sector=data+38*4)
        e(1,b'..',0,attr=16,sector=data+38*4)
        e(2,b'CHILD   TXT',41,1,sector=data+38*4);fat(40,end);fat(41,end)
        original=bytes(image);selected=[data+(c-2)*4+off for c in (2,40,41) for off in range(4)]
        rc,text,after,writes,baseline_reads=run(original,b=False,r=True)
        assert rc==1 and after==original and not writes
        rc,text,after,writes,reads=run(original,r=True)
        assert rc==1 and after==original and not writes and Counter(reads)-Counter(baseline_reads)==Counter(selected),(bits,'RB',text)
        assert 'File/directory data sectors read: 12' in text
        for fix in (False,True):
            for sector in selected:
                rc,text,after,writes,reads=run(original,r=True,fix=fix,readsector=sector)
                assert rc==2 and after==original and not writes and reads[-1]==sector,(bits,'RB/RBF data error',fix,sector,text)
        fat(2,0);broken=bytes(image)
        rc,text,after,writes,rd=run(broken,r=True,fix=True,readsector=data+39*4+3)
        assert rc==2 and after==broken and not writes,(bits,'RBF blocks unrelated EOF fix',text)
        fat(2,end)
        e(1,b'FILE0028CHK',40,attr=16);expected=bytes(image)
        rc,text,after,baseline,reads=run(original,r=True,fix=True)
        assert rc==0 and after==expected,(bits,'RBF',text)
        assert all(data-2<=sector<data for sector,_ in baseline)
        assert after[data*512:]==original[data*512:]
        def prefix(records):
            result=bytearray(original)
            for sector,payload in records:result[sector*512:(sector+1)*512]=payload
            return result
        for index in range(len(baseline)):
            rc,text,after,writes,rd=run(original,r=True,fix=True,writefail=index)
            assert rc==2 and writes==baseline[:index+1] and after==prefix(baseline[:index]),(bits,'RBF write',index,text)
            assert 'TEST WRITE ATTEMPT' not in text.split('TEST WRITE FAILED',1)[1]
        for index in sorted({0,len(reads)//4,len(reads)//2,3*len(reads)//4,len(reads)-1}):
            rc,text,after,writes,rd=run(original,r=True,fix=True,readfail=index)
            assert rc==2 and writes==baseline[:len(writes)] and after==prefix(writes),(bits,'RBF read',index,text)
            assert len(rd)==index+1 and 'TEST WRITE ATTEMPT' not in text.split('TEST READ FAILED',1)[1],(bits,index,len(rd),text)
            if writes:assert 'partial changes' in text,text
    print(f'PASS: {count} B/BF/RB/RBF/LB/LBF cases; exact read coverage, no data writes and fail-closed metadata repair verified')
