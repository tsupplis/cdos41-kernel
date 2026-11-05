#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "backup.h"
#include "fatdest.h"
#include "copyio.h"
static char *error;
static char *header[]={
 "CLEAR: 2,27,69\r\n",
 "ATTRIBUTE: start screen: 9,27,99,0,27,97,3,27,98,2\r\n",
 "ATTRIBUTE: leave screen: 3,27,98,7\r\n",
 "ATTRIBUTE: general: 3,27,98,2\r\n",
 "ATTRIBUTE: errors: 3,27,98,15\r\n",
 "ATTRIBUTE: message: 3,27,98,14\r\n",
 "ATTRIBUTE: data: 3,27,98,3\r\n",
 "ATTRIBUTE: input: 3,27,98,12\r\n",
 "PRINTER INIT: 1,13\r\n","FORMFEED: 1,12\r\n",
 "LENGTH: 60\r\n","WIDTH: 80\r\n","REPORT PRINT: true\r\n",
 "SHOW SKIPS: true\r\n","ID:Concurrent DOS Hard Disk Backup\r\n",
 "SPLIT: true\r\n","ERASE: true\r\n",0
};
char *fm_backup_error() { return error?error:""; }
static int emit(s,put)
char *s;int (*put)();
{
 while(*s) if((*put)(*s++ & 255)!=1) return 0;
 return 1;
}
static int namevalid(s)
char *s;
{
 int i,c,base,ext,dot,gap;
 base=ext=dot=gap=0;
 for(i=0;i<FM_NAME_SIZE && s[i];++i) {
  c=s[i]&255;
  if(c==' ') {gap=1;continue;}
  if(gap || i>=12 || c<33 || c>126 || c==':' || c=='/' ||
     c=='\\' || c=='*' || c=='?' || c==';' || c==',' || c=='=' ||
     c=='<' || c=='>' || c=='|' || c=='"' || c=='[' || c==']' || c=='!') return 0;
  if(c=='.') {if(dot || !base)return 0;dot=1;}
  else if(dot) {if(++ext>3)return 0;}
  else if(++base>8)return 0;
 }
 return i<FM_NAME_SIZE && base && (!dot || ext);
}
int fm_backup_control(list,files,filecount,marks,source,user,fat,path,destination,whole,put)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,source,user,fat,destination,whole;
char *path;
int (*put)();
{
 int i,k,n;
 char letter[4],rule[14];
 error="Invalid backup settings";
 if(!put || source<1 || source>16 || user<0 || user>15 ||
    destination<1 || destination>2 || (fat!=0 && fat!=1) ||
    (whole!=0 && whole!=1)) return 0;
 if(fat) {
  if(!path || !*path) return 0;
  for(i=0;i<128 && path[i];++i)
   if((path[i]&255)<32 || (path[i]&255)>126) return 0;
  if(i==128) return 0;
 }
 error="Invalid file selection";
 if(!list || !marks || filecount<0 || filecount>256 ||
    (filecount && !files) || list->navigation.count<0 ||
    list->navigation.count>256 || (list->navigation.count && !list->names)) return 0;
 n=0;
 if(!whole) for(i=0;i<list->navigation.count;++i) {
  if(!marks->value[i]) continue;
  ++n;
  for(k=0;k<filecount;++k) if(list->names[i]==files[k].name) break;
  if(k==filecount || files[k].directory || !namevalid(files[k].name)) return 0;
 }
 if(!whole && !n) {error="No files selected for Backup";return 0;}
 error="Cannot write backup control file";
 for(i=0;header[i];++i) if(!emit(header[i],put)) return 0;
 letter[0]='A'+destination-1;letter[1]='\r';letter[2]='\n';letter[3]=0;
 if(!emit("DEST DRIVE: ",put) || !emit(letter,put)) return 0;
 letter[0]='A'+source-1;
 if(!emit("SOURCE: ",put) || !emit(letter,put) ||
    !emit("CONTROL DRIVE: ",put) || !emit(letter,put)) return 0;
 if(fat) {
  if(!emit("PATH: ",put) || !emit(path,put) || !emit("\r\n",put)) return 0;
 } else if(!emit("USERS: 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15\r\n",put)) return 0;
 if(!emit("EXC:  ?,?,c,k,control?.br\r\n",put) ||
    !emit("EXC:  ?,?,n,k,*.br?\r\n",put)) return 0;
 /* Right-aligned two-character user field, or literal space-D for FAT. */
 rule[0]='E';rule[1]='X';rule[2]='C';rule[3]=':';rule[4]=' ';
 rule[5]=fat || user<10 ? ' ' : '1';
 rule[6]=fat ? 'D' : '0'+user%10;
 rule[7]=',';rule[8]='A'+source-1;rule[9]=',';
 rule[10]='a';rule[11]=',';rule[12]='k';rule[13]=0;
 if(whole) {
  if(!emit(rule,put) || !emit(",*.*\r\n",put)) return 0;
 } else for(i=0;i<list->navigation.count;++i) {
  if(!marks->value[i]) continue;
  if(!emit(rule,put) || !emit(",",put) ||
     !emit(list->names[i],put) || !emit("\r\n",put)) return 0;
 }
 if(!emit("EXC:  ?,?,n,k,*.*\r\n",put)) return 0;
 error="";return 1;
}

