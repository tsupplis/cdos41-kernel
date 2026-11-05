/* Console transaction boundary. Callbacks return 1 on success, 0 on
 * failure; read returns a byte, -1 when no input, or -2 on failure.
 * Direct-screen locking is optional; it must never span BDOS output.
 */
struct fm_console {
    int (*acquire)();
    int (*release)();
    int (*put)();
    int (*read)();
    int held;
};
int fm_console_begin();
int fm_console_end();
int fm_console_write();
int fm_console_key();
int fm_native_key();
