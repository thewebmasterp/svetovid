---
name: route
description: Route one service's mail end to end — triage every mail in its folder, cut slop at the sender's own notification settings (in the user's browser), agree with the user per category where mail goes (a feed, INBOX, Urgent, another folder, or stays), then have the rule written and landed (mail-rules), existing mail re-filed, and feeds published (feed-wiring). Built for several agents running it at once on different services. Use when the user says "next, <service>", "sort out / triage my <service> mail", "route <service> notifications", "move <these mails> to INBOX/Urgent/a feed", "do the same for <service> as for <other>", "create <svc>-rss", pastes a prompt from the sweep's hand-off, or runs /route. Not for one kind of mail across every service (the lane-* skills), auditing Urgent rules (lane-urgent) or feed-only changes (feed-wiring).
metadata:
  version: "2.0.0"
---

# route

One service at a time: its folder gets triaged and its mail moved where the
user wants it. Several agents may run this at once on different services, so
all thinking and editing happens in a private workspace; only landing and
re-filing take a shared lock (mail-rules handles both).

**Started without being asked?** If neither the user nor a hand-off prompt
asked for this service, ask before starting.

## Before anything

1. Read `$SVETOVID_HOME/route/notes.md` if it exists (the user's standing rules; they win
   where more specific) and the closest precedent in
   `$SVETOVID_HOME/route/services.md` if it exists.
2. This skill decides; two shared skills do the mechanics. Load them when you
   reach their steps: **mail-rules** (workspace, replay, land, re-file) and
   **feed-wiring** (feeds). For the sender's settings, the user's browser.

```sh
T=<this skill's folder>/scripts/triage
# Sibling skills sit next to this one; below, <mail-rules> means
# <this skill's folder>/../mail-rules/scripts, <feed-wiring> and <sweep> likewise.
```

## Rules

1. **Rules move, never copy, never drop.** Mail leaves `<svc>` for a feed,
   INBOX, Urgent or another folder; what stays in `<svc>` is "unrouted" by
   definition, and the weekly sweep works through it.
2. **Urgent comes first**: an urgent mail never reaches a route. Urgent holds
   the only copy; clean it by archiving.
3. **Slop is stopped at the sender**, never by rules. If the service has
   notification settings, go through them with the user in their browser,
   category by category; change only the email channel unless told; verify
   every toggle after a fresh page load. "Leave it" means leave it.
4. **Ask, don't assume.** Classify every mail, show categories with real
   subjects and counts, ask per category with a recommendation first.
   Free-text answers change the plan: follow them exactly; if two answers
   contradict, ask again. Confirm a folder name the user may have mistyped.
5. **Allowlist notices.** Route only the kinds the user named; an unknown
   kind stays in `<svc>`. Precision beats recall.
6. **Names:** a feed folder follows the `[folders] feed` template
   (per-service: `<svc>-rss`, or `<svc>-<topic>-rss` for a second feed),
   chosen by the user. **One folder per sending service, never shared**,
   named after the sender even when it arrives at another service's address
   (a CI service writing to the code host's address gets its own feed).
7. **A lane's kind of mail is not yours.** If the service is a shop, its
   order and shipping mail belongs to lane-deliveries; the generic Urgent
   keys (the lists every service shares) belong to lane-urgent. Leave those
   blocks alone. A rule that sends *this service's* mail to Urgent is yours:
   a class scoped by the service, in URGENT (mail-rules shows the form).
8. Permanent deletions need an explicit yes.

## Procedure

### 1. Open a workspace and look

```sh
<mail-rules>/rules-start <svc>
<feed-wiring>/feeds list; <feed-wiring>/feeds senders <svc>
$T <svc>                      # senders, List-Unsubscribe counts, type headers, subject groups
$T <svc> --first-lines        # when the subject hides the event
```

Also check: other folders holding this service's mail (`notmuch count
from:<domain>`); senders that are *other services* using this address
("Sign in with X" hands X's address to third parties); work mail mixed in.

**Find the discriminator**, best first:
1. A type header (the platform's template or reason header). When you
   find one, record it so the sweep groups by it too:
   `<sweep>/ms type-headers add <Header-Name>`.
2. Sender address or subdomain.
3. `List-Unsubscribe` present = marketing, absent = notices (verify on the
   archive: it is per service).
4. Subject keys, as an allowlist, last.

### 2. Settings at the sender (if the service has them)

Read every category first (no changes), then ask the user round by round
which emails to keep, then switch off the rest and re-read the page to
verify. Map each setting to the mail it produces and say so in the
questions. Record what was changed (the rules repo's log and the user's
notes).

### 3. Decide with the user

Present: counts per category, 1–2 real subjects each, what is already
handled (Urgent, existing routes), and a recommendation. Typical
destinations: a feed (things to read), INBOX (a person addressing the user:
chats, replies, invitations), Urgent (security, money, codes: check the
generic Urgent rules first, `rules-sim <svc> --show Urgent`), another folder
the user keeps, stays.

If the work came from a sweep hand-off, its destinations are decided: don't
ask them again.

### 4. Write and prove the route

Follow **mail-rules** steps 2–3: one self-contained block in the ROUTE part,
`rules-sim <svc> --diff`, `--show <target>`, `--refile <svc>` (counts must
match), log the change, commit.

### 5. Land, re-file

mail-rules steps 4–5: `rules-land <svc>`, then `rules-refile <svc> [--to <dest>
...] [--quiet-urgent]`. Move only what the user decided.

### 6. Feeds

```sh
<mail-rules>/rules-wait-mirror <folder> <expected count>
```

then feed-wiring: `feed-add` (body titles with `--title-regex` when every
mail has the same subject: test the regex on the archive first) and
`source-add`, **untagged and not in the reader** unless the user asks.

### 7. Close and record

```sh
<mail-rules>/rules-done <svc>
```

If the work came from a sweep hand-off, mark each pattern built:
`<sweep>/ms know set Kn --status built`.

Add the service to `$SVETOVID_HOME/route/services.md` (decisions in the
user's words, settings changed, what stays) so the next agent has a
precedent. Report: counts per destination, what stays and why, settings
changed at the sender, anything surprising (mixed-in work mail, other
services on the address, side effects).

## Need and check (for doctor)

- `scripts/need`: routes the user approved in a sweep that nobody has built
  (those are decisions, the one thing passed between skills), a service's
  own Urgent rule included. Generic Urgent keys go to lane-urgent.
- `scripts/check`: service folders holding mail the deployed rules would
  file elsewhere (arrived before its rule, or a re-file was skipped).

## Gotchas

- A work organisation's account-level mail (invites, team changes) is often
  not covered by the platform's per-organisation routing; ask where it goes.
- The feed bridge caps a feed at its `max_entries` (default 50).
- Mail that arrived while a rule was briefly missing: `rules-sim <svc> --refile
  <svc>`, then `rules-refile`.

## Keeping this skill current

General lessons go here (public: no names or addresses); the user's choices
in `$SVETOVID_HOME/route/notes.md`, per-service precedents in `services.md`.
