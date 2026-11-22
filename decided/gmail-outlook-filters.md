# Supporting Gmail and Outlook filters

**Considered:** a rules backend for Gmail's filter API and Outlook's inbox
rules.

**Rejected (2026-11):** their filters lack what the skills rely on
(variables, ordered rules with stop, header tests, real folders), and every
change would need a second rule language and a second simulator. Users
forward such accounts to a Sieve provider instead (STACK.md, "Accounts you
can't move").
