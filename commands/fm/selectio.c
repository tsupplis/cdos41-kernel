/* Native selection services. Private DPH-table access is version guarded:
 * CDOS SYSDAT 0C18h holds 16 drive pointers (same walk as original 7034h).
 * All BDOS calls use the full-word bridge, never the byte-only C wrapper.
 */
#include "select.h"
extern unsigned short XDATA;
int BDOS(),XINIT(),FARWORD();
int fm_native_subset(text,mask)
char *text,*mask;
{
    char fcb[36],*packet[2];
    int i,length,wild;
    if(!text || !mask) return 0;
    for(length=0;text[length] && length<=12;++length) ;
    if(!length || length>12) return 0;
    for(i=0;i<36;++i) fcb[i]=0;
    packet[0]=text;packet[1]=fcb;
    if(BDOS(152,packet)==255) return 0;
    wild=0;
    for(i=1;i<12;++i) if(fcb[i]=='?') wild=1;
    if(!wild) return 0;
    for(i=0;i<11;++i) mask[i]=fcb[i+1]&127;
    return 1;
}
unsigned fm_native_drives()
{
    unsigned mask;
    int i;
    if((BDOS(12,0)&65535)!=0x1441) return 0;
    XINIT();mask=0;
    for(i=0;i<16;++i)
        if(FARWORD(XDATA,0xc18+2*i)) mask|=(unsigned)1<<i;
    return mask;
}
int fm_native_drive(drive)
int drive;
{
    if(drive<1 || drive>16 || !(fm_native_drives()&((unsigned)1<<(drive-1)))) return 0;
    if((BDOS(14,drive-1)&255)==255) return 0;
    return (BDOS(25,0)&255)==drive-1;
}
