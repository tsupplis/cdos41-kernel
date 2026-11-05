/* Selection/viewport core from CODE 88D7..89FD, 8FFD..9028,
 * 90B7..91DC, and 92ED..933A. Rendering and marking are separate.
 */
#include "navigate.h"
static int fit(n)
struct fm_navigation *n;
{
    int changed,maximum;
    changed=0;
    n->offset=(n->offset/n->columns)*n->columns;
    while (n->selected<=n->offset) { n->offset-=n->columns; changed=1; }
    while (n->selected-n->offset>n->capacity) { n->offset+=n->columns; changed=1; }
    if (changed) {
        maximum=((n->count+n->columns-1)/n->columns)*n->columns-n->capacity;
        if (maximum<0) maximum=0;
        if (n->offset>maximum) n->offset=maximum;
    }
    return 0;
}
int fm_navigate(n,key)
struct fm_navigation *n;
int key;
{
    int old,offset,target;
    if (!n || n->count<0 || n->count>32000 || n->columns<1 ||
        n->columns>127 || n->capacity<n->columns || n->capacity>255 ||
        n->capacity%n->columns || n->offset<0) return -1;
    if (!n->count) { n->selected=0; n->offset=0; return 0; }
    if (n->selected<1 || n->selected>n->count || n->offset>=n->count) return -1;
    old=n->selected; offset=n->offset; target=old;
    switch (key) {
    case 12: target=old==n->count ? 1 : old+1; break;
    case 8: target=old==1 ? n->count : old-1; break;
    case 11: if (old>n->columns) target=old-n->columns; break;
    case 10:
        if (old==n->count) break;
        target=old+n->columns;
        if (target>n->count) {
            if (n->offset+n->capacity<n->count) {
                n->selected=n->count; fit(n); n->selected=old;
            }
            target=old;
        }
        break;
    case 1: target=1; break;
    case 26: target=n->count; break;
    default: return 0;
    }
    n->selected=target;
    fit(n);
    return n->selected!=old || n->offset!=offset;
}
