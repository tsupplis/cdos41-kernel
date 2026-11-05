/* Read-only BDOS search. The caller supplies its current DMA address,
 * in the same data segment, so it can be restored on every exit.
 * Search-first/next state is consumed; searches cannot be interleaved.
 */
#ifndef FM_SCAN_H
#define FM_SCAN_H
#include "dirlist.h"
struct fm_file {
    char name[FM_NAME_SIZE];
    char raw[32];
    int directory;
};
struct fm_search_ops {
    int (*getuser)();
    int (*setuser)();
    int (*setdma)();
    int (*first)();
    int (*next)();
};
/* drive: 1..16, user: 0..15, fat: known media type (0/1).
 * Returns 1 complete, 0 capacity reached, -1 invalid input/search result.
 * count is the number of valid entries, including on a partial result.
 */
int fm_scan();
int fm_native_scan();
int fm_native_enter();
#endif
