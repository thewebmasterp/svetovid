# Scope

svetovid decides with you what your mail and RSS system should do, and
looks after it. It does not install the parts: doctor writes a build plan
from STACK.md, and you (or your agent) build them.

## In scope

- Deciding with the user where mail goes, and keeping those decisions.
- Writing, proving, deploying and checking Sieve rules for that.
- Re-filing mail already received when the rules change.
- Turning mail folders and websites into feeds, and wiring them into a hub
  and a reader.
- Checking that all of it still works, and saying which skill to run.

## Out of scope

- Installing or operating infrastructure (mail servers, Docker, the hub, the
  reader, VPNs). STACK.md states what each part must do; building it is
  yours.
- Mail providers without user-written Sieve rules.
- Getting around a site's login wall, anti-bot checks or terms to scrape it.
- Reading mail for the user beyond what a skill needs to decide where it
  goes. The model running a skill reads the mail that skill shows it (that
  is how it decides). Beyond that, mail content goes to no other service
  unless the user asks for it (an AI filter or a digest in the hub).

## A new skill

A new skill is added only when its job cannot be built from the existing
skills. It owns one job (a workflow) or one mechanism (a shared skill used by
at least two others), ships a `need` script when it is a workflow and a
`check` script when it builds something that can break, keeps no personal
data in the repository, and names tools by their role.
A new lane follows the lane pattern (detect, ask per service, write rules,
deliver, catch misses).

## Nothing built in

No word list, language, courier, folder name or service is assumed by the
code. What depends on the user is learned from their own mail or read from
their server, and kept in their data. Where a whole kind of service differs
(an alias service), it plugs in as one module (`lib/aliases/`), and a module
for a service nobody has contributed yet is a welcome pull request.

Ideas already considered and rejected are in [decided/](decided/), one file
each, with the reason. Read them before proposing something.
