"""Native directory operation FCBs and rejection paths with injected BDOS."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#define __BDOS BDOS
#include "native.c"
static int calls,fnseen,status,cluster=10;
static char captured[36];
int fm_scan(){return 0;}
int FMLOC(drive,out)int drive,*out;
{out[0]=3;out[1]=9;out[2]=cluster;out[3]=1;return 1;}
int BDOS(fn,p)int fn;char *p;
{if(fn==12)return 0x1441;++calls;fnseen=fn;memcpy(captured,p,36);return status;}
int main(){int i,n;
 status=0;assert(fm_native_directory(3,"new.ext",1));assert(calls==1 && fnseen==22);
 assert((captured[0]&255)==131 && !memcmp(captured+1,"NEW     EXT",11));
 for(i=12;i<36;++i)assert(!captured[i]);
 assert(fm_native_directory(16,"child",2));assert(fnseen==19 && (captured[0]&255)==144);
 status=0x0bff;assert(!fm_native_directory(3,"CHILD",2));
 n=calls;assert(!fm_native_directory(3,"*",2));assert(!fm_native_directory(3,"..",2));
 assert(!fm_native_directory(3,"A/B",1));assert(!fm_native_directory(3,"A.",1));
 assert(!fm_native_directory(3,"A..B",1));assert(!fm_native_directory(0,"A",1));
 assert(!fm_native_directory(3,"TOOLONGGG",1));assert(!fm_native_directory(3,"",1));assert(calls==n);
 status=0;assert(fm_native_directory(3,0,0));assert(fnseen==16);
 cluster=0;n=calls;assert(fm_native_directory(3,0,0));assert(calls==n);
 return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'check.c';p.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: FAT directory MAKE/DELETE/root, concrete names, fresh FCB and low-byte errors')
