/* Read-only viewer adapter. Every read restores the caller's DMA before
 * returning to screen painting. No file write or attribute call is used.
 */
#include "typeio.h"
static char tfcb[36];
static char *saved_dma;
static int opened;
int fm_type_open(drive,raw,dma)
int drive;
char *raw,*dma;
{
    int i;
    if(opened || drive<1 || drive>16 || !raw || !dma) return 0;
    for(i=0;i<36;++i) tfcb[i]=0;
    tfcb[0]=drive;
    for(i=1;i<12;++i) tfcb[i]=raw[i]&127;
    saved_dma=dma;
    opened=(__BDOS(15,tfcb)&255)!=255;
    return opened;
}
/* 1 record read, 0 EOF, -1 error. Unlike the historical reader, errors
 * remain distinguishable so a failed file is never marked completed. */
int fm_type_read(record)
char *record;
{
    int result;
    if(!opened || !record) return -1;
    __BDOS(26,record);
    result=__BDOS(20,tfcb)&255;
    __BDOS(26,saved_dma);
    return result==0 ? 1 : result==1 ? 0 : -1;
}
int fm_type_close()
{
    int result;
    if(!opened) return 1;
    result=(__BDOS(16,tfcb)&255)!=255;
    opened=0;
    __BDOS(26,saved_dma);
    return result;
}
