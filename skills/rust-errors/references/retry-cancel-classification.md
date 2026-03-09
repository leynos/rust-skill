# Retry and Cancellation Classification

Do not decide retries from text matching.

Classify failures by meaning:

- permanent: bad input, invariant break, unsupported operation,
- transient: timeout, temporary unavailability, contention, backpressure,
- cancelled: caller requested stop or shutdown,
- unknown: treat conservatively until the contract is clearer.

If cancellation is expected, make it a first-class result path instead of
burying it inside a generic IO error bucket.
