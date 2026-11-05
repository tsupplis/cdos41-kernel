/* FM.CFG parsing, translated from FM CODE 5DED..5F18 and 602C..6208.
 * Public callers own line buffering and system-drive/user-area selection.
 * Matching ignores ASCII letter case but preserves spaces and '=' placement.
 * Values wrap at 16 bits; assignment retains the low byte, as in the original.
 */
#include "fm.h"

char *fm_config_names[] = {
    "OVPMODE=", "MENU POSITION=", "OBJECT FG COLOR=", "OBJECT BG COLOR=",
    "COMMAND FG COLOR=", "COMMAND BG COLOR=", "PROMPT FG COLOR=",
    "PROMPT BG COLOR=", "MENU SIZE=", "PROMPT SIZE=", "TOP MARGIN=",
    "BOTTOM MARGIN=", "LEFT MARGIN=", "RIGHT MARGIN=",
    "KEY FG COLOR=", "KEY BG COLOR="
};

static int upper(c)
int c;
{
    if (c >= 'a' && c <= 'z') return c - 'a' + 'A';
    return c;
}

/* Return the original table index (14..29), or zero without moving *input.
 * Empty table entries 1..13 cannot match a keyword ending in '='.
 */
int fm_config_keyword(input)
char **input;
{
    char *p, *key;
    int i;
    for (i = 0; i < FM_CONFIG_COUNT; ++i) {
        p = *input;
        key = fm_config_names[i];
        while (*key && upper(*p & 255) == *key) { ++p; ++key; }
        if (!*key) { *input = p; return i + 14; }
    }
    return 0;
}

/* CODE 5E11: skip spaces, consume unsigned decimal digits, require one digit.
 * No sign, tab or hexadecimal prefix is recognized. On failure, leave both
 * caller outputs unchanged. Stop at the first non-digit for the next parser.
 */
int fm_config_number(input, result)
char **input;
unsigned *result;
{
    char *p;
    unsigned value;
    int found;
    p = *input;
    while (*p == ' ') ++p;
    value = 0;
    found = 0;
    while (*p >= '0' && *p <= '9') {
        value = (value * 10 + (*p++ - '0')) & (unsigned)65535;
        found = 1;
    }
    if (found) { *input = p; *result = value; }
    return found;
}

/* One assignment only. Whole-file line handling remains in the native layer.
 * A recognized keyword is consumed even when its numeric value is absent.
 */
int fm_config_assignment(config, input)
struct fm_config *config;
char **input;
{
    int keyword;
    unsigned value;
    keyword = fm_config_keyword(input);
    if (!keyword || !fm_config_number(input, &value)) return 0;
    config->value[keyword - 14] = value & 255;
    return keyword;
}

/* DATA defaults with the PC reset at CODE 5D3Ah applied. */
int fm_config_defaults(config)
struct fm_config *config;
{
    static char defaults[FM_CONFIG_COUNT]={2,1,0,5,0,4,15,1,17,1,0,2,0,0,14,1};
    int i;
    if (!config) return 0;
    for(i=0;i<FM_CONFIG_COUNT;++i) config->value[i]=defaults[i];
    return 1;
}
int fm_config_begin(reader)
struct fm_config_reader *reader;
{
    reader->used=reader->overflow=reader->ended=reader->assignments=0;
    return 1;
}
static int line_end(config,reader)
struct fm_config *config;
struct fm_config_reader *reader;
{
    char *line;
    reader->line[reader->used]=0;
    line=reader->line;
    /* Reject an oversized line as a unit; never interpret its suffix. */
    if (!reader->overflow && fm_config_assignment(config,&line))
        ++reader->assignments;
    reader->used=reader->overflow=0;
    return reader->assignments;
}
int fm_config_feed(config,reader,ch)
struct fm_config *config;
struct fm_config_reader *reader;
int ch;
{
    if (reader->ended) return 0;
    ch &= 255;
    if (ch==26) {
        line_end(config,reader);reader->ended=1;return 0;
    }
    if (ch==13 || ch==10) line_end(config,reader);
    else if (reader->used<81) reader->line[reader->used++]=ch;
    else reader->overflow=1;
    return 1;
}
int fm_config_finish(config,reader)
struct fm_config *config;
struct fm_config_reader *reader;
{
    if (!reader->ended) line_end(config,reader);
    reader->ended=1;
    return reader->assignments;
}
