"""Original Print byte conversion and output failure propagation."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = r"""
#include <assert.h>
#include "prtext.h"
static int count, chars[32], failat;
int put(int ch) {
    if (count == failat) return 0;
    chars[count % 32] = ch;
    ++count;
    return 1;
}
int main(void) {
    struct fm_prtext p;
    int i, j, low, end, expected;
    failat = -1;
    for (i=0; i<256; ++i) {
        count=0; fm_prtext_init(&p); low=i&127;
        end=i==255 || low==26;
        assert(fm_prtext_feed(&p,i,put)==(end ? 1 : 0));
        if (end) {
            assert(count==0 && p.column==0);
            assert(fm_prtext_feed(&p,'x',put)==1 && count==0);
        } else if (low==9) {
            assert(count==8 && p.column==0);
            for (j=0; j<8; ++j) assert(chars[j]==' ');
        } else {
            expected=low<32 && low!=10 && low!=12 && low!=13 ? ' ' : low;
            assert(count==1 && chars[0]==expected);
            assert(p.column==(low==10 || low==12 || low==13 ? 0 : 1));
        }
    }
    /* Tabs at every column, including a full tab at a tab stop. */
    for (i=0; i<8; ++i) {
        count=0; fm_prtext_init(&p);
        for (j=0; j<i; ++j) assert(fm_prtext_feed(&p,'x',put)==0);
        assert(fm_prtext_feed(&p,9,put)==0);
        assert(count==8 && p.column==0);
        for (j=i; j<8; ++j) assert(chars[j]==' ');
    }
    count=0; fm_prtext_init(&p);
    fm_prtext_feed(&p,'A',put);
    fm_prtext_feed(&p,10,put); fm_prtext_feed(&p,12,put);
    assert(p.column==1 && count==3 && chars[1]==10 && chars[2]==12);
    fm_prtext_feed(&p,9,put); assert(count==10 && p.column==0);
    fm_prtext_feed(&p,'B',put); fm_prtext_feed(&p,13,put);
    assert(p.column==0 && chars[11]==13);
    fm_prtext_feed(&p,9,put); assert(count==20 && p.column==0);
    /* Long streams cannot overflow a 16-bit column counter. */
    count=0; fm_prtext_init(&p);
    for (i=0; i<100000; ++i) {
        assert(fm_prtext_feed(&p,'x',put)==0);
        assert(p.column==((i+1)&7));
    }
    assert(fm_prtext_feed(&p,9,put)==0 && count==100008);
    assert(fm_prtext_feed(&p,-1,put)==1 && count==100008);
    assert(fm_prtext_feed(&p,'x',put)==1 && count==100008);
    /* Failure on ordinary output and at each position of an expanded tab. */
    count=0; failat=0; fm_prtext_init(&p);
    assert(fm_prtext_feed(&p,'x',put)==-1 && count==0);
    for (i=0; i<8; ++i) {
        count=0; failat=i; fm_prtext_init(&p);
        assert(fm_prtext_feed(&p,9,put)==-1 && count==i && p.column==i);
        failat=-1;
        assert(fm_prtext_feed(&p,'x',put)==-1 && count==i);
    }
    fm_prtext_init(&p);
    assert(fm_prtext_feed(&p,'x',0)==-1);
    fm_prtext_init(&p);
    assert(fm_prtext_feed(&p,26,0)==1);
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / 'check.c'
    src.write_text(source)
    exe = Path(tmp) / 'check'
    subprocess.run(['cc', '-std=c89', '-Wno-deprecated-non-prototype',
                    '-I', str(root), str(src), str(root / 'prtext.c'),
                    '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('PASS: Print all-byte conversion, tabs, controls, long streams and failures')
