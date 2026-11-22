# One skill with modes

**Considered:** a single `svetovid` skill routing to mode files
(`/svetovid sweep`, `/svetovid deliveries`, ...), as some large personal
pipelines do.

**Rejected (2026-11):** it blurs the boundaries between jobs, one
description has to trigger for everything (so the right mode is picked less
reliably), and one job cannot be read, run or replaced on its own.
Separate skills with two shared skills underneath keep each job runnable
alone and each procedure written once. (They still share `lib/` and the
two shared skills, so the repository is installed whole.)
