# Lifecycle and RAII

RAII is the default resource model: acquire in a constructor, release in
`Drop`, and let scope define cleanup.

Use it for:

- file handles and sockets,
- temporary directories and test fixtures,
- transaction guards,
- lock guards and mapped views,
- cancellation or shutdown guards that must fire on unwind or early return.

If a type needs `start()` and `stop()` in normal use, consider an owning guard
or wrapper that makes the valid lifecycle the only easy path.
