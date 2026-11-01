/* Read the CDOS 4.11 national directory from CCPM.SYS on the current drive. */
long lseek();
static char *keyboards[] = {
    "U.S., 8 Bit", "U.K., 8 Bit", "U.S., 7 Bit", "U.K., 7 Bit",
    "UK Keyboard, US Screen"
};

static int fetch(fd, pos, buf, size)
int fd, size;
long pos;
char *buf;
{
    return lseek(fd, pos, 0) == pos && read(fd, buf, size) == size;
}

static unsigned word(p)
char *p;
{
    return (p[0] & 255) | ((unsigned)p[1] << 8);
}

static char *inspect(fd)
int fd;
{
    char buf[48];
    unsigned slot;
    int i;
    long base;

    if (!fetch(fd, 0L, buf, 3) || buf[0] != 1)
        return "Invalid CCPM.SYS header";
    base = 128L + 16L * word(buf + 1);
    if (!fetch(fd, base + 0xc3cL, buf, 4))
        return "Cannot read national directory header";
    if (word(buf) != 0x574a)
        return "Missing JW signature in CCPM.SYS";
    if (!fetch(fd, base + word(buf + 2), buf, 48))
        return "Cannot read national directory";
    for (i = 0; i < 24; i++)
        printf("Slot %2d  %04x\n", i, word(buf + 2*i));
    slot = word(buf + 4);  /* N reads one byte from directory slot 2. */
    if (!slot || !fetch(fd, base + slot, buf, 1))
        return "Missing keyboard setting";
    if ((buf[0] & 255) >= 5)
        return "Unknown keyboard setting";
    printf("Keyboard and screen: %s\n", keyboards[buf[0]]);
    return 0;
}

main()
{
    int fd;
    char *error;
    fd = openb("CCPM.SYS", 0);
    if (fd < 0)
        error = "Cannot open CCPM.SYS";
    else {
        error = inspect(fd);
        close(fd);
    }
    if (error)
        printf("%s\n", error);
    exit(error != 0);
}
