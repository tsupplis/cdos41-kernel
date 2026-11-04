"""L/LF candidate and failure tests use the production checker and FAT writer."""
from pathlib import Path
import os,re,struct,subprocess,tempfile
from fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
count=0
with tempfile.TemporaryDirectory(prefix='chkdosfs-L-') as temporary:
    folder=Path(temporary);exe=folder/'check'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type',
                    '-Wno-deprecated-non-prototype','-I',str(ROOT),str(ROOT/'fat.c'),
                    str(ROOT/'check.c'),str(ROOT/'tests/host.c'),'-o',str(exe)],check=True)
    def run(image,fix=False,answer='Y',writefail=-1,readfail=-1):
        global count
        path=folder/'disk.img';path.write_bytes(image);trace=folder/'trace.bin'
        p=subprocess.run([str(exe),str(path),'-1',answer,str(writefail),'0',
                          str(int(fix)),str(readfail),'1'],
                         env=dict(os.environ,CHKDOSFS_TRACE=str(trace)),
                         capture_output=True,text=True,timeout=10)
        journal=trace.read_bytes();assert len(journal)%516==0
        records=[(struct.unpack_from('<I',journal,i)[0],journal[i+4:i+516])
                 for i in range(0,len(journal),516)]
        count+=1
        return p.returncode,p.stdout,path.read_bytes(),records
    def setup(bits,start=40,spc=1,slot=0,size=None,multiple=False):
        b,fat,entry,end,data=fixture(bits,spc=spc)
        b[data*512:]=bytes([0x69])*(len(b)-data*512)
        size=size if size is not None else 2*spc*512-100
        for i in range(slot):entry(i,('F%07dTXT'%i).encode(),0)
        entry(slot,b'LOST    TXT',start,size)
        if multiple:
            entry(slot+1,b'SECOND  TXT',start+2,size)
            entry(slot+2,b'ANCHOR  TXT',start+4,1);fat(start+4,end)
        else:entry(slot+1,b'ANCHOR  TXT',start+2,1);fat(start+2,end)
        original=bytes(b)
        fat(start,start+1);fat(start+1,end)
        if multiple:fat(start+2,start+3);fat(start+3,end)
        return b,original,fat,entry,end,data
    for bits in (12,16):
        for kind in ('ordinary','sector-boundary','multiple','split-tail'):
            spc=2 if kind=='sector-boundary' else 1
            slot=15 if kind=='sector-boundary' else 0
            start=340 if kind=='split-tail' else 40
            expected,original,fat,entry,end,data=setup(bits,start,spc,slot,multiple=kind=='multiple')
            if kind=='split-tail':
                # Three clusters place a FAT12 tail across a sector, while
                # keeping the head inside one sector for final activation.
                b,fat,entry,end,data=fixture(bits)
                b[data*512:]=bytes([0x69])*(len(b)-data*512)
                entry(0,b'LOST    TXT',340,1400);entry(1,b'ANCHOR  TXT',343,1);fat(343,end)
                original=bytes(b);fat(340,341);fat(341,342);fat(342,end);expected=bytes(b)
            rc,out,after,writes=run(original)
            assert rc==1 and after==original and not writes,(bits,kind,out)
            assert 'Contiguous-chain candidates: '+('2' if kind=='multiple' else '1') in out
            rc,out,after,baseline=run(original,True)
            assert rc==0 and after==expected,(bits,kind,out)
            assert all(1<=sector<data-2 for sector,_ in baseline),(bits,kind,'non-FAT write')
            rc,out,after,writes=run(original,True,'N')
            assert rc==1 and after==original and not writes,(bits,kind,'cancellation')
            def prefix(records):
                b=bytearray(original)
                for sector,payload in records:b[sector*512:(sector+1)*512]=payload
                return b
            for index in range(len(baseline)):
                rc,out,after,writes=run(original,True,writefail=index)
                assert rc==2 and writes==baseline[:index+1] and after==prefix(baseline[:index]),(bits,kind,index,out)
                assert 'TEST WRITE ATTEMPT' not in out.split('TEST WRITE FAILED',1)[1]
            reads=int(re.search(r'TEST READ COUNT (\d+)',run(original,True)[1]).group(1))
            for index in sorted({0,reads//3,2*reads//3,reads-1}):
                rc,out,after,writes=run(original,True,readfail=index)
                assert rc==2 and writes==baseline[:len(writes)] and after==prefix(writes),(bits,kind,index,out)
                assert 'TEST WRITE ATTEMPT' not in out.split('TEST READ FAILED',1)[1]
            # In every successful prefix, a committed head must already have
            # its complete tail in that same FAT copy.
            live=bytearray(original)
            for record in baseline:
                live=prefix(baseline[:baseline.index(record)+1])
                reserved=1;fatsize=(data-3)//2
                for copy in (0,1):
                    def get(c):
                        at=(reserved+copy*fatsize)*512+(c*bits//8)
                        value=int.from_bytes(live[at:at+2],'little')
                        return value if bits==16 else value>>4 if c&1 else value&4095
                    if get(start):
                        c=start;visited=set()
                        while c<(0xfff8 if bits==16 else 0xff8):
                            assert c>=2 and c not in visited,(bits,kind,'invalid published chain')
                            visited.add(c);c=get(c)
                            assert c,(bits,kind,'head published before tail')
        # Evidence or ownership failures must never fall back to ordinary F.
        for kind in ('wrong-anchor','deleted-anchor','end-marker','label-anchor',
                     'allocated-range','live-reference','overlap','zero-size',
                     'cluster-boundary','root-end','oversized-range','split-head'):
            expected,original,fat,entry,end,data=setup(bits)
            b=bytearray(original)
            root=(data-2)*512
            if kind=='wrong-anchor':struct.pack_into('<H',b,root+32+26,43)
            if kind=='deleted-anchor':b[root+32]=229
            if kind=='end-marker':b[root+32]=0
            if kind=='label-anchor':b[root+43]=8
            if kind=='allocated-range':
                # Modify through the fixture closure, then copy its FAT sector.
                expected,original,fat,entry,end,data=setup(bits)
                fat(41,end);b=bytearray(original)
                for k in range(2):
                    at=(1+k*((data-3)//2))*512+41*bits//8
                    value=int.from_bytes(b[at:at+2],'little')
                    value=end if bits==16 else (value&15)|(end<<4)
                    b[at:at+2]=value.to_bytes(2,'little')
            if kind in ('live-reference','overlap'):
                struct.pack_into('<H',b,root+64+26,41);b[root+64:root+75]=b'OTHER   TXT'
                struct.pack_into('<I',b,root+64+28,1)
            if kind=='zero-size':struct.pack_into('<I',b,root+28,0)
            if kind in ('cluster-boundary','root-end'):
                b,fat,entry,end,data=fixture(bits)
                slot=15 if kind=='cluster-boundary' else 31
                for i in range(slot):entry(i,('F%07dTXT'%i).encode(),0)
                entry(slot,b'LOST    TXT',40,700)
                if slot==15:entry(16,b'ANCHOR  TXT',42,1);fat(42,end)
            if kind=='oversized-range':struct.pack_into('<I',b,root+28,0x7fffffff)
            if kind=='split-head':
                _,original,_,_,_,data=setup(bits,start=341);b=bytearray(original)
                if bits==16:continue # FAT16 entries cannot span sectors.
            original=bytes(b)
            for fix in (False,True):
                rc,out,after,writes=run(original,fix)
                assert rc==(2 if fix else 1) and after==original and not writes,(bits,kind,fix,out)
    print(f'PASS: {count} L/LF cases; exact FAT-only repairs, safe publication order and failure prefixes verified')

    for bits in (12,16):
        for answers,recover in (('YY',True),('YNY',False)):
            b,fat,entry,end,data=fixture(bits)
            entry(0,b'LOST    TXT',40,700);entry(1,b'ANCHOR  TXT',42,1)
            fat(42,end);fat(70,end);original=bytes(b)
            fat(40,41);fat(41,end)
            if recover:entry(2,b'FILE0046CHK',70,512,attr=32)
            else:fat(70,0)
            rc,out,after,writes=run(original,True,answers)
            assert rc==0 and after==b,(bits,'L plus orphan recovery/release',out)
    print('PASS: 4 LF plus orphan recovery/release cases; ownership scratch remains isolated')

    for bits in (12,16):
        b,fat,entry,end,data=fixture(bits,root=1024)
        for i in range(257):
            entry(i*2,('M%07dTXT'%i).encode(),2+i*2,1)
            entry(i*2+1,('A%07dTXT'%i).encode(),3+i*2,1)
            fat(3+i*2,end)
        for fix in (False,True):
            rc,out,after,writes=run(b,fix)
            assert rc==2 and after==b and not writes,(bits,'candidate limit',out)
            assert 'Too many contiguous-chain candidates' in out
    print('PASS: 4 candidate-capacity cases; incomplete scans refuse all writes')
