/* Bounded read-only search adapter, based on FM CODE 0E70h.
 * Disk access is injected; formatting stays in dirlist.c. No pathname
 * changes, allocation, opens or writes are performed by this module.
 */
#include "scan.h"
int fm_scan(ops, drive, user, fat, files, capacity, count, restore_dma)
struct fm_search_ops *ops;
int drive, user, fat, capacity, *count;
struct fm_file *files;
char *restore_dma;
{
    char fcb[36], dma[128], *entry;
    int i, slot, saved_user, result;
    if (!ops || !ops->getuser || !ops->setuser || !ops->setdma ||
        !ops->first || !ops->next || !files || !count || !restore_dma ||
        drive < 1 || drive > 16 || user < 0 || user > 15 ||
        fat < 0 || fat > 1 || capacity < 1 || capacity > 512) return -1;
    *count = 0;
    for (i = 0; i < 36; ++i) fcb[i] = 0;
    for (i = 1; i < 12; ++i) fcb[i] = '?';
    /* Extended search exposes FAT directories as well as regular files.
     * On CP/M, never interpret allocation bytes as directory flags.
     */
    fcb[0] = drive | 128;
    saved_user = (*ops->getuser)();
    if (saved_user < 0 || saved_user > 15) return -1;
    (*ops->setuser)(user);
    (*ops->setdma)(dma);
    result = 1;
    slot = (*ops->first)(fcb);
    for (;;) {
        slot &= 255;
        if (slot == 255) break;
        if (slot > 3) { result = -1; break; }
        entry = dma + slot * 32;
        if ((entry[0] & 255) == user) {
            if (*count == capacity) { result = 0; break; }
            fm_directory_name(entry, files[*count].name, FM_NAME_SIZE);
            for (i = 0; i < 32; ++i) files[*count].raw[i] = entry[i];
            files[*count].directory = fat && (entry[16] & 64) != 0;
            ++*count;
        }
        /* The original reinstates the extended drive flag each time. */
        fcb[0] = drive | 128;
        slot = (*ops->next)(fcb);
    }
    (*ops->setdma)(restore_dma);
    (*ops->setuser)(saved_user);
    return result;
}
