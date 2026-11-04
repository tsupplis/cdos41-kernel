"""Prove diagnostic-only D and bounded, stop-on-failure metadata writes."""
from pathlib import Path
import os
import re
import struct
import subprocess
import tempfile
from fixtures import fixture

ROOT = Path(__file__).resolve().parents[1]
count = 0
with tempfile.TemporaryDirectory(prefix='chkdosfs-safety-') as temporary:
    folder = Path(temporary)
    exe = folder/'checker'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type',
                    '-Wno-deprecated-non-prototype','-I',str(ROOT),
                    str(ROOT/'fat.c'),str(ROOT/'check.c'),str(ROOT/'tests/host.c'),
                    '-o',str(exe)],check=True)

    def run(image, *, fix=False, deleted=False, answers='NN', readsector=-1,
            writefail=-1, readfail=-1):
        global count
        path=folder/'disk.img'; path.write_bytes(image)
        trace=folder/'writes.bin'
        result=subprocess.run([str(exe),str(path),str(readsector),answers,
                               str(writefail),str(int(deleted)),str(int(fix)),str(readfail)],
                              env=dict(os.environ,CHKDOSFS_TRACE=str(trace)),
                              capture_output=True,text=True,timeout=10)
        raw=trace.read_bytes(); assert len(raw)%516==0
        writes=[(struct.unpack_from('<I',raw,at)[0],raw[at+4:at+516])
                for at in range(0,len(raw),516)]
        count+=1
        return result.returncode,result.stdout,path.read_bytes(),writes

    def dot_fixture(bits):
        b,fat,entry,end,data=fixture(bits)
        entry(0,b'.',40,attr=16,sector=data+38)
        entry(1,b'..',0,attr=16,sector=data+38)
        return b,fat,entry,end,data

    for bits in (12,16):
        for kind in ('empty','remnant','live-directory','live-file','allocated-orphan',
                     'wrong-self','wrong-parent','self-parent','wrong-dotdot',
                     'wrong-attribute','label-attribute','wrong-size'):
            b,fat,entry,end,data=dot_fixture(bits)
            expected=1
            if kind=='empty': b[(data+38)*512:(data+39)*512]=bytes(512);expected=0
            if kind in ('live-directory','live-file'):
                fat(40,end);entry(0,b'LIVE',40,512 if kind=='live-file' else 0,
                                  attr=0 if kind=='live-file' else 16);expected=0
            if kind=='allocated-orphan': fat(40,end);expected=0
            at=(data+38)*512
            if kind=='wrong-self': struct.pack_into('<H',b,at+26,41);expected=0
            if kind=='wrong-parent': struct.pack_into('<H',b,at+58,65535);expected=0
            if kind=='self-parent': struct.pack_into('<H',b,at+58,40);expected=0
            if kind=='wrong-dotdot': b[at+33]=32;expected=0
            if kind=='wrong-attribute': b[at+43]=0;expected=0
            if kind=='label-attribute': b[at+11]=24;expected=0
            if kind=='wrong-size': struct.pack_into('<I',b,at+60,1);expected=0
            original=bytes(b)
            for fix in (False,True):
                status,out,after,writes=run(original,fix=fix,deleted=True)
                assert status==(1 if kind=='allocated-orphan' else 0),(bits,kind,fix,out)
                assert f'Erased directory remnants: {expected}' in out,(bits,kind,fix,out)
                assert after==original and not writes,(bits,kind,fix,'unexpected write')
        b,fat,entry,end,data=dot_fixture(bits)
        for fix in (False,True):
            status,out,after,writes=run(b,fix=fix,deleted=True,readsector=data+38)
            assert status==2 and after==b and not writes,(bits,'D I/O failure',out)
        # DF may correct an independently proven file EOF; the free remnant
        # remains entirely untouched and unallocated.
        b,fat,entry,end,data=dot_fixture(bits)
        entry(0,b'BROKEN  TXT',2,10);original=bytes(b);fat(2,end)
        status,out,after,writes=run(original,fix=True,deleted=True,answers='Y')
        assert status==0 and after==b and 'Erased directory remnants: 1' in out,(bits,'DF',out)
        assert after[(data+38)*512:(data+39)*512]==original[(data+38)*512:(data+39)*512]
    diagnostic_cases=count
    print(f'PASS: {diagnostic_cases} D/DF cases; free remnants never written or allocated')

    def scenario(bits,kind):
        b,fat,entry,end,data=fixture(bits)
        b[data*512:]=bytes([0x5a])*(len(b)-data*512)
        if kind=='combined':
            entry(0,b'BROKEN  TXT',2,900);fat(40,41);fat(41,40)
            original=bytes(b)
            fat(2,end);entry(0,b'BROKEN  TXT',2,512)
            fat(41,end);entry(1,b'FILE0028CHK',40,1024,attr=32)
            answers='YY'
        elif kind=='release':
            entry(0,b'OWNED   TXT',340,10);fat(340,end)
            fat(341,342);fat(342,341);original=bytes(b)
            fat(341,0);fat(342,0);answers='NY'
        else:
            for i in range(15): entry(i,('F%07dTXT'%i).encode(),0)
            fat(40,end);original=bytes(b)
            root=data-2
            entry(15,b'FILE0028CHK',40,512,attr=32)
            b[(root+1)*512]=0
            # Bytes beyond the old end marker have no live directory owner.
            original=bytearray(original)
            original[(root+1)*512:(root+1)*512+32]=b'Q'*32
            b[(root+1)*512+1:(root+1)*512+32]=b'Q'*31
            original=bytes(original);answers='Y'
        return original,bytes(b),answers,data

    for bits in (12,16):
        for kind in ('combined','release','root-boundary'):
            original,expected,answers,data=scenario(bits,kind)
            status,out,after,baseline=run(original,fix=True,answers=answers)
            assert status==0 and after==expected,(bits,kind,out)
            assert baseline,(bits,kind,'no writes')
            assert all(1<=sector<data for sector,_ in baseline),(bits,kind,'write outside metadata')
            assert after[data*512:]==original[data*512:],(bits,kind,'data changed')
            reads=int(re.search(r'TEST READ COUNT (\d+)',out).group(1))
            def prefix(writes):
                image=bytearray(original)
                for sector,payload in writes: image[sector*512:(sector+1)*512]=payload
                return image
            assert prefix(baseline)==expected,(bits,kind,'journal mismatch')
            # Fail every individual physical write, not just the first copy.
            for index in range(len(baseline)):
                rc,text,image,writes=run(original,fix=True,answers=answers,writefail=index)
                assert rc==2,(bits,kind,index,text)
                assert writes==baseline[:index+1],(bits,kind,index,'continued after failure')
                assert image==prefix(baseline[:index]),(bits,kind,index,'unexpected bytes')
                assert 'TEST WRITE ATTEMPT' not in text.split('TEST WRITE FAILED',1)[1]
            # Read failures cover preflight, repair, and final verification.
            for index in sorted({0,1,reads//4,reads//2,3*reads//4,reads-1}):
                rc,text,image,writes=run(original,fix=True,answers=answers,readfail=index)
                assert rc==2 and 'TEST READ FAILED' in text,(bits,kind,index,text)
                assert writes==baseline[:len(writes)],(bits,kind,index,'different write plan')
                assert image==prefix(writes),(bits,kind,index,'unexpected bytes')
                assert 'TEST WRITE ATTEMPT' not in text.split('TEST READ FAILED',1)[1]
                if writes: assert 'partial changes' in text,(bits,kind,index,text)
            for fix,reply in ((False,answers),(True,'NN')):
                rc,text,image,writes=run(original,fix=fix,answers=reply)
                assert image==original and not writes,(bits,kind,'unguarded or cancelled write')
    print(f'PASS: {count-diagnostic_cases} safety cases; every write failure stops at its exact expected prefix')
