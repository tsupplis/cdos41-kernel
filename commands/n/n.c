/* Interactive CDOS national installation utility. All menu text after the
   language choice comes from the selected directory in NATIONAL.MSG. */
long lseek();
static int language, keyboard;
static char models[5], *catalog;
static int catalog_size;
static char *languages[] = {"English, US","Fran\207ais","Deutsch","English, UK",
    "Danmark","Norge","Sverige/Suomi","Italiano","Espa\244ol","<EXIT>"};
static int lang_index[] = {0,1,2,3,4,8,5,6,7};
static int model_msg[] = {20,21,34,22,23,35};
unsigned OSVERS();
char *malloc();
static char *title = "Concurrent PC DOS National Setup Utility for the IBM PC  version 4.1";

static emit_char(c)
int c;
{
    __BDOS(2,c);
}
static text(s)
char *s;
{
    while (*s) emit_char(*s++ & 255);
}
static position(y,x)
int y,x;
{
    text("\033Y"); emit_char(32+y); emit_char(32+x);
}
static row(y)
int y;
{
    position(y,2);
}
static char *msg(n)
int n;
{
    int i;
    unsigned off;
    i = 128 + 200*language + 2*n;
    if (i+1 < catalog_size) {
        off = (catalog[i]&255) | ((unsigned)catalog[i+1]<<8);
        if (off < catalog_size-128) return catalog+128+off;
    }
    text("Invalid NATIONAL.MSG"); exit(1);
    return "";
}
static repeat(c,n)
int c,n;
{
    while (n-- > 0) emit_char(c);
}
static center(y,s)
int y;
char *s;
{
    position(y,40-strlen(s)/2); text(s);
}
static rule(y,left,line,right)
int y,left,line,right;
{
    position(y,0); emit_char(left); repeat(line,78); emit_char(right);
}
static frame(heading)
char *heading;
{
    int y;
    text("\033q\033f\033w\033E");
    rule(0,0xda,0xc4,0xbf);
    for (y=1;y<23;y++) {
        position(y,0); emit_char(0xb3);
        position(y,79); emit_char(0xb3);
    }
    rule(2,0xc6,0xcd,0xb5);
    rule(23,0xc0,0xc4,0xd9);
    text("\033v"); center(1,title);
    text("\033p"); center(4,heading); text("\033q");
}
static choice_row(y,s,width,selected)
int y,width,selected;
char *s;
{
    int len;
    len=strlen(s);
    position(y,40-width);
    if (selected) text("\033p");
    text(" o "); repeat(' ',width-3-len/2); text(s);
    repeat(' ',width-len+len/2);
    if (selected) text("\033q");
}
/* One highlighted option; arrows and space wrap, Escape selects the last
   (Back/Discard) entry, just as in the release menu dispatcher. */
