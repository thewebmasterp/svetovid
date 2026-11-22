# Passing doctor's findings to the prescribed skill

**Considered:** doctor saves each skill's need as a file the skill reads on
start, or passes the item as an argument (`/lane-deliveries exampleshop`).

**Rejected (2026-11):** the skill looks again when it starts (its own scan,
which sees at least what its need script saw) and finds at least as much,
including what arrived after doctor ran. A
handed-over scope would make it skip that. Rule: between skills pass only
what cannot be worked out again, which means the user's decisions (the
sweep's approved routes).
