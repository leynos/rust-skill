# Rigorous Benchmarking

Single-number "X is N% faster" claims hide more than they reveal. Five
disciplines turn microbenchmarks and load tests into evidence that can
survive a code review.

## Paired benchmarking with Tango

[Tango](https://github.com/bazhenov/tango) interleaves two implementations
in the same process, on the same input, in the same wall-clock window. It
cancels out the noise sources that ruin isolated benchmark runs (CPU
frequency scaling, cache state, GC-style allocator effects, neighbouring
process load) by comparing pairs of samples rather than aggregate means.

Use Tango when the change is a swap of one implementation for another and
the question is "which is faster on this input?". The output is a paired
difference distribution, which you can ship as evidence rather than a bar
chart of two means.

## Deterministic profiling with iai-callgrind

[`iai-callgrind`](https://github.com/iai-callgrind/iai-callgrind) runs each
benchmark under Valgrind's Callgrind and reports instruction counts, cache
events, and branch behaviour rather than wall time. The same revision on
the same input produces the same number, which makes it useful in CI:
regressions show up as a step change, not as drift.

It does not replace wall-clock benchmarking (instruction count is a proxy,
not the truth). Use it to catch regressions early and to localise them to
a function, then confirm with a wall-clock run.

## Open versus closed system models

A closed-loop benchmark issues request _N+1_ only after request _N_
completes. A real production system has clients that keep arriving whether
the server is keeping up or not. Closed-loop measurements understate
latency tails because slow responses throttle the offered load.

Pick the model that matches the question:

- Microbenchmarks of a pure function: closed-loop is fine.
- Service-level latency under load: open-loop (Poisson or fixed-rate
  arrivals). Tools like `wrk2`, `vegeta`, `oha`, and Goose support
  rate-controlled load.

If a benchmark cannot say which model it is using, treat the numbers as
informational, not load-bearing.

## Tail latency and CDFs

The mean (and often the median) of a latency distribution hides the
behaviour users actually notice. Report p95, p99, and p99.9 instead, and
include the maximum observed. Better: publish the full latency CDF for the
window, so a reviewer can see whether the tail is a long plateau or a
small spike.

A common rule of thumb: the slowest 1% of requests can dominate a user's
perception of a service; the slowest 0.1% can dominate a sales call. Both
should be in the measurement, not in the post-mortem.

## Goodput, not throughput

Throughput counts requests served. Goodput counts requests that were
served _and were useful_ (within the SLO, not retried, not returned as an
error to the client). A system can have flat throughput while goodput
collapses under overload. Define what counts as useful per the workload and
report goodput alongside throughput in any load test.

## Where this fits

[`benchmark-discipline.md`](benchmark-discipline.md) covers the day-to-day
hygiene rules (isolate the workload, keep inputs stable, validate
correctness). This page covers the harder questions: which model are you
benchmarking, which statistic answers the question, and which tools cancel
out the noise that turns benchmarks into vibes.
