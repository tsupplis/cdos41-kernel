/* Read FM.CFG using FCB I/O: current location, then P: user zero.
 * P: is CDOS's floating system drive. No current-drive/path change is needed.
 * The caller supplies its DMA address for restoration, as with scan.c.
 * Return 1 loaded, 0 absent, -1 I/O error; never publish a partial read.
 */
#include "fm.h"
int fm_config_load(config,restore_dma)
struct fm_config *config;
char *restore_dma;
{
    struct fm_config candidate;
    struct fm_config_reader reader;
    char fcb[36], record[128];
    int i,user,result,opened,status;
    user=__BDOS(32,255)&255;
    for(i=0;i<FM_CONFIG_COUNT;++i) candidate.value[i]=config->value[i];
    for(i=0;i<36;++i) fcb[i]=0;
    for(i=1;i<12;++i) fcb[i]=' ';
    fcb[1]='F';fcb[2]='M';fcb[9]='C';fcb[10]='F';fcb[11]='G';
    opened=(__BDOS(15,fcb)&255)!=255;
    if (!opened) {
        fcb[0]=16;
        __BDOS(32,0);
        opened=(__BDOS(15,fcb)&255)!=255;
    }
    result=0;
    if (opened) {
        fm_config_begin(&reader);
        __BDOS(26,record);
        result=1;
        while (!reader.ended) {
            status=__BDOS(20,fcb)&255;
            if (status==1) break;
            if (status) { result=-1;break; }
            for(i=0;i<128 && !reader.ended;++i)
                fm_config_feed(&candidate,&reader,record[i]);
        }
        fm_config_finish(&candidate,&reader);
        if ((__BDOS(16,fcb)&255)==255) result=-1;
    }
    __BDOS(32,user);
    __BDOS(26,restore_dma);
    if (result==1)
        for(i=0;i<FM_CONFIG_COUNT;++i) config->value[i]=candidate.value[i];
    return result;
}
