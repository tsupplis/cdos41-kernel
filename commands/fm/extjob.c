/* Original DATA descriptor strings and CODE2380 argument construction.
 * Fields are executable,+12 prefix,+16 first,+18 between,+1A after,+14 tail.
 * These shipped records have no implicit separators between selected names.
 * Help uses its specialized CODE24E0 topic; Backup/Boot need separate flows.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "runjob.h"
#include "extjob.h"
struct tool {
    int index,minimum,maximum,mode;
    char *exe,*prefix,*first,*between,*after,*tail;
};
/* mode0=selected names,1=Help topic,2=chained command,3=special workflow. */
static struct tool tools[]={
    {0,0,32767,1,"HELP.CMD","HELP",0,0,0,0},
    {9,0,32767,3,"BACK.CMD",0,0,0,0,0},
    {10,0,1,0,"DREDIX.CMD",0,0,0,0,0},
    {12,0,32767,0,"DSKMAINT.CMD","/COPY",0,0,0,0},
    {13,0,32767,0,"DSKMAINT.CMD","/FORMAT",0,0,0,0},
    {14,0,32767,0,"STOP.CMD",0,0,0,0,0},
    {20,1,1,0,"FUNCTION.CMD",0,0,0,0,0},
    {21,0,32767,2,"FUNCTION.CMD","!SETUP /PARAM",0,0,0,0},
    {22,0,32767,2,"SETPORT.CMD","!SETUP /PARAM",0,0,0,0},
    {23,0,32767,0,"SETUP.CMD",0,0,0,0,0},
    {24,0,32767,0,"SETUP.CMD","/MDISK",0,0,0,0},
    {25,0,32767,3,"HDMAINT.CMD","[F5,F6,F0,F0]",0,0,0,0},
    {26,0,32767,0,"HDMAINT.CMD",0,0,0,0,0},
    {27,0,32767,0,"DSKMAINT.CMD",0,0,0,0,0}
};
static struct tool *find(index)
int index;
{
    int i;
    for(i=0;i<14;++i) if(tools[i].index==index) return &tools[i];
    return 0;
}
int fm_external_available(index)
int index;
{
    struct tool *t;
    t=find(index);
    return t && t->mode<3;
}
static int reject(ops,s)
struct fm_runner *ops;char *s;
{ return (*ops->report)(s) ? 0 : -1; }
static int append(out,n,s)
char *out,*s;int *n;
{
    if(!s) return 1;
    while(*s) {
        if(*n==127) return 0;
        out[(*n)++]=*s++;
    }
    out[*n]=0;return 1;
}
static int filename(text,out)
char *text,*out;
{
    int i,n,c,base,ext,dot,gap;
    n=base=ext=dot=gap=0;
    for(i=0;i<FM_NAME_SIZE && text[i];++i) {
        c=text[i]&255;
        if(c==' ') {gap=1;continue;}
        if(gap || i>=12 || c<33 || c>126 || c==':' || c=='/' ||
           c=='\\' || c=='*' || c=='?' || c==';' || c==',' ||
           c=='=' || c=='<' || c=='>' || c=='|' || c=='"' ||
           c=='[' || c==']' || c=='!') return 0;
        if(c>='a' && c<='z') c=c-'a'+'A';
        if(c=='.') {if(dot || !base)return 0;dot=1;}
        else if(dot) {if(++ext>3)return 0;}
        else if(++base>8)return 0;
        out[n++]=c;
    }
    if(i==FM_NAME_SIZE || !base || (dot && !ext)) return 0;
    out[n]=0;return 1;
}
static int execute(t,list,files,filecount,marks,ops,prefix)
struct tool *t;
char *prefix;
int filecount;
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
struct fm_runner *ops;
{
    char arguments[128],command[128],name[13];
    int i,k,n,used,first,result;
    if(!ops || !ops->invoke || !ops->report) return -1;
    if(!list || !marks || filecount<0 || filecount>256 ||
       (filecount && !files) || list->navigation.count<0 ||
       list->navigation.count>256 || (list->navigation.count && !list->names))
        return reject(ops,"Invalid file selection");
    n=0;
    for(i=0;i<list->navigation.count;++i) if(marks->value[i]) ++n;
    if(!n && t->minimum>0 && list->navigation.selected>0 &&
       list->navigation.selected<=list->navigation.count) {
        fm_marks_key(marks,list->navigation.selected,list->navigation.count,44);
        n=1;
    }
    if(n<t->minimum) return reject(ops,"Please select one file");
    if(n>t->maximum) return reject(ops,"Too many files selected");
    used=0;arguments[0]=0;
    if(!append(arguments,&used,prefix)) goto longline;
    first=1;
    if(t->mode!=1) for(i=0;i<list->navigation.count;++i) {
        if(!marks->value[i]) continue;
        for(k=0;k<filecount;++k) if(list->names[i]==files[k].name) break;
        if(k==filecount || files[k].directory)
            return reject(ops,"Please select files, not directories");
        if(!filename(files[k].name,name))
            return reject(ops,"Name is too long, or invalid");
        if(!append(arguments,&used,first?t->first:t->between) ||
           !append(arguments,&used,name)) goto longline;
        first=0;
    }
    if(!append(arguments,&used,t->after) ||
       !append(arguments,&used,t->tail)) goto longline;
    used=0;command[0]=0;
    if(!append(command,&used,t->exe)) goto longline;
    if(arguments[0] && (!append(command,&used," ") ||
       !append(command,&used,arguments))) goto longline;
    if(t->mode==2) {
        /* RUNMENU advances beyond ! before running each command, and
         * continues even after loader failure. Only these known records
         * are split: selected names cannot contain an exclamation mark.
         * Check the complete original command above before either launch.
         */
        used=0;command[0]=0;
        if(!append(command,&used,"SETUP.CMD ") ||
           !append(command,&used,arguments+7)) goto longline;
        result=(*ops->invoke)(t->exe)==1;
        if((*ops->invoke)(command)!=1) result=0;
        if(!result) return 0;
    } else if((*ops->invoke)(command)!=1) return 0;
    /* Original Help returns its incoming selection count unchanged. */
    if(t->mode!=1) fm_marks_clear(marks);
    return 1;
longline:
    return reject(ops,"Too many files selected");
}

