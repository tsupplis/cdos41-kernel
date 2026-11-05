/* Read-only directory display core. No BDOS calls or disk writes. */
#ifndef FM_DIRECTORY_H
#define FM_DIRECTORY_H
#define FM_NAME_WIDTH 12
#define FM_NAME_SIZE 13
/* Input: at least 12 bytes of a BDOS directory entry (user, name, type).
 * Output: twelve display bytes followed by NUL; capacity must be >= 13.
 */
int fm_directory_name();
/* Sort pointers to twelve-byte, seven-bit display names in place. */
int fm_directory_sort();
#endif
