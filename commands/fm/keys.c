/* CODE 66EEh: apply terminal mappings in order, including cascades.
 * The native loader supplies validated table lengths; it must stop at the
 * original source table's first NUL. No PC scan-code assumption is made here.
 */
#include "keys.h"
int fm_key_translate(key, source, target, length)
int key, length;
char *source, *target;
{
    int i;
    key &= 255;
    if (!source || !target || length<0) return key;
    for (i=0;i<length && source[i];++i)
        if (key==(source[i]&255)) key=target[i]&255;
    return key;
}

/* CODE 68C8h..6909h: FM navigation/control values after terminal translation.
 * Control bytes not listed here pass through unchanged, including Escape.
 */
int fm_key_normalize(key)
int key;
{
    key &= 255;
    switch (key) {
    case 0xe1: case 0xbb: return '?';
    case 9: return 3;
    case 0xd1: case 0xcf: return 26;
    case 0xc9: case 0xc7: return 1;
    case 0xd2: return ',';
    case 0xd3: return 127;
    case 0xc8: return 11;
    case 0xd0: return 10;
    case 0xcb: return 8;
    case 0xcd: return 12;
    }
    return key;
}
