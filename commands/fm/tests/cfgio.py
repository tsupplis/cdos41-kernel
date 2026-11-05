"""Configuration I/O cleanup and search order, with injected BDOS failures."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <stdint.h>
#include <string.h>
static int user=4, mode, opens, reads, closes;
static char saved[128], *dma=saved;
static int mock(int fn,intptr_t arg) {
    char *f=(char*)arg;
    if(fn==32) { if(arg!=255)user=arg;return user; }
    if(fn==26) {dma=f;return 0;}
    if(fn==15) {
        ++opens;assert(!memcmp(f+1,"FM      CFG",11));
        if(opens==1) {assert(user==4 && f[0]==0);return mode?255:0;}
        assert(user==0 && f[0]==16);return mode==2?255:0;
    }
    if(fn==20) {
        ++reads;
        if(mode==3)return 255;
        memset(dma,26,128);memcpy(dma,"OBJECT FG COLOR=7\r\n",19);return 0;
    }
    assert(fn==16);++closes;return mode==4?255:0;
}
#define __BDOS(fn,arg) mock(fn,(intptr_t)(arg))
#include "cfgio.c"
int main(void) {
    struct fm_config config;
    int result;
    for(mode=0;mode<5;++mode) {
        opens=reads=closes=0;user=4;dma=saved;
        fm_config_defaults(&config);
        result=fm_config_load(&config,saved);
        assert(user==4 && dma==saved);
        assert(opens==(mode?2:1));
        assert(closes==(mode==2?0:1));
        assert(result==(mode>=3?-1:mode==2?0:1));
        assert(config.value[2]==(result==1?7:0));
    }
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
    subprocess.run(['cc','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'config.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: local/system configuration search, absent file, read/close errors, user/DMA restoration')
