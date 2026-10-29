/* DOS SETENV. Environment editing is independent of the far-memory bridge. */
#include "setenv.h"
char envbuf[ENV_MAX] = {0}, result[ENV_MAX] = {0};

int upper(c)
int c;
{
    if (c >= 'a' && c <= 'z') c -= 'a' - 'A';
    return c;
}

/* Match a complete NAME= prefix, never a substring in another name or value. */
int matches(entry, name, n)
char *entry, *name;
int n;
{
    int i;
    for (i = 0; i < n; ++i)
        if (!entry[i] || upper(entry[i]) != upper(name[i])) return 0;
    return entry[n] == '=';
}

/* Return used bytes through the final extra NUL, or -1 for malformed input. */
int envused(buf, cap)
char *buf;
int cap;
{
    int i;
    for (i = 0; i + 1 < cap; ++i)
        if (!buf[i] && !buf[i+1]) return i + 2;
    return -1;
}

/* Build transactionally in result; envbuf is untouched on overflow/error.
   Empty value deletes. Preserve unrelated entries and the value's exact bytes. */
int change(name, n, value, cap)
char *name, *value;
int n, cap;
{
    int i, j, k, end, used;
    used = envused(envbuf, cap);
    if (used < 0) return -1;
    j = 0;
    for (i = 0; i < used - 1 && envbuf[i]; i = end + 1) {
        for (end = i; envbuf[end]; ++end) ;
        if (!matches(envbuf+i, name, n))
            for (k = i; k <= end; ++k) result[j++] = envbuf[k];
    }
    if (*value) {
        for (k = 0; value[k]; ++k) ;
        if (j + n + k + 3 > cap) return -1;
        for (k = 0; k < n; ++k) result[j++] = upper(name[k]);
        result[j++] = '=';
        for (k = 0; value[k]; ++k) result[j++] = value[k];
        result[j++] = 0;
    }
    while (j < cap) result[j++] = 0;
    return 0;
}

#ifndef HOST_TEST
void message(s)
char *s;
{
    while (*s) bdos(2, *s++ & 255);
}
void line(s)
char *s;
{
    message(s);
    message("\r\n");
}
main()
{
    char tail[129], *name, *value;
    int i, n, cap, used, assign, found;
    n = tailread(tail);
    name = tail;
    while (*name == ' ' || *name == '\t') ++name;
    if (*name == '?' || (*name == '/' && name[1] == '?')) {
        line("SETENV [NAME[=value]]  (empty value removes NAME)");
        return;
    }
    n = 0;
    while (name[n] && name[n] != '=') {
        if (name[n] <= ' ') { line("Invalid environment variable name."); return; }
        ++n;
    }
    assign = name[n] == '=';
    if (assign && !n) { line("Missing environment variable name."); return; }
    value = name + n + (assign ? 1 : 0);
    cap = envread(envbuf);
    if (cap < 2) {
        line("SETENV requires a supported Concurrent DOS environment.");
        return;
    }
    used = envused(envbuf, cap);
    if (used < 0) { line("Invalid environment block; unchanged."); return; }
    if (assign) {
        if (change(name,n,value,cap)) { line("Insufficient environment space; unchanged."); return; }
        envwrite(result);
        return;
    }
    found = 0;
    for (i = 0; i < used-1 && envbuf[i]; ) {
        if (!n || matches(envbuf+i,name,n)) { line(envbuf+i); found=1; }
        while (envbuf[i++]) ;
    }
    if (n && !found) line("Environment variable not found.");
}
#endif
