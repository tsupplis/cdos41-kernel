main(argc, argv)
int argc;
char **argv;
{
    int fd, msg, ok, language;
    if ((argc != 2 && argc != 3) || argv[1][0] < '0' || argv[1][0] > '4' || argv[1][1] ||
        (argc == 3 && (argv[2][0] < '0' || argv[2][0] > '8' || argv[2][1]))) {
        printf("Usage: NKEY 0..4 [language 0..8] (test copy NTEST.SYS)\n");
        exit(1);
    }
    fd = openb("NTEST.SYS", 2);
    if (fd < 0) {
        printf("Cannot open NTEST.SYS\n");
        exit(1);
    }
    msg = openb("NATIONAL.MSG", 0);
    language = argc == 3 ? argv[2][0] - '0' : -1;
    ok = msg >= 0 && set_choice(fd, msg, argv[1][0] - '0', language, 0);
    if (msg >= 0) close(msg);
    if (close(fd) < 0 || !ok) {
        printf("Keyboard update failed\n");
        exit(1);
    }
    printf("Keyboard selection saved\n");
    exit(0);
}