/* Backup control output uses the existing transactional copy commit. Original
 * CODE51F7/5241 roots and restores the physical source through public BDOS.
 */
char *strcpy();
int BDOS(),FMLOC(),XINIT(),FARWORD();
extern unsigned short XDATA;
static char *backup_io_error;
static char backup_record[128],backup_fcb[36];
static int backup_used;
char *fm_backup_io_error() {return backup_io_error?backup_io_error:"";}
int fm_native_permanent(drive,fat)
int drive,fat;
{
    int loc[4];unsigned dph,dpb;
    if(drive<1 || drive>16 || (fat!=0 && fat!=1) ||
       (BDOS(12,0)&65535)!=0x1441) return -1;
    loc[0]=drive;
    if(fat && !FMLOC(drive,loc)) return -1;
    if(loc[0]<1 || loc[0]>13) return -1;
    XINIT();dph=FARWORD(XDATA,0xc18+2*(loc[0]-1));
    if(!dph || dph>65525) return -1;
    dpb=FARWORD(XDATA,dph+8);
    if(!dpb || dpb>65510) return -1;
    if((unsigned)FARWORD(XDATA,dpb)>=65520) dpb+=12;
    return (FARWORD(XDATA,dpb+11)&32768)!=0;
}
static int backup_init(fcb,drive,name)
char *fcb,*name;int drive;
{
    int i;for(i=0;i<36;++i)fcb[i]=0;
    fcb[0]=drive;for(i=0;i<11;++i)fcb[i+1]=name[i];return 0;
}
static int backup_probe(c)
int c;
{return 1;}
static int backup_put(c)
int c;
{
    backup_record[backup_used++]=c;
    if(backup_used==128) {
        BDOS(26,backup_record);
        if((BDOS(21,backup_fcb)&255)!=0)return 0;
        backup_used=0;
    }
    return 1;
}
static int backup_enter(drive,path)
int drive;char *path;
{
    char fcb[36];int p,i,n,ext,c;
    p=3;
    while(path[p]) {
        for(i=0;i<36;++i)fcb[i]=0;
        for(i=1;i<12;++i)fcb[i]=' ';
        fcb[0]=drive|128;n=1;ext=0;
        while(path[p] && path[p]!='\\') {
            c=path[p++];
            if(c=='.') {if(ext)return 0;ext=1;n=9;continue;}
            if((!ext && n>8) || n>11)return 0;
            fcb[n++]=c;
        }
        if((BDOS(15,fcb)&255)!=0)return 0;
        if(path[p])++p;
    }
    return 1;
}
int fm_backup_run(list,files,count,marks,source,user,fat,dest,whole,restore,dma,invoke)
struct fm_browser *list;struct fm_file *files;struct fm_marks *marks;
int count,source,user,fat,dest,whole,restore;
char *dma;int (*invoke)();
{
    char path[68],oldpath[68],name[11],raw[32],target[32],fcb[36],command[32];
    int loc[4],physical,root,entryuser,entrydrive,i,n,r,opened,ownedfile,moved,result;
    backup_io_error="Invalid Backup request";
    if(!dma || !invoke || source<1 || source>16 || user<0 || user>15 ||
       (fat!=0 && fat!=1) || (restore!=0 && restore!=1)) return 0;
    entryuser=BDOS(32,255)&255;entrydrive=BDOS(25,0)&255;
    opened=ownedfile=moved=0;result=-1;path[0]=oldpath[0]=0;
    backup_io_error="Select a hard disk drive to backup or restore";
    if(fm_native_permanent(source,fat)!=1) {result=0;goto done;}
    physical=source;root=source;
    if(fat) {
        if(!FMLOC(source,loc)) goto done;
        physical=loc[0];root=fm_fat_root(source,path,sizeof(path),dma);
        if(!root){backup_io_error=fm_fat_destination_error();goto done;}
        /* Physical mapping may differ from a floating source. Its path must
         * be saved independently before the launch roots the physical drive. */
        if(source==physical) {
            for(i=0;path[i];++i)oldpath[i]=path[i];oldpath[i]=0;
        } else {
            root=fm_fat_root_protected(physical,oldpath,sizeof(oldpath),dma,source);
            if(!root){backup_io_error=fm_fat_destination_error();goto done;}
        }
    }
    if(!restore && !fm_backup_control(list,files,count,marks,physical,user,fat,path,dest,whole,backup_probe)) {
        backup_io_error=fm_backup_error();result=0;goto done;
    }
    BDOS(32,0);
    if(!restore) {
        backup_io_error="Cannot create Backup control staging file";
        for(n=0;n<256;++n) {
            for(i=0;i<11;++i)name[i]=' ';
            name[0]='F';name[1]='M';name[2]='B';
            name[3]='0'+n/100;name[4]='0'+n/10%10;name[5]='0'+n%10;
            name[8]=name[9]=name[10]='$';
            backup_init(fcb,root,name);BDOS(26,backup_record);r=BDOS(17,fcb);
            if((r&65535)==255)break;
            if((r&255)==255)goto done;
        }
        if(n==256)goto done;
        backup_init(backup_fcb,root,name);
        if((BDOS(22,backup_fcb)&255)==255)goto done;
        opened=ownedfile=1;backup_used=0;
        backup_io_error="Cannot write Backup control file";
        if(!fm_backup_control(list,files,count,marks,physical,user,fat,path,dest,whole,backup_put))goto done;
        if(backup_used)while(backup_used)if(!backup_put(26))goto done;
        if((BDOS(16,backup_fcb)&255)==255)goto done;
        opened=0;
        for(i=0;i<32;++i)raw[i]=target[i]=0;
        for(i=0;i<11;++i)raw[i+1]=name[i];
        for(i=1;i<12;++i)target[i]=' ';
        target[1]='C';target[2]='O';target[3]='N';target[4]='T';
        target[5]='R';target[6]='O';target[7]='L';target[8]='A'+physical-1;
        target[9]='B';target[10]='R';
        backup_io_error="Cannot commit Backup control file";
        if(fm_copy_users(root,0,raw,root,0,target,dma,0)!=1)goto done;
        backup_init(fcb,root,name);
        if((BDOS(19,fcb)&255)==255)goto done;
        ownedfile=0;
    }
    if(fat) {
        backup_init(fcb,physical,".          ");fcb[0]|=128;
        moved=1;backup_io_error="Cannot root Backup source";
        if((BDOS(16,fcb)&255)==255)goto done;
    }
    if((BDOS(14,physical-1)&255)==255)goto done;
    BDOS(32,0);BDOS(26,dma);
    strcpy(command,restore ? "REST.CMD CTL=A" : "BACK.CMD CTL=A");
    command[12]='A'+physical-1;
    backup_io_error="Backup or Restore command failed";
    result=(*invoke)(command)?1:0;
done:
    if(opened){BDOS(32,0);if((BDOS(16,backup_fcb)&255)==255)result=-1;}
    if(ownedfile){backup_init(fcb,root,name);BDOS(32,0);if((BDOS(19,fcb)&255)==255)result=-1;}
    if(moved) {
        backup_init(fcb,physical,".          ");fcb[0]|=128;
        r=BDOS(16,fcb)&255;
        if(r==255 || !backup_enter(physical,oldpath)) {
        backup_io_error="Cannot restore source directory after Backup";result=-2;
        }
    }
    if((BDOS(14,entrydrive)&255)==255) {
        backup_io_error="Cannot restore current drive after Backup";result=-2;
    }
    BDOS(32,entryuser);BDOS(26,dma);
    if(result==1)backup_io_error="";
    return result;
}
