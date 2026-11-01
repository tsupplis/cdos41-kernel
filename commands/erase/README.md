# DOS ERASE

The OEM-source rebuild has the same executable logic and data as 4.11,
except serial-number text. No command-line or behavior change is needed.

`make check` pins the independent 4.11 reference hash and compares the entire
file, allowing only the exact source serial, LINK86 stack placement (0038h
instead of 0037h), an additional zero-filled 512-byte page, the corresponding
page count and recalculated checksum. Both stack placements lie in checked
zero reserve. Any other difference fails the check.
