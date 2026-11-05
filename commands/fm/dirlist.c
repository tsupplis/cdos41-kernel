/* FM directory display names and pointer sorting.
 * CODE 0DC8h..0E6Fh formats BDOS entries; 20A4h..21FBh sorts lists.
 * Enumeration and extended metadata belong to the future native adapter.
 */
#include "dirlist.h"

int fm_directory_name(entry, output, capacity)
char *entry, *output;
int capacity;
{
    int i, length, ch;
    if (!entry || !output || capacity < FM_NAME_SIZE) return 0;
    length = 0;
    for (i = 1; i <= 8; ++i) {
        ch = entry[i] & 127;
        if (ch == ' ') break;
        output[length++] = ch;
    }
    /* The original checks the unmasked extension byte here. */
    if ((entry[9] & 255) != ' ') output[length++] = '.';
    for (i = 9; i <= 11; ++i) output[length++] = entry[i] & 127;
    while (length < FM_NAME_WIDTH) output[length++] = ' ';
    output[length] = 0;
    return 1;
}

static int compare(left, right)
char *left, *right;
{
    int i, a, b;
    for (i = 0; i < FM_NAME_WIDTH; ++i) {
        a = left[i] & 127;
        b = right[i] & 127;
        if (a != b) return a < b ? -1 : 1;
        if (!b) break;
    }
    return 0;
}

static int sort(names, count)
char **names;
int count;
{
    int left, right, pivot, remaining;
    char *saved;
    /* Same pivot and swaps as the original. Recurse into the smaller
     * partition and iterate the larger, bounding the 16-bit stack use.
     */
    while (count > 1) {
        left = 0;
        right = pivot = count - 1;
        do {
            while (left < right && compare(names[left], names[pivot]) <= 0)
                ++left;
            while (right > left && compare(names[right], names[pivot]) >= 0)
                --right;
            if (left < right) {
                saved = names[left]; names[left] = names[right];
                names[right] = saved;
            }
        } while (left < right);
        saved = names[left]; names[left] = names[pivot];
        names[pivot] = saved;
        remaining = count - left - 1;
        if (left < remaining) {
            sort(names, left);
            names += left + 1;
            count = remaining;
        } else {
            sort(names + left + 1, remaining);
            count = left;
        }
    }
    return 1;
}

int fm_directory_sort(names, count)
char **names;
int count;
{
    int i;
    if (count < 0 || (count && !names)) return 0;
    for (i = 0; i < count; ++i) if (!names[i]) return 0;
    return sort(names, count);
}
