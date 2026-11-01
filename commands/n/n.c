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
static row(y)
int y;
{
    text("\033Y"); emit_char(32+y); emit_char(34);
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
/* One highlighted option; arrows and space wrap, Escape selects the last
   (Back/Discard) entry, just as in the release menu dispatcher. */
static menu(heading, items, count, current)
char *heading, **items;
int count,current;
{
    int i,key;
    int initial;
    initial=current;
    text("\033E"); row(1); text(title); row(4); text(heading);
    if ((count==6 && heading==msg(6)) || count==7) {
        row(5); text(msg(26)); text(items[initial]);
    }
    if (count != 10) { row(6); text(msg(36)); row(7); text(msg(37)); }
    for (;;) {
        for (i=0;i<count;i++) {
            row(9+i); text(i==current ? "\033p > " : "   ");
            text(items[i]); text("\033q");
        }
        key=__BDOS(6,253)&255;
        if (key==13) return current;
        if (key==27) return count-1;
        if (key==0xc8 || key==0xcb || key=='8' || key=='4')
            current=(current+count-1)%count;
        else current=(current+1)%count;
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
            text("\033E"); row(2); text(msg(24)); text(msg(7+keyboard));
            row(4); text(msg(25));
            for (i=0;i<5;i++) {
                row(6+i); text(msg(13+i)); text(" = "); text(msg(model_msg[models[i]]));
            }
            row(14); text(msg(18)); __BDOS(6,253);
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
main()
{
    int fd,mfd,i,ok;
    if (OSVERS() != 0x1441) {
        text("Requires Concurrent PC DOS"); exit(1);
    }
    i=menu("Select your language:",languages,10,0);
    if (i==9) { text("\033E"); exit(0); }
    language=lang_index[i];
    mfd=openb("NATIONAL.MSG",0);
    if (mfd<0) mfd=openb("P:NATIONAL.MSG",0);
    if (mfd<0) { text("\033EMissing NATIONAL.MSG"); exit(1); }
    catalog=malloc(20480);
    if (!catalog) { text("Insufficient memory"); exit(1); }
    catalog_size=read(mfd,catalog,20479);
    if (catalog_size<=0) { text("Cannot read NATIONAL.MSG"); exit(1); }
    catalog[catalog_size]=0;
    fd=openb("CCPM.SYS",2);
    if (fd<0) fd=openb("P:CCPM.SYS",2);
    if (fd<0) { text(msg(29)); exit(1); }
    if (!load_settings(fd)) { text(msg(30)); exit(1); }
    ok=install(fd,mfd);
    if (close(fd)<0) ok=0;
    close(mfd); text("\033E");
    if (!ok) text(msg(28));
    exit(!ok);
}
