"""Mock native resolver/launcher: explicit types, SYS fallback and ownership."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#include "spawn.h"
struct file {int drive,user,sys;char name[11];};
static struct file files[16];
static int count,user=7,drive=2,sysdisk=3,opened,opens,closes,launches;
static int dosown,dosreject,launchkind,consumed;
int FMDOSOWN(){return dosown;}
static int orderfail,parsefail,openfail,closefail,launchfail,launchuser;
static char searchorder[12],line[128],saved[128],foreign[128],*dma,*handle;
int FMORDER(out)
char *out;
{assert(out[0]==1);if(orderfail)return -1;memcpy(out+1,searchorder,12);return 0;}
int FMSYSDISK(){return sysdisk;}
int FMLAUNCH(command,kind,fcb)
char *command,*fcb;int kind;
{
 assert(dma==saved);dosown=0;launchkind=kind;
 if(kind){assert(kind==1 && opened && fcb==handle);
  if(!dosreject){dosown=1;opened=0;++consumed;}}
 else assert(!fcb && !opened);
 ++launches;strcpy(line,command);launchuser=user;
 user=4;dma=foreign;
 return (launchfail || dosreject) ? -1 : 0;
}
int BDOS(fn,arg)
int fn;char *arg;
{
 int i,j,d;char **packet,*p,*f;
 if(fn==32){if((long)arg==255)return user;user=(int)(long)arg;return user;}
 if(fn==25)return drive-1;
 if(fn==26){dma=arg;return 0;}
 if(fn==152){
  if(parsefail)return 65535;
  packet=(char **)arg;p=packet[0];f=packet[1];
  memset(f,0,36);memset(f+1,' ',11);
  if(p[1]==':'){f[0]=p[0]-'A'+1;p+=2;}
  j=1;for(i=0;p[i];++i){if(p[i]=='.')j=9;else f[j++]=p[i];}
  return 0;
 }
 if(fn==15){
  ++opens;assert(!opened && dma==saved);
  if(openfail)return 0x03ff;
  d=arg[0]?arg[0]:drive;
  for(i=0;i<count;++i)if(files[i].drive==d && files[i].user==user &&
     !memcmp(arg+1,files[i].name,11)){
   if(files[i].sys)arg[10]|=128;
   opened=1;handle=arg;return 0;
  }
  return 255;
 }
 assert(fn==16 && opened && handle==arg);++closes;
 if(closefail){closefail=0;return 0x03ff;}
 opened=0;return 0;
}
static int add(d,u,name,sys)
int d,u,sys;char *name;
{
 files[count].drive=d;files[count].user=u;files[count].sys=sys;
 memcpy(files[count].name,name,11);++count;return 0;
}
static int reset()
{
 count=opened=opens=closes=launches=dosown=dosreject=launchkind=consumed=0;user=7;drive=2;sysdisk=3;
 orderfail=parsefail=openfail=closefail=launchfail=0;
 memcpy(searchorder,"CMDCOMEXEBAT",12);dma=saved;line[0]=0;
 return 0;
}
static int attempt(command,want,expected,owner)
char *command,*expected;int want,owner;
{
 char input[180],before[180];int r;
 strcpy(input,command);strcpy(before,command);
 r=fm_spawn(input,saved);
 assert(r==want && user==7 && dma==saved && !opened);
 assert(!strcmp(input,before));
 if(expected)assert(launches==1 && !strcmp(line,expected) && launchuser==owner);
 if(want)assert(!fm_spawn_error()[0]);else assert(fm_spawn_error()[0]);
 return 0;
}
int main(void)
{
 int i;char large[160];
 reset();add(2,7,"HELLO   CMD",0);
 attempt("hello.cmd /Mixed tail",1,"B:HELLO.CMD /Mixed tail",7);
 assert(opens==1 && closes==1);
 reset();add(1,7,"HELLO   CMD",0);
 attempt(" a:hello.cmd\tArg",1,"A:HELLO.CMD\tArg",7);assert(closes==1);
 reset();add(3,7,"HELLO   CMD",1);
 attempt("hello",1,"C:HELLO.CMD",7);assert(closes==1);
 reset();add(3,7,"HELLO   CMD",0);add(3,0,"HELLO   CMD",1);
 attempt("HELLO.CMD arg",1,"C:HELLO.CMD arg",0);assert(closes==2);
 reset();add(3,7,"HELLO   CMD",0);add(3,0,"HELLO   CMD",0);
 attempt("HELLO.CMD",0,0,0);assert(!launches && closes==2);
 reset();add(3,7,"HELLO   CMD",1);
 attempt("A:HELLO.CMD",0,0,0);assert(opens==1 && !launches);
 reset();attempt("RSP /X",1,"RSP /X",7);
 reset();orderfail=1;attempt("RSP",1,"RSP",7);
 reset();add(2,7,"SCRIPT  BAT",0);
 attempt("script.bat /Mixed",1,"BATCH B:SCRIPT.BAT /Mixed",7);
 assert(closes==1);
 reset();memcpy(searchorder,"BATCMDCOMEXE",12);add(3,0,"SCRIPT  BAT",1);
 attempt("script Arg",1,"BATCH C:SCRIPT.BAT Arg",0);
 reset();add(2,7,"HELLO   CMD",0);orderfail=1;
 attempt("HELLO",1,"B:HELLO.CMD",7);
 /* A DOS match is not silently substituted by a later native CMD. */
 reset();memcpy(searchorder,"COMCMDEXEBAT",12);
 add(2,7,"HELLO   COM",0);add(2,7,"HELLO   CMD",0);
 attempt("HELLO",1,"B:HELLO.COM",7);assert(opens==1 && !closes && consumed==1 && launchkind==1);
 reset();add(2,7,"HELLO   EXE",0);
 attempt("HELLO.EXE /X",1,"B:HELLO.EXE /X",7);assert(!closes && consumed==1);
 reset();add(3,0,"HELLO   COM",1);
 attempt("HELLO.COM /X",1,"C:HELLO.COM /X",0);assert(!closes && consumed==1);
 reset();add(2,7,"HELLO   COM",0);launchfail=1;
 attempt("HELLO.COM",0,"B:HELLO.COM",7);assert(!closes && consumed==1);
 reset();add(2,7,"HELLO   COM",0);dosreject=1;
 attempt("HELLO.COM",0,"B:HELLO.COM",7);assert(closes==1 && !consumed);
 reset();add(2,7,"HELLO   EXE",0);dosreject=1;closefail=1;
 attempt("HELLO.EXE",0,"B:HELLO.EXE",7);assert(closes==2 && !consumed);
 reset();attempt("HELLO.COM",0,0,0);assert(!launches);
 reset();attempt("HELLO.EXE /X",0,0,0);assert(!launches);
 reset();memcpy(searchorder,"BADCMDEXEBAT",12);attempt("HELLO",0,0,0);assert(!opens);
 reset();parsefail=1;attempt("HELLO.CMD",0,0,0);assert(!opens);
 reset();openfail=1;attempt("HELLO.CMD",0,0,0);assert(opens==1 && !launches);
 reset();add(2,7,"HELLO   CMD",0);closefail=1;
 attempt("HELLO.CMD",0,0,0);assert(closes==2 && !launches);
 reset();add(2,7,"HELLO   CMD",0);launchfail=1;
 attempt("HELLO.CMD",0,"B:HELLO.CMD",7);assert(closes==1);
 {char *bad[]={"","   ","A:","Q:A.CMD","A/B.CMD","A\\B.CMD","A*.CMD",
 "A?.CMD","A;.CMD","A!.CMD","A,.CMD","A|.CMD","A=.CMD",".CMD",
 "123456789.CMD","A.ABCD","A..CMD","A.","A.TXT",0};
 for(i=0;bad[i];++i){reset();attempt(bad[i],0,0,0);assert(!opens && !launches);}}
 reset();memset(large,'X',128);large[128]=0;attempt(large,0,0,0);assert(!opens);
 /* Input fits, but resolved prefix/BATCH expansion must still reject overflow. */
 reset();add(2,7,"SCRIPT  BAT",0);strcpy(large,"SCRIPT.BAT ");
 for(i=11;i<127;++i)large[i]='x';large[127]=0;
 attempt(large,0,0,0);assert(closes==1 && !launches);
 reset();add(2,7,"HELLO   COM",0);strcpy(large,"HELLO.COM ");
 for(i=10;i<127;++i)large[i]='x';large[127]=0;
 attempt(large,0,0,0);assert(closes==1 && !launches && !consumed);
 reset();assert(!fm_spawn(0,saved) && user==7 && dma==saved);
 assert(!fm_spawn("HELLO",0));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'spawn.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: native launch resolution, SYS/user fallback, ORDER, bounded tails, native/DOS FCB ownership and rejection cleanup')
