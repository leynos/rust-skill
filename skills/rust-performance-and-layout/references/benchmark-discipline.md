# Benchmark Discipline

Before and after numbers should answer the same question.

Checklist:

- isolate the workload,
- keep inputs stable,
- report wall time plus allocation effects when relevant,
- validate correctness before trusting the speedup,
- keep a simple baseline for comparison.

If the optimization changes semantics, it is not a benchmark result; it is a
different program.

For paired benchmarking, deterministic profiling, open-versus-closed load
models, tail latency, and goodput, see
[rigorous-benchmarking.md](rigorous-benchmarking.md).
