/* Session directory slots behind original F3/F4 and F7/F8 commands.
 * Original FM DATA 1F50h: "DIR #1 set to: ". FAT captures use pinned
 * process aliases; CP/M captures store the drive and user number directly.
 */
#include "book.h"
#include "fatdest.h"
int fm_book_set(book,fat,drive,user,raw,label,dma)
struct fm_book *book;
int fat,drive,user;
char *raw,*label,*dma;
{
    int next,i;
    if(!book || !label || drive<1 || drive>16 || user<0 || user>15) return 0;
    next=drive;
    if(fat) {
        next=fm_fat_capture(drive,raw,dma);
        if(next<=0 || !fm_fat_pin(next)) return 0;
    }
    if(book->set && book->fat) fm_fat_unpin(book->drive);
    book->set=1;book->fat=fat;book->drive=next;book->user=user;
    for(i=0;i<31 && label[i];++i) book->label[i]=label[i];
    book->label[i]=0;
    return 1;
}
int fm_book_target(book,navigation,dma)
struct fm_book *book;
int navigation;
char *dma;
{
    if(!book || !book->set) return 0;
    if(!book->fat) return book->drive;
    if(!fm_fat_valid(book->drive)) return 0;
    return navigation ? fm_fat_clone(book->drive,dma) : book->drive;
}
