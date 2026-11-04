/* CHKDOSFS -- native FAT checker, C recreation of DOS Plus CHKDSK.
 * Initial milestone: read-only checks. Recovery switches are rejected before
 * any drive is selected. Do not confuse this build with full CHKDSK parity.
 */
#include <stdio.h>
#include "chkdosfs.h"
unsigned OSCALL();
int verbose;

static upper(c)
int c;
{ return c>='a' && c<='z' ? c-32 : c; }

static usage()
{
    printf("USAGE: CHKDOSFS drive: [FV]\n");
    printf("  drive: A:..P:\n");
    printf("  F      repair (not implemented)\n");
    printf("  V      verbose (not implemented)\n");
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
        if(c=='V') pending=1;
        else if(c=='F' || c=='D' || c=='L' || c=='R' || c=='B') pending=1;
        else return 0;
    }
    return pending ? -1 : 1;
}

main(argc,argv)
int argc;
char **argv;
{
    int i,n,drives[16],status,opt;
    char *s;
    n=status=0;
    printf("CHKDOSFS 0.1 - READ-ONLY FAT FILESYSTEM CHECK\n");
    for(i=1;i<argc;i++) {
        s=argv[i];
        if(s[0]=='/' || s[0]=='[') {
            opt=options(s);
            if(opt==1) continue;
            if(opt<0) printf("ERROR: Requested option is not implemented yet.\n");
            else printf("ERROR: Invalid command option.\n");
            usage(); OSCALL(108,2); return 2;
        } else if(s[0] && s[1]==':' && !s[2] && upper(s[0])>='A' &&
                  upper(s[0])<='P' && n<1) drives[n++]=upper(s[0])-'A';
        else {
            printf("ERROR: Invalid command line.\n");
            usage(); OSCALL(108,2); return 2;
        }
    }
    if(!n) { usage(); OSCALL(108,2); return 2; }
    for(i=0;i<n;i++) {
        if(!diskopen(drives[i])) { status=2; continue; }
        printf("Drive %c  FAT%u  data clusters %u\n",
               'A'+drives[i],vol.fat16 ? 16 : 12,vol.limit-2);
        if(!fscheck()) {
            printf("ERROR: Scan incomplete; no changes written.\n"); status=2;
        } else if(errors && !status) status=1;
        diskclose();
    }
    OSCALL(108,status);
    return status;
}
