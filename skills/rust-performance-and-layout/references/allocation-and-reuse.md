# Allocation and Reuse

Check these before deeper tuning:

- can the caller provide the output buffer,
- can a loop reuse one `Vec`, `String`, or map with `clear()`,
- can capacity be reserved once,
- can borrowed input avoid owned copies,
- can rarely-used large data move behind `Box`.

If the code clones because the API shape forced it, fix the boundary first.