static menu(heading, items, count, current)
char *heading, **items;
int count,current;
{
    int i,key,width,length,old;
    width=0;
    for (i=0;i<count;i++) {
        length=strlen(items[i]);
        if (length>width) width=length;
    }
    width=(width+10)/2;
    frame(heading);
    if ((count==6 && heading==msg(6)) || count==7) {
        row(6); text(msg(26)); text(items[current]);
    }
    if (count != 10) { center(8,msg(36)); center(9,msg(37)); }
    for (i=0;i<count;i++) choice_row(11+i,items[i],width,i==current);
    for (;;) {
        old=current;
        key=__BDOS(6,253)&255;
        if (key==13) return current;
        if (key==27) return count-1;
        if (key==0xc8 || key==0xcb || key=='8' || key=='4')
            current=(current+count-1)%count;
        else if (key==0xd0 || key==0xcd || key=='2' || key=='6' || key==' ')
            current=(current+1)%count;
        else continue;
        choice_row(11+old,items[old],width,0);
        choice_row(11+current,items[current],width,1);
    }
}
static install(fd,mfd)
int fd,mfd;
{
    char *items[8];
    int i,option,device,model,ok;
    option=0;
    for (;;) {
        for (i=0;i<4;i++) items[i]=msg(2+i);
        option=menu(msg(1),items,4,option);
        if (option==3) break;
        if (option==0) {
            for (i=0;i<5;i++) items[i]=msg(7+i);
            items[5]=msg(18);
            i=menu(msg(6),items,6,keyboard);
            if (i<5) keyboard=i;
        } else if (option==1) {
            device=0;
            for (;;) {
                for (i=0;i<6;i++) items[i]=msg(13+i);
                device=menu(msg(12),items,6,device);
                if (device==5) break;
                for (i=0;i<6;i++) items[i]=msg(model_msg[i]);
                items[6]=msg(18);
                model=menu(msg(19),items,7,models[device]);
                if (model<6) models[device]=model;
            }
        } else {
            frame(msg(4)); row(6); text(msg(24)); text(msg(7+keyboard));
            row(8); text(msg(25));
            for (i=0;i<5;i++) {
                row(10+i); text(msg(13+i)); text(" = "); text(msg(model_msg[models[i]]));
            }
            row(18); text(msg(18)); __BDOS(6,253);
        }
        option=(option+1)%4;
    }
    items[0]=msg(33); items[1]=msg(32);
    if (menu(msg(31),items,2,0)==1) return 1;
    text("\033E"); text(msg(27));
    ok=set_choice(fd,mfd,keyboard,language,models);
    return ok;
}
static load_settings(fd)
int fd;
{
    unsigned paras,sig,dir,slot;
    char records[55],key;
    long base;
    int i;
    if (!word_at(fd,1L,&paras)) return 0;
    base=128L+16L*paras;
    if (!word_at(fd,base+0xc3cL,&sig) || sig!=0x574a ||
        !word_at(fd,base+0xc3eL,&dir) || !dir ||
        !word_at(fd,base+dir+4,&slot) || !slot ||
        lseek(fd,base+slot,0)!=base+slot || read(fd,&key,1)!=1 ||
        (key&255)>4) return 0;
    keyboard=key;
    if (!word_at(fd,base+dir+20,&slot) || !slot ||
        lseek(fd,base+slot,0)!=base+slot || read(fd,records,55)!=55) return 0;
    for (i=0;i<5;i++) {
        models[i]=records[i*11+1];
        if ((models[i]&255)>5) return 0;
    }
    return 1;
}
static finish(status)
int status;
{
    text("\0337\033e\033q"); exit(status);
}
main()
{
    int fd,mfd,i,ok;
    if (OSVERS() != 0x1441) {
        text("Requires Concurrent PC DOS"); exit(1);
    }
    __BDOS(110,0);
    __BDOS(109,__BDOS(109,65535)|14);
    text("\0336");
    i=menu("Select your language:",languages,10,0);
    if (i==9) { text("\033E"); finish(0); }
    language=lang_index[i];
    mfd=openb("NATIONAL.MSG",0);
    if (mfd<0) mfd=openb("P:NATIONAL.MSG",0);
    if (mfd<0) { text("\033EMissing NATIONAL.MSG"); finish(1); }
    catalog=malloc(20480);
    if (!catalog) { text("Insufficient memory"); finish(1); }
    catalog_size=read(mfd,catalog,20479);
    if (catalog_size<=0) { text("Cannot read NATIONAL.MSG"); finish(1); }
    catalog[catalog_size]=0;
    fd=openb("CCPM.SYS",2);
    if (fd<0) fd=openb("P:CCPM.SYS",2);
    if (fd<0) { text(msg(29)); finish(1); }
    if (!load_settings(fd)) { text(msg(30)); finish(1); }
    ok=install(fd,mfd);
    if (close(fd)<0) ok=0;
    close(mfd); text("\033E");
    if (!ok) text(msg(28));
    finish(!ok);
}
