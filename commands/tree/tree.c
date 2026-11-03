/* TREE - DOS Plus-style directory statistics for Concurrent DOS.
 * Native BDOS directory mapping keeps traversal private to this process.
 * Each row counts immediate regular files and their logical byte lengths;
 * children are listed depth first in on-disk order, not added to parents.
 */
unsigned OSCALL();
static char fcb[36], dma[128];
static char pathname[68], childname[13];
static unsigned nextchild[33], pathend[33];
static int drive, failed;

static text(s)
char *s;
{
    while (*s) __BDOS(2,*s++ & 255);
}
static line(s)
char *s;
{
    text(s); text("\r\n");
}
static upper(c)
int c;
{
    return c>='a' && c<='z' ? c-32 : c;
}
static clearfcb(name, special)
char *name;
int special;
{
    int i,j,dots;
    dots=name[0]=='.' && (!name[1] || (name[1]=='.' && !name[2]));
    for (i=0;i<36;i++) fcb[i]=0;
    fcb[0]=drive+1+(special ? 128 : 0);
    for (i=1;i<12;i++) fcb[i]=' ';
    i=1;
    while (*name && i<12) {
        if (*name=='.' && i>1) { i=9; name++; }
        else fcb[i++]=upper(*name++);
    }
    /* Dot and dot-dot are literal directory names, not extensions. */
    if (special && dots) {
        for (j=1;j<12;j++) fcb[j]=' ';
        fcb[1]='.';
        if (i>2) fcb[2]='.';
    }
}
static change(name)
char *name;
{
    clearfcb(name,1);
    return (OSCALL(15,fcb)&255)==0;
}
/* The native DIR command requests the media label with drive '?'. FAT
 * supplies a synthetic label even on an unnamed/empty volume. This public
 * search convention also works for mapped drives, without XIOS offsets.
 */
static fatmedia()
{
    int i;
    clearfcb("",0);
    for(i=0;i<128;i++) dma[i]=0;
    fcb[0]='?';
    __BDOS(26,dma);
    OSCALL(17,fcb);
    return (dma[0]&255)==32 && (dma[15]&255)==128;
}
static first(dirs)
int dirs;
{
    int i;
    clearfcb("",dirs);
    for(i=1;i<12;i++) fcb[i]='?';
    __BDOS(26,dma);
    return OSCALL(17,fcb)&255;
}
static next()
{
    return OSCALL(18,fcb)&255;
}
static isdir(e)
char *e;
{
    return !(e[0]&16) && e[16]==e[17] && (e[16]&192)==192;
}
static regular(e)
char *e;
{
    return e[0]<16 && e[1]!='.';
}
static namecopy(e)
char *e;
{
    int i,j;
    j=0;
    for(i=1;i<9 && (e[i]&127)!=' ';i++) childname[j++]=e[i]&127;
    if ((e[9]&127)!=' ') {
        childname[j++]='.';
        for(i=9;i<12 && (e[i]&127)!=' ';i++) childname[j++]=e[i]&127;
    }
    childname[j]=0;
}
/* Re-scan after a child: BDOS search state is not recursive. No directory
 * list or open file survives descent, so very wide directories use no heap.
 */
static child(number)
unsigned number;
{
    int slot;
    char *e;
    for(slot=first(1);slot!=255;slot=next()) {
        e=dma+32*slot;
        if(regular(e) && isdir(e)) {
            if(!number--) { namecopy(e); return 1; }
        }
    }
    return 0;
}
/* Decimal division uses two 16-bit limbs: DR C has no unsigned long. */
static number(low,high,width)
unsigned low,high;
int width;
{
    char digits[16];
    int i,n;
    long rest;
    i=0;n=0;
    do {
        if(n && n%3==0) digits[i++]=',';
        rest=(long)(high%10)*65536L+low;
        digits[i++]=(int)(rest%10L)+'0';
        high/=10;low=(unsigned)(rest/10L);n++;
    } while(low || high);
    for(n=i;n<width;n++) text(" ");
    while(i) __BDOS(2,digits[--i]);
}
static statistics()
{
    unsigned low,high,old,add,carry,files;
    char *e;
    int slot;
    low=high=files=0;
    for(slot=first(0);slot!=255;slot=next()) {
        e=dma+32*slot;
        if(regular(e) && !isdir(e)) {
            add=(e[28]&255) | ((unsigned)(e[29]&255)<<8);
            old=low;low+=add;carry=low<old;
            add=(e[30]&255) | ((unsigned)(e[31]&255)<<8);
            old=high;high+=add;
            if(high<old || (carry && high==65535)) {
                line("TREE: directory size exceeds 32 bits.");failed=1;return;
            }
            high+=carry;files++;
        }
    }
    number(low,high,12);text(" ");number(files,0,6);text("  ");line(pathname);
}
main(argc,argv)
int argc;
char **argv;
{
    int depth,i,n,old;
    unsigned version;
    if(argc>1 && (!strcmp(argv[1],"[HELP]") || !strcmp(argv[1],"/?"))) {
        line("TREE {d:}");line("List FAT directories, immediate file counts and byte sizes.");return;
    }
    drive=__BDOS(25,0);
    if(argc>2 || (argc==2 && (strlen(argv[1])!=2 || argv[1][1]!=':' ||
       upper(argv[1][0])<'A' || upper(argv[1][0])>'P'))) {
        line("Usage: TREE {d:}");return;
    }
    version=OSCALL(12,0);
    if((version&0xfd00)==0x1400 && (version&255)>=0x41) {
        if(argc==2) drive=upper(argv[1][0])-'A';
        old=__BDOS(25,0);
        if((OSCALL(14,drive)&255) || !fatmedia()) {
            __BDOS(14,old);line("TREE requires a DOS/FAT disk.");return;
        }
    } else { line("TREE requires Concurrent DOS 4.1.");return; }
    clearfcb("",1);
    if(OSCALL(16,fcb)&255) { line("TREE: cannot open root directory.");return; }
    pathname[0]='A'+drive;pathname[1]=':';pathname[2]='\\';pathname[3]=0;
    depth=0;nextchild[0]=0;pathend[0]=3;
    line("       Space  Files  Path Name");
    statistics();
    while(!failed) {
        if(child(nextchild[depth]++)) {
            n=strlen(childname);
            i=strlen(pathname);
            if(depth==32 || i+n+(depth!=0)>=68) {
                line("TREE: path exceeds 67 characters.");failed=1;break;
            }
            if(!change(childname)) { line("TREE: cannot enter directory.");failed=1;break; }
            if(depth) pathname[i++]='\\';
            strcpy(pathname+i,childname);
            depth++;nextchild[depth]=0;pathend[depth]=strlen(pathname);
            statistics();
        } else {
            if(!depth) break;
            if(!change("..")) { line("TREE: cannot return to parent.");break; }
            depth--;pathname[pathend[depth]]=0;
        }
    }
    __BDOS(14,old);
}
