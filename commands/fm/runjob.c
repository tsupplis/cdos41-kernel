/* Run CODE 59DD: one concrete executable, with original type diagnostic.
 * The invocation mechanism and screen ownership belong to the caller.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "runjob.h"
static int reject(ops,message)
struct fm_runner *ops;
char *message;
{ return (*ops->report)(message) ? 0 : -1; }
int fm_run_file(list,files,filecount,marks,drive,ops)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,drive;
struct fm_runner *ops;
{
    char command[15];
    int i,j,k,n,length,base,ext,dot,c,gap;
    if(!ops || !ops->invoke || !ops->report) return -1;
    if(!list || !files || !marks || drive<1 || drive>16 ||
       filecount<0 || filecount>256 || list->navigation.count<0 ||
       list->navigation.count>256 || !list->names)
        return reject(ops,"Please select one file");
    n=0;j=-1;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) {++n;j=i;}
    if(!n && list->navigation.selected>0 &&
       list->navigation.selected<=list->navigation.count) {
        j=list->navigation.selected-1;n=1;
    }
    if(n!=1) return reject(ops,"Please select one file");
    fm_marks_key(marks,j+1,list->navigation.count,44);
    for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
    if(k==filecount || files[k].directory)
        return reject(ops,"Please select one file");
    command[0]='A'+drive-1;command[1]=':';
    base=ext=dot=gap=length=0;
    for(i=0;i<FM_NAME_SIZE && files[k].name[i];++i) {
        c=files[k].name[i]&255;
        if(c==' ') {gap=1;continue;}
        if(gap || i>=12 || c<33 || c>126 || c==':' || c=='/' ||
           c=='\\' || c=='*' || c=='?' || c==';' || c==',' ||
           c=='=' || c=='<' || c=='>' || c=='|' || c=='"' ||
           c=='[' || c==']')
            return reject(ops,"Name is too long, or invalid");
        if(c>='a' && c<='z') c=c-'a'+'A';
        if(c=='.') {
            if(dot || !base) return reject(ops,"Name is too long, or invalid");
            dot=1;
        } else if(dot) {
            if(++ext>3) return reject(ops,"Name is too long, or invalid");
        } else if(++base>8) return reject(ops,"Name is too long, or invalid");
        command[length+2]=c;++length;
    }
    if(i==FM_NAME_SIZE || !base || (dot && !ext))
        return reject(ops,"Name is too long, or invalid");
    command[length+2]=0;
    if(ext!=3 || !((command[length-1]=='C' && command[length]=='M' && command[length+1]=='D') ||
                  (command[length-1]=='C' && command[length]=='O' && command[length+1]=='M') ||
                  (command[length-1]=='E' && command[length]=='X' && command[length+1]=='E') ||
                  (command[length-1]=='B' && command[length]=='A' && command[length+1]=='T')))
        return reject(ops,"Bad file type, only .CMD, .COM, .EXE, or .BAT files ");
    if((*ops->invoke)(command)!=1) return 0;
    fm_marks_clear(marks);
    return 1;
}
