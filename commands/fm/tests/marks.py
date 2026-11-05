"""Mark state and rendering, independent of file-changing actions."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include "marks.h"
#include "browse.h"
static int cells;
int cell(int row,int col,int ch,int attr) {
 assert(row==1 && col>=15 && col<27 && attr==112);++cells;return 1;
}
int main(void) {
 struct fm_marks m;struct fm_browser b;struct fm_canvas c;int i;
 char *names[2]={"ONE.TXT     ","TWO.TXT     "};
 fm_marks_clear(&m);
 assert(!fm_marks_key(&m,0,0,44));
 assert(fm_marks_key(&m,1,2,44)==1 && m.count==1);
 assert(fm_marks_key(&m,1,2,44)==0 && m.count==1);
 assert(fm_marks_key(&m,2,2,44)==1 && m.count==2);
 assert(fm_marks_key(&m,1,2,127)==1 && m.count==1);
 assert(!fm_marks_key(&m,1,2,127) && m.count==1);
 b.navigation.count=2;b.navigation.offset=0;b.navigation.capacity=2;b.navigation.columns=2;
 b.area.row=0;b.area.column=0;b.names=names;b.stride=14;b.selected=112;
 c.rows=24;c.columns=80;c.cell=cell;
 assert(fm_marks_draw(&m,&b,&c) && cells==12);
 for(i=1;i<=256;++i)fm_marks_key(&m,i,256,44);
 assert(m.count==256);fm_marks_clear(&m);assert(!m.count);
 for(i=0;i<256;++i)assert(!m.value[i]);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'marks.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: marking bounds, idempotence, count, clear and visible overlay')
