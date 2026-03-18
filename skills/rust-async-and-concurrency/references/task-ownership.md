# Task Ownership

Every spawned task should answer three questions:

- Who starts it?
- Who can stop it?
- Who waits for it or observes failure?

If those answers differ, write them down in the type or API.

Typical safe shape:

- owner creates task,
- owner holds `JoinHandle`,
- owner passes a shutdown signal,
- owner awaits completion during teardown.
