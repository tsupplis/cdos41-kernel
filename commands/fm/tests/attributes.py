from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#include <stdint.h>
#include "renio.h"
static int user=5,fail,calls;static char saved[128],*dma=saved,got[36];
int BDOS(fn,arg)int fn;char *arg;
{if(fn==32){if((intptr_t)arg!=255)user=(int)(intptr_t)arg;return user;}
 if(fn==26){dma=arg;return 0;}assert(fn==30 && user==7);
 memcpy(got,arg,36);++calls;return fail?255:0;}
int main(){char raw[32],before[32];int i;
 memset(raw,0,sizeof(raw));memcpy(raw+1,"TEST    CMD",11);
 for(i=1;i<12;++i)raw[i]|=128;memcpy(before,raw,32);
 assert(fm_set_attributes(3,7,raw,1,saved));assert(user==5 && dma==saved);
 assert((got[9]&255)==('C'|128) && (got[10]&255)==('M'|128));
 assert(got[11]=='D' && got[1]=='T' && got[0]==3);
 assert(fm_set_attributes(3,7,raw,0,saved));for(i=1;i<12;++i)assert(!(got[i]&128));
 fail=1;assert(!fm_set_attributes(3,7,raw,0,saved));assert(user==5 && dma==saved);
 assert(!memcmp(before,raw,32));assert(!fm_set_attributes(17,7,raw,0,saved));
 assert(calls==3);return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(source)
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(p/'test.c'),str(root/'renio.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS: original system/local attributes, preserved source, caller user/DMA and failed writes')
