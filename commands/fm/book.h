/* Session-only directory bookmarks. FAT aliases are pinned snapshots;
 * navigation clones them so entering another directory cannot change them.
 * FAT identity assumes stable mounted media; validation does not force a
 * media login or proactively detect disk removal/reinsertion.
 */
struct fm_book { int set,fat,drive,user; char label[32]; };
int fm_book_set();
/* Resolve saved target; navigation!=0 clones FAT mapping. Returns drive,
 * zero on unset/invalid/failed clone. CP/M user remains in book->user. */
int fm_book_target();
