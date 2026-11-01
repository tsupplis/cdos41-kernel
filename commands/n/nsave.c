/* Save national settings to the selected system file. */
long lseek();
static int byte_at(fd, pos, value, writing)
int fd, writing;
long pos;
char *value;
{
    if (lseek(fd, pos, 0) != pos)
        return 0;
    if (writing)
        return write(fd, value, 1) == 1;
    return read(fd, value, 1) == 1;
}

int word_at(fd, pos, value)
int fd;
long pos;
unsigned *value;
{
    char b[2];
    if (lseek(fd, pos, 0) != pos || read(fd, b, 2) != 2)
        return 0;
    *value = (b[0] & 255) | ((unsigned)b[1] << 8);
    return 1;
}

/* Stage all 21 slot writes before changing the disposable system file. */
struct change {
    long pos;
    int size;
    char before[64], after[64];
};
static struct change edits[21];

static int transfer(fd, pos, buf, n, writing)
int fd, n, writing;
long pos;
char *buf;
{
    if (lseek(fd, pos, 0) != pos)
        return 0;
    if (writing)
        return write(fd, buf, n) == n;
    return read(fd, buf, n) == n;
}

/* A zero size denotes a NUL-terminated message, including its terminator. */
static int message(fd, language, number, e)
int fd, language, number;
struct change *e;
{
    unsigned offset;
    int i;
    if (!word_at(fd, 128L + 200L * language + 2L * number, &offset))
        return 0;
    if (e->size)
        return transfer(fd, 128L + offset, e->after, e->size, 0);
    for (i = 0; i < sizeof(e->after); i++)
        if (!byte_at(fd, 128L + offset + i, &e->after[i], 0))
            return 0;
        else if (!e->after[i]) {
            e->size = i + 1;
            return 1;
        }
    return 0;
}

int set_choice(fd, msg, choice, language, models)
int fd, msg, choice, language;
char *models;
{
    static char flags[] = {0,6,1,7,3};
    static char printer_flags[] = {4,2,4,7,1,0};
    static int sizes[] = {1,1,1,54,54,54,0,0,0,0,55,48,48,5,0,5,8,8,1,0,0};
    static int messages[] = {-1,-1,-1,50,51,52,53,54,55,56,-1,57,58,59,0,60,61,62,-1,67,68};
    unsigned paras, signature, directory, slot;
    long base;
    int i, j, alternate, number, model;
    char group;
    struct change *e;
    if (!byte_at(fd, 0L, &group, 0) || group != 1 ||
        !word_at(fd, 1L, &paras))
        return 0;
    base = 128L + 16L * paras;
    if (!word_at(fd, base + 0xc3cL, &signature) || signature != 0x574a ||
        !word_at(fd, base + 0xc3eL, &directory) || !directory)
        return 0;
    for (i = 0; i < 21; i++) {
        if (!word_at(fd, base + directory + 2*i, &slot) || !slot)
            return 0;
        edits[i].pos = base + slot;
        edits[i].size = sizes[i];
    }
    if (!byte_at(fd, edits[18].pos, edits[18].after, 0))
        return 0;
    if (language < 0) {
        if (!byte_at(fd, edits[0].pos, &group, 0)) return 0;
        language = group & 255;
        if (language > 8) return 0;
    }
    alternate = edits[18].after[0] != 0;
    for (i = 0; i < 21; i++) {
        e = &edits[i];
        number = messages[i];
        if (alternate && i >= 3 && i <= 5) number += 13;
        if (alternate && i == 9) number = 66;
        if (alternate && i >= 19) number += 2;
        if (number >= 0 && !message(msg, language, number, e))
            return 0;
        if (!transfer(fd, e->pos, e->before, e->size, 0))
            return 0;
    }
    edits[0].after[0] = language;
    edits[1].after[0] = flags[choice];
    edits[2].after[0] = choice;
    e = &edits[10];
    for (i = 0; i < 55; i++) e->after[i] = e->before[i];
    for (i = 0; i < 55; i += 11) {
        model = models ? models[i/11] : (e->before[i+1] & 255);
        if (model >= sizeof(printer_flags)) return 0;
        e->after[i+1] = model;
        e->after[i+2] = printer_flags[model];
        e->after[i+3] = 0;
        e->after[i+8] = 0xff;
    }
    for (i = 0; i < 21; i++) {
        e = &edits[i];
        if (!transfer(fd, e->pos, e->after, e->size, 1)) {
            for (j = i; j >= 0; j--)
                transfer(fd, edits[j].pos, edits[j].before, edits[j].size, 1);
            return 0;
        }
    }
    return 1;
}
