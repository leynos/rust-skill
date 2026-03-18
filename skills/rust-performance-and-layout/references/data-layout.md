# Data Layout

Layout matters when size, cache locality, or ABI compatibility show up in
measurements or contracts.

Useful moves:

- inspect enum and struct size early on hot types,
- separate hot fields from cold payloads,
- box rare large variants,
- use contiguous representations for scan-heavy workloads,
- be explicit with `repr(C)` only when an ABI contract needs it.

Do not cargo-cult layout tricks into code that is not measured hot.
