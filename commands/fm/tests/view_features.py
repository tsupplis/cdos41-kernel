"""Host gate for staged F10 and Size/Date helpers; no PCE launch."""
from pathlib import Path
import subprocess,tempfile,sys
stage=Path(__file__).resolve().parent
repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/Users/thierry/Projects/CPM86/cdos41-kernel/commands/fm')
# Exercise production editor as well as feature callbacks, with only native I/O mocked.
s=repo.joinpath('fmview.c').read_text()
editor=s[s.index('static int text_ask('):s.index('static int name_ask(')]
if 'static int command_action()' in s:
    command=s[s.index('static int command_action()'):s.index('static int run_report(')]
    details_code=s[s.index('static char detail_lines'):s.index('/* CODE 8EDB')]
    search=s[s.index('static char search_prefix'):s.index('static int repaint()')]
else:
    command=stage.joinpath('features.c').read_text()
    details_code=stage.joinpath('details.c').read_text().replace('static int details;','')
    search=stage.joinpath('search.c').read_text()
source=r'''
#include <assert.h>
#include <string.h>
struct nav {int capacity,offset,count,columns,selected;};
struct rect {int row,column,width;};
struct {struct nav navigation;struct rect area;int stride,selected,normal;} browser;
struct {struct rect files;} layout;
struct {int value[16];} config;
struct {int active;} focus;
struct {char name[13],raw[32];} files[256];
char *names[256],*notice,dma[128];
int details,directories,drives,drive=2,fat,count,normal,promptattr,console,launch_console_error;
int keys[200],keycount,keypos,spawncalls,refreshcalls,spawnresult=1,refreshresult=1,termerror;
int b35,b102,rc35,rc102,querydrive;unsigned long records;
unsigned stampdays;int stamphour,stampminute,stampoffset=28;
char command_seen[128],heading_seen[80];
int text(int r,int c,char *s,int w,int a){if(c==0){strncpy(heading_seen,s,79);}return 1;}
int fm_console_begin(){return 1;}
int fm_console_end(){return 1;}
int fm_console_key(){assert(keypos<keycount);return keys[keypos++];}
int __BDOS(){return 0;}
int fm_attribute(){return 7;}
int fm_browser_open(){browser.navigation.selected=1;return 1;}
int fm_browser_key(void *v,int k){if(k==1)browser.navigation.selected=1;else ++browser.navigation.selected;return 1;}
int run_invoke(char *s){++spawncalls;strcpy(command_seen,s);launch_console_error=termerror;return spawnresult;}
int refresh_retained(){++refreshcalls;return refreshresult;}
int BDOS(int n,char *p){querydrive=p[0];if(n==35){++b35;p[33]=records;p[34]=records>>8;p[35]=records>>16;return rc35;}
assert(n==102);++b102;p[stampoffset]=stampdays;p[stampoffset+1]=stampdays>>8;
p[stampoffset+2]=stamphour;p[stampoffset+3]=stampminute;return rc102;}
'''+editor+command+details_code+search+r'''
void input(char *s,int end){keypos=keycount=0;while(*s)keys[keycount++]=*s++;keys[keycount++]=end;}
int main(void){char raw[32],out[27],before[32];int i;unsigned date,time;
input("tool.cmd /arg",13);assert(command_action());assert(spawncalls==1&&refreshcalls==1);
assert(!strcmp(command_seen,"TOOL.CMD /ARG"));assert(!strcmp(heading_seen,"B>"));
input("discard",27);assert(command_action());input("",13);assert(command_action());assert(spawncalls==1);
input("AB\bC",13);assert(command_action());assert(!strcmp(command_seen,"AC"));
input("AB\030C",13);assert(command_action());assert(!strcmp(command_seen,"C"));
keypos=0;keycount=91;for(i=0;i<90;++i)keys[i]='x';keys[90]=13;
assert(command_action());assert(strlen(command_seen)==77);
spawnresult=0;i=refreshcalls;input("MISSING",13);assert(command_action());assert(refreshcalls==i);
termerror=1;input("TOOL",13);assert(!command_action());termerror=0;
input("",-2);assert(!command_action());
memset(raw,0,32);fat=1;raw[28]=0x34;raw[29]=0x12;raw[30]=1;
date=((2024-1980)<<9)|(2<<5)|29;time=(13<<11)|(5<<5);
raw[24]=date;raw[25]=date>>8;raw[22]=time;raw[23]=time>>8;memcpy(before,raw,32);
detail_line(raw,out);assert(!memcmp(out,"   70196",8));assert(!strcmp(out+10," 2-29-2024 1:05p"));
assert(!memcmp(raw,before,32));assert(!b35&&!b102);
raw[24]=raw[25]=0;detail_line(raw,out);for(i=8;i<26;++i)assert(out[i]==' ');
fat=0;records=130;raw[13]=3;stampdays=1;stamphour=0x00;stampminute=0x09;
detail_line(raw,out);assert(!memcmp(out,"   16515",8));assert(!strcmp(out+10," 1-01-197812:09a"));
assert(querydrive==2&&b35==1&&b102==1);
stampoffset=24;stampdays=2;detail_line(raw,out);assert(!memcmp(out+10," 1-02-1978",10));
rc35=rc102=255;detail_line(raw,out);for(i=0;i<26;++i)assert(out[i]==' ');
rc35=rc102=0;records=0;raw[13]=0;stampdays=0;detail_line(raw,out);assert(!memcmp(out,"     128",8));
names[0]="ALPHA.CMD   ";names[1]="BETA.TXT    ";names[2]="BETTER.TXT  ";
browser.navigation.count=3;browser.navigation.selected=1;
assert(search_key('b')==1&&browser.navigation.selected==2);
assert(search_key('e')==1);assert(search_key('t')==1);assert(search_key('t')==1&&browser.navigation.selected==3);
assert(search_key('z')==1&&search_length==4&&browser.navigation.selected==3);
assert(search_key(127)==1&&search_length==3);assert(search_key(24)==1&&!search_length);
assert(search_key(127)==-1);assert(search_key(',')==-1);
layout.files.width=55;details=0;browser.navigation.selected=7;assert(details_action());
assert(details&&browser.navigation.selected==7);assert(details_action());assert(!details);
layout.files.width=30;assert(details_action());assert(!details);
return 0;}
'''
with tempfile.TemporaryDirectory(prefix='fm-view-host-') as td:
    c=Path(td)/'test.c';exe=Path(td)/'test';c.write_text(source)
    subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('F10 and Size/Date host checks PASS')
