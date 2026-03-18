# Blocking and Backpressure

Async does not remove blocking; it only moves where blocking hurts.

Rules:

- use `spawn_blocking` for blocking libraries or CPU-heavy bursts,
- bound queues and channels when producers can outrun consumers,
- make backpressure visible in API names or return values,
- prefer dropping low-value work explicitly over silent memory growth.

If latency spikes and queue length both rise, look for hidden blocking first.
