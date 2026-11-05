/* Native DR C BDOS adapter. Search does not change drive or FAT mapping.
 * DMA restoration is explicit: BDOS has no portable get-DMA service.
 */
#include "scan.h"
static int getuser() { return __BDOS(32,255) & 255; }
static int setuser(user)
int user;
{ return __BDOS(32,user); }
static int setdma(address)
char *address;
{ return __BDOS(26,address); }
static int first(fcb)
char *fcb;
{ return __BDOS(17,fcb) & 255; }
static int next(fcb)
char *fcb;
{ return __BDOS(18,fcb) & 255; }
static struct fm_search_ops operations;
int fm_native_scan(drive,user,fat,files,capacity,count,restore_dma)
int drive,user,fat,capacity,*count;
struct fm_file *files;
char *restore_dma;
{
    /* DR C 1.11 emits incorrect relocations for static function addresses
     * in this aggregate initializer. Assign code pointers at runtime.
     */
    operations.getuser = getuser;
    operations.setuser = setuser;
    operations.setdma = setdma;
    operations.first = first;
    operations.next = next;
    return fm_scan(&operations,drive,user,fat,files,capacity,count,restore_dma);
}
