/* CHKDOSFS -- native FAT checker, C recreation of DOS Plus CHKDSK.
 * F permits confirmed size/EOF correction and lost-chain recovery/release.
 * Cross-links, conflicting FAT copies and uncertain ownership block writes.
 */
#include <stdio.h>
#include "chkdosfs.h"
unsigned OSCALL();
int verbose,repair,wrote;

static upper(c)
int c;
{ return c>='a' && c<='z' ? c-32 : c; }

static usage()
{
    printf("USAGE: CHKDOSFS drive: [FV]\n");
    printf("  drive: A:..P:\n");
    printf("  F      repair\n");
    printf("  V      verbose\n");
    return 0;
}

/* Return 1 for supported options, -1 for recognized but not
 * implemented options, and 0 for malformed input. Do not accept a trailing
 * suffix after ], or silently treat a bare option introducer as success.
 */
static options(s)
char *s;
{
    char token[16];
    int i,c,bracket,pending;
    bracket=*s=='['; s++; i=pending=0;
    while(*s && *s!=']' && i<15) token[i++]=upper(*s++);
    token[i]=0;
    if(!i || (*s && (!bracket || *s!=']' || s[1]))) return 0;
    for(i=0;token[i];i++) {
        c=token[i];
        if(c=='V') verbose=1;
        else if(c=='F') repair=1;
        else return 0;
    }
    return pending ? -1 : 1;
}

main(argc,argv)
int argc;
char **argv;
{
    int drive,status,opt;
    char *s;
    status=0;
    printf("CHKDOSFS 0.1 - FAT FILESYSTEM CHECK\n");
    if(argc==1) { usage(); OSCALL(108,2); return 2; }
    s=argv[1];
    if(!s[0] || s[1]!=':' || s[2] || upper(s[0])<'A' ||
       upper(s[0])>'P') {
        printf("ERROR: Invalid command line.\n");
        usage(); OSCALL(108,2); return 2;
    }
    drive=upper(s[0])-'A';
    if(argc>2) {
        s=argv[2];
        opt=0;
        if(argc==3 && (s[0]=='/' || s[0]=='[')) opt=options(s);
        if(opt!=1) {
            if(opt<0) printf("ERROR: Requested option is not implemented yet.\n");
            else printf("ERROR: Invalid command option.\n");
            usage(); OSCALL(108,2); return 2;
        }
    }
    if(!diskopen(drive)) { OSCALL(108,2); return 2; }
    printf("Drive %c  FAT%u  data clusters %u\n",
           'A'+drive,vol.fat16 ? 16 : 12,vol.limit-2);
    if(!fscheck()) {
        printf("ERROR: Scan incomplete; no changes written.\n"); status=2;
    } else if(errors) status=1;
    if(repair && !failed && !repairfs()) status=2;
    else if(repair && !failed && !errors) status=0;
    diskclose();
    OSCALL(108,status);
    return status;
}

/* Direct console input permits cancellation without the BDOS Ctrl-C abort
 * path bypassing MXdisk cleanup. Yield when no character is available. */
confirm()
{
    unsigned c;
    do {
        c=OSCALL(6,255)&255;
        if(!c) OSCALL(142,0);
    } while(!c);
    OSCALL(2,c); OSCALL(2,13); OSCALL(2,10);
    return c=='Y' || c=='y';
}
