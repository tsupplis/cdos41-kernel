/* invoke(command): 1 launched/completed successfully, 0 failed.
 * report(message): nonzero displayed, zero UI failure.
 * fm_run_file returns 1 success, 0 rejected/launch failure, -1 UI failure.
 * Caller refreshes after success. No arguments or wildcard commands.
 */
struct fm_runner { int (*invoke)(); int (*report)(); };
int fm_run_file();
