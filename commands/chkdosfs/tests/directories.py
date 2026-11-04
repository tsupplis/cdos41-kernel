"""R/RF tree validation, root-only changes and injected-failure regressions."""
from pathlib import Path
import os,re,struct,subprocess,tempfile
from fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
count=0
with tempfile.TemporaryDirectory(prefix='chkdosfs-R-') as temporary:
    folder=Path(temporary);exe=folder/'check'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type',
                    '-Wno-deprecated-non-prototype','-I',str(ROOT),str(ROOT/'fat.c'),
                    str(ROOT/'check.c'),str(ROOT/'tests/host.c'),'-o',str(exe)],check=True)
    def run(image,fix=False,answer='Y',writefail=-1,readfail=-1,deleted=False,contiguous=False):
        global count
        path=folder/'disk.img';path.write_bytes(image);trace=folder/'trace.bin'
        p=subprocess.run([str(exe),str(path),'-1',answer,str(writefail),str(int(deleted)),
                          str(int(fix)),str(readfail),str(int(contiguous)),'1'],
                         env=dict(os.environ,CHKDOSFS_TRACE=str(trace)),
                         capture_output=True,text=True,timeout=10)
        journal=trace.read_bytes();assert len(journal)%516==0
        records=[(struct.unpack_from('<I',journal,i)[0],journal[i+4:i+516])
                 for i in range(0,len(journal),516)]
        count+=1
        return p.returncode,p.stdout,path.read_bytes(),records
    def tree(bits,empty=False,second=False):
        b,fat,e,end,data=fixture(bits)
        e(0,b'LIVE    TXT',2,13,attr=7);fat(2,end)
        b[data*512:(data+1)*512]=bytes([0x55])*512
        def header(c,parent):
            e(0,b'.',c,attr=16,sector=data+c-2)
            e(1,b'..',parent,attr=16,sector=data+c-2)
            fat(c,end)
        header(40,0)
        if not empty:
            e(2,b'CHILD   TXT',41,13,attr=7,sector=data+38);fat(41,end)
            b[(data+39)*512:(data+40)*512]=bytes([0xa5])*512
            e(3,b'SUB',42,attr=16,sector=data+38);header(42,40)
            e(2,b'GRAND   BIN',43,3,sector=data+40);fat(43,end)
            b[(data+41)*512:(data+42)*512]=bytes([0x69])*512
        if second:header(50,0)
        return b,fat,e,end,data,header
    for bits in (12,16):
        for kind in ('nested','empty','two','collision','other-orphan','deleted-child','multi-cluster'):
            b,fat,e,end,data,header=tree(bits,empty=kind=='empty',second=kind=='two')
            at=(data+38)*512;slot=1;name=b'FILE0028CHK'
            if kind=='collision':e(1,b'file0028chk',0);slot=2;name=b'FILE0029CHK'
            if kind=='other-orphan':fat(70,end)
            if kind=='deleted-child':
                e(4,b'ERASED  TXT',44,1,sector=data+38);b[at+128]=229;fat(44,end)
            if kind=='multi-cluster':
                for j in range(4,16):e(j,('F%07dTXT'%j).encode(),0,sector=data+38)
                fat(40,44);fat(44,end);e(0,b'LAST    TXT',45,1,sector=data+42);fat(45,end)
            original=bytes(b)
            e(slot,name,40,attr=16)
            if kind=='two':e(slot+1,b'FILE0032CHK',50,attr=16)
            expected=bytes(b)
            rc,out,after,journal=run(original)
            assert rc==1 and after==original and not journal,(bits,kind,'R',out)
            assert 'Directory recovery candidates: '+('2' if kind=='two' else '1') in out
            rc,out,after,baseline=run(original,True)
            assert rc==(1 if kind in ('other-orphan','deleted-child') else 0) and after==expected,(bits,kind,'RF',out)
            assert all(data-2<=sector<data for sector,_ in baseline),(bits,kind,'not root-only')
            assert after[:(data-2)*512]==original[:(data-2)*512] and after[data*512:]==original[data*512:]
            rc,text,image,writes=run(original,True,'NN')
            assert rc==1 and image==original and not writes,(bits,kind,'cancel')
            if kind not in ('nested','two','multi-cluster'):continue
            def prefix(records):
                image=bytearray(original)
                for sector,payload in records:image[sector*512:(sector+1)*512]=payload
                return image
            for index in range(len(baseline)):
                rc,text,image,writes=run(original,True,writefail=index)
                assert rc==2 and writes==baseline[:index+1] and image==prefix(baseline[:index]),(bits,kind,index,text)
                assert 'TEST WRITE ATTEMPT' not in text.split('TEST WRITE FAILED',1)[1]
            reads=int(re.search(r'TEST READ COUNT (\d+)',out).group(1))
            for index in sorted({0,1,reads//4,reads//2,3*reads//4,reads-1}):
                rc,text,image,writes=run(original,True,readfail=index)
                assert rc==2 and writes==baseline[:len(writes)] and image==prefix(writes),(bits,kind,index,text)
                assert 'TEST WRITE ATTEMPT' not in text.split('TEST READ FAILED',1)[1]
                if writes:assert 'partial changes' in text,(bits,kind,index,text)
        for kind in ('wrong-self','not-first-level','free-head','missing-dotdot','wrong-attribute',
                     'wrong-size','child-cycle','child-free','directory-cycle','directory-free-tail',
                     'bad-cluster','live-crosslink','shared-child','wrong-child-parent','duplicate',
                     'invalid-name','misplaced-dot','label-child','reserved-attribute','directory-size','mirror-conflict','root-full'):
            b,fat,e,end,data,header=tree(bits);at=(data+38)*512
            ignored=kind in ('wrong-self','not-first-level','free-head','missing-dotdot','wrong-attribute','wrong-size')
            if kind=='wrong-self':struct.pack_into('<H',b,at+26,39)
            if kind=='not-first-level':struct.pack_into('<H',b,at+58,20)
            if kind=='free-head':fat(40,0)
            if kind=='missing-dotdot':b[at+33]=32
            if kind=='wrong-attribute':b[at+11]=0
            if kind=='wrong-size':struct.pack_into('<I',b,at+28,1)
            if kind=='child-cycle':fat(41,41)
            if kind=='child-free':fat(41,0)
            if kind=='directory-cycle':fat(40,40)
            if kind=='directory-free-tail':fat(40,44)
            if kind=='bad-cluster':fat(41,0xff7 if bits==12 else 0xfff7)
            if kind=='live-crosslink':struct.pack_into('<H',b,at+2*32+26,2)
            if kind=='shared-child':header(50,0);e(2,b'SHARED  TXT',41,13,sector=data+48)
            if kind=='wrong-child-parent':struct.pack_into('<H',b,(data+40)*512+58,0)
            if kind=='duplicate':e(4,b'child   txt',44,1,sector=data+38);fat(44,end)
            if kind=='invalid-name':e(4,b'BAD?    TXT',0,sector=data+38)
            if kind=='misplaced-dot':e(4,b'.',40,attr=16,sector=data+38)
            if kind=='reserved-attribute':b[at+2*32+11]|=0x80
            if kind=='directory-size':struct.pack_into('<I',b,at+3*32+28,17)
            if kind=='label-child':e(4,b'LABEL',0,attr=8,sector=data+38)
            if kind=='mirror-conflict':fat(41,0,copy=1)
            if kind=='root-full':
                for j in range(32):e(j,('F%07dTXT'%j).encode(),0)
            original=bytes(b)
            for fix in (False,True):
                rc,out,after,journal=run(original,fix)
                expected_rc=1 if not fix or ignored else 2
                assert rc==expected_rc and after==original and not journal,(bits,kind,fix,out)
        # DR/DRF must never allocate an erased, free directory remnant.
        b,fat,e,end,data,header=tree(bits,empty=True);fat(40,0)
        for fix in (False,True):
            rc,out,after,journal=run(b,fix,deleted=True)
            assert rc==0 and after==b and not journal,(bits,'DR free remnant',fix,out)
            assert 'Erased directory remnants: 1' in out and 'Directory recovery candidates: 0' in out
        # L and R preflight scratch must not contaminate each other's ownership.
        b,fat,e,end,data,header=tree(bits)
        e(1,b'LOST    TXT',60,700);e(2,b'ANCHOR  TXT',62,1);fat(62,end)
        original=bytes(b);fat(60,61);fat(61,end);e(3,b'FILE0028CHK',40,attr=16)
        rc,out,after,journal=run(original,True,'YY',contiguous=True)
        assert rc==0 and after==b,(bits,'LFR',out)
        # The full candidate set is bounded before any root entries are added.
        b,fat,e,end,data=fixture(bits,root=512)
        for c in range(100,357):
            e(0,b'.',c,attr=16,sector=data+c-2);e(1,b'..',0,attr=16,sector=data+c-2);fat(c,end)
        for fix in (False,True):
            rc,out,after,journal=run(b,fix)
            assert rc==2 and after==b and not journal,(bits,'candidate cap',fix,out)
            assert 'Too many directory candidates' in out
    print(f'PASS: {count} R/RF/DR/DRF cases; complete-tree preflight, root-only changes and failure prefixes verified')

    for bits in (12,16):
        b,fat,e,end,data,header=tree(bits);fat(2,0);original=bytes(b);fat(2,end)
        rc,out,after,writes=run(original,True,'YN')
        assert rc==1 and after==b,(bits,'staged cancellation',out)
        assert 'previous changes retained' in out and 'Repair cancelled; no changes written.' not in out
    print('PASS: 2 staged cancellation cases; prior verified changes reported accurately')
