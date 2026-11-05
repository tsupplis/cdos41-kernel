"""Pure control formatter: exact legacy bytes and failure boundaries."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "backup.h"
static char output[4096];static int used,fail=-1;
static struct fm_browser b;static struct fm_file f[2];
static struct fm_marks marks,before;static char *names[2];
int put(c)int c;{if(used==fail)return 0;output[used++]=c;return 1;}
int run(source,user,fat,path,destination,whole)
int source,user,fat,destination,whole;char *path;
{int r;before=marks;used=0;r=fm_backup_control(&b,f,2,&marks,source,user,fat,path,destination,whole,put);
 assert(!memcmp(&marks,&before,sizeof(marks)));return r;}
int main(argc,argv)int argc;char **argv;
{
 int i,n;memset(&b,0,sizeof(b));memset(f,0,sizeof(f));memset(&marks,0,sizeof(marks));
 strcpy(f[0].name,"SECOND.TXT ");strcpy(f[1].name,"FIRST.DAT");
 names[0]=f[1].name;names[1]=f[0].name;b.names=names;b.navigation.count=2;
 marks.value[0]=marks.value[1]=1;marks.count=2;
 assert(run(3,9,0,0,1,0));n=used;
 for(i=0;i<n;++i){fail=i;assert(!run(3,9,0,0,1,0) && used==i);}
 fail=-1;
 assert(run(1,15,0,0,2,0));output[used]=0;assert(strstr(output,"EXC: 15,A,a,k,FIRST.DAT\r\n"));
 assert(run(1,0,0,0,2,0));output[used]=0;assert(strstr(output,"EXC:  0,A,a,k,FIRST.DAT\r\n"));
 assert(!run(0,0,0,0,1,0) && !used);
 assert(!run(17,0,0,0,1,0) && !used);
 assert(!run(3,-1,0,0,1,0) && !used);
 assert(!run(3,16,0,0,1,0) && !used);
 assert(!run(3,0,0,0,3,0) && !used);
 assert(!run(3,0,1,0,1,0) && !used);
 assert(!run(3,0,1,"C:\\DIR\r\nBAD",1,0) && !used);
 f[1].directory=1;assert(!run(3,0,0,0,1,0) && !used);f[1].directory=0;
 strcpy(f[1].name,"BAD?.TXT");assert(!run(3,0,0,0,1,0) && !used);
 strcpy(f[1].name,"FIRST.DAT");
 names[0]="UNKNOWN.TXT";assert(!run(3,0,0,0,1,0) && !used);names[0]=f[1].name;
 marks.value[0]=marks.value[1]=marks.count=0;
 assert(!run(3,0,0,0,1,0) && !used && !strcmp(fm_backup_error(),"No files selected for Backup"));
 if(argc>1) assert(run(16,15,1,"P:\\BACKUP",2,1));
 else {marks.value[0]=marks.value[1]=1;marks.count=2;assert(run(3,9,0,0,1,0));}
 assert(!*fm_backup_error());fwrite(output,1,used,stdout);return 0;
}
'''
header='''CLEAR: 2,27,69
ATTRIBUTE: start screen: 9,27,99,0,27,97,3,27,98,2
ATTRIBUTE: leave screen: 3,27,98,7
ATTRIBUTE: general: 3,27,98,2
ATTRIBUTE: errors: 3,27,98,15
ATTRIBUTE: message: 3,27,98,14
ATTRIBUTE: data: 3,27,98,3
ATTRIBUTE: input: 3,27,98,12
PRINTER INIT: 1,13
FORMFEED: 1,12
LENGTH: 60
WIDTH: 80
REPORT PRINT: true
SHOW SKIPS: true
ID:Concurrent DOS Hard Disk Backup
SPLIT: true
ERASE: true
'''
common='EXC:  ?,?,c,k,control?.br\nEXC:  ?,?,n,k,*.br?\n'
expected=[header+'DEST DRIVE: A\nSOURCE: C\nCONTROL DRIVE: C\nUSERS: 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15\n'+common+'EXC:  9,C,a,k,FIRST.DAT\nEXC:  9,C,a,k,SECOND.TXT \nEXC:  ?,?,n,k,*.*\n',header+'DEST DRIVE: B\nSOURCE: P\nCONTROL DRIVE: P\nPATH: P:\\BACKUP\n'+common+'EXC:  D,P,a,k,*.*\nEXC:  ?,?,n,k,*.*\n']
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 extracted=Path(tmp)/'formatter.c';extracted.write_text((root/'backup.c').read_text().split('/* Backup control output uses')[0])
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(extracted),'-o',str(exe)],check=True)
 for args,want in zip([[],['fat']],expected):
  got=subprocess.check_output([str(exe),*args]);assert got==want.replace('\n','\r\n').encode(),repr(got)
print('PASS: exact CP/M and FAT control bytes, selection preservation, invalid inputs and every byte-write failure')