int fm_external(index,list,files,filecount,marks,ops)
int index,filecount;
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
struct fm_runner *ops;
{
    struct tool *t;
    if(!ops || !ops->invoke || !ops->report) return -1;
    t=find(index);
    if(!t) return reject(ops,"External operation is not available");
    if(t->mode==3)
        return reject(ops,"This operation requires its original setup workflow");
    return execute(t,list,files,filecount,marks,ops,t->prefix);
}
int fm_external_boot(list,files,filecount,marks,ask,ops)
int filecount;
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int (*ask)();
struct fm_runner *ops;
{
    char answer[6],*prefix;
    int i,r;
    if(!ask || !ops || !ops->invoke || !ops->report) return -1;
    for(;;) {
        for(i=0;i<6;++i) answer[i]=0;
        r=(*ask)(answer);
        if(r<0) return -1;
        if(!r || !answer[0]) return 0;
        answer[5]=0;
        for(i=0;answer[i];++i)
            if(answer[i]>='a' && answer[i]<='z') answer[i]-='a'-'A';
        if(answer[0]=='D' && answer[1]=='O' && answer[2]=='S' && !answer[3]) {
            prefix="[F5,F6,F0,F0]";break;
        }
        if(answer[0]=='C' && answer[1]=='P' && answer[2]=='/' &&
           answer[3]=='M' && !answer[4]) {
            prefix="[F5,F4,F0,F0]";break;
        }
    }
    return execute(find(25),list,files,filecount,marks,ops,prefix);
}
