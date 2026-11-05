/* Original CODE 6DC3h..6E16h and 6CFBh..6D12h release the
 * direct-screen semaphore before BDOS output and reacquire afterward.
 * Reconstruct the ownership boundary without embedding XIOS offsets here.
 */
#include "conio.h"
#include "keys.h"
int fm_console_begin(console)
struct fm_console *console;
{
    if (!console || !console->acquire || !console->release) return 0;
    if (console->held) return 1;
    if (!(*console->acquire)()) return 0;
    console->held=1;
    return 1;
}
int fm_console_end(console)
struct fm_console *console;
{
    if (!console) return 0;
    if (!console->held) return 1;
    if (!console->release || !(*console->release)()) return 0;
    console->held=0;
    return 1;
}
int fm_console_write(console, bytes, length)
struct fm_console *console;
char *bytes;
int length;
{
    int was_held, ok, i;
    if (!console || !console->put || length<0 || (length && !bytes)) return 0;
    if (!length) return 1;
    was_held=console->held;
    if (was_held && !fm_console_end(console)) return 0;
    ok=1;
    for (i=0; i<length; ++i)
        if (!(*console->put)(bytes[i]&255)) { ok=0; break; }
    if (was_held && !fm_console_begin(console)) return 0;
    return ok;
}
int fm_console_key(console, source, target, length)
struct fm_console *console;
char *source, *target;
int length;
{
    int key;
    if (!console || !console->read || length<0 ||
        (length && (!source || !target))) return -2;
    /* Never wait/poll for input while owning direct-screen memory. */
    if (!fm_console_end(console)) return -2;
    key=(*console->read)();
    if (key<0) return key;
    if (key>255) return -2;
    return fm_key_normalize(fm_key_translate(key,source,target,length));
}
