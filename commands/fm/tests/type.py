"""Original Type conversion and incremental pagination, without file I/O."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = r"""
#include <assert.h>
#include "type.h"
static int count, rows[512], columns[512], chars[512];
int cell(int row, int col, int ch) {
    assert(count < 512);
    rows[count]=row; columns[count]=col; chars[count]=ch;
    ++count;
    return 1;
}
int main(void) {
    struct fm_type v;
    int i, expected, low;
    /* Test every possible input byte separately, including DEL and 0xff. */
    for (i=0; i<256; ++i) {
        count=0; fm_type_init(&v,24); low=i&127;
        expected=low==26 ? FM_TYPE_END : FM_TYPE_MORE;
        assert(fm_type_feed(&v,i,cell)==expected);
        if (low==26 || low==13 || low==10) assert(count==0);
        else if (low==9) {
            assert(count==8 && v.column==8);
            for (expected=0; expected<8; ++expected)
                assert(chars[expected]==' ' && columns[expected]==expected);
        } else {
            assert(count==1 && chars[0]==(low<32 ? ' ' : low));
            assert(rows[0]==3 && columns[0]==0);
        }
        assert(v.row==(low==13 ? 4 : 3));
    }
    count=0; fm_type_init(&v,24);
    fm_type_feed(&v,'A',cell); fm_type_feed(&v,9,cell);
    fm_type_feed(&v,'B',cell); fm_type_feed(&v,10,cell);
    fm_type_feed(&v,13,cell); fm_type_feed(&v,'C',cell);
    assert(count==10 && chars[0]=='A' && chars[8]=='B');
    assert(columns[8]==8 && rows[9]==4 && columns[9]==0);
    /* Long lines are consumed and clipped, never wrapped. Tab also clips. */
    count=0; fm_type_init(&v,24);
    for (i=0; i<77; ++i) fm_type_feed(&v,'x',cell);
    fm_type_feed(&v,9,cell);
    for (i=0; i<200; ++i) fm_type_feed(&v,'y',cell);
    assert(count==78 && chars[77]==' ' && v.column==78 && v.row==3);
    fm_type_feed(&v,9,cell); assert(count==78);
    fm_type_feed(&v,13,cell); fm_type_feed(&v,'z',cell);
    assert(count==79 && rows[78]==4 && columns[78]==0);
    /* A page ends on its CR. No bytes render until an explicit resume. */
    count=0; fm_type_init(&v,5);
    assert(fm_type_feed(&v,13,cell)==FM_TYPE_MORE);
    assert(fm_type_feed(&v,13,cell)==FM_TYPE_PAGE);
    assert(v.row==5 && v.column==0);
    assert(fm_type_feed(&v,'x',cell)==FM_TYPE_PAGE && count==0);
    assert(fm_type_resume(&v)==FM_TYPE_MORE && v.row==3);
    fm_type_feed(&v,'x',cell);
    assert(rows[0]==3 && columns[0]==0);
    assert(fm_type_resume(&v)==FM_TYPE_MORE && v.column==1);
    assert(fm_type_feed(&v,154,cell)==FM_TYPE_END);
    assert(fm_type_resume(&v)==FM_TYPE_END);
    assert(fm_type_feed(&v,'y',cell)==FM_TYPE_END && count==1);
    fm_type_init(&v,24);
    assert(fm_type_feed(&v,-1,cell)==FM_TYPE_END && count==1);
    fm_type_init(&v,0);
    assert(fm_type_feed(&v,13,cell)==FM_TYPE_PAGE);
    fm_type_init(&v,24);
    assert(fm_type_feed(&v,'x',0)==FM_TYPE_MORE && v.column==1);
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / 'check.c'
    src.write_text(source)
    exe = Path(tmp) / 'check'
    subprocess.run(['cc', '-std=c89', '-Wno-deprecated-non-prototype',
                    '-I', str(root), str(src), str(root / 'type.c'),
                    '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('PASS: Type all-byte conversion, tabs, clipping, EOF and page resume')
