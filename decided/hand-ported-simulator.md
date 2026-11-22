# Keeping a hand-written copy of the rules for the replay

**Considered (and used at first):** the replay tool carried a Python copy of
every routing rule, updated by hand next to the Sieve script.

**Rejected (2026-11):** the copy drifts, every change is written twice, and
the copy is personal, so nobody else could use the tool. sieve-sim now runs
the script itself; a rule it cannot run gets rewritten.
