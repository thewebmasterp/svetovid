---
name: sweep
description: The weekly sweep of the user's unread service mail — the per-service folders the rules did not empty. Syncs first, sorts every service folder into a category, walks the user through one category at a time (junk as titles only, real mail with a one-line summary), spots recurring kinds of mail that should go to Urgent, INBOX, another folder or a feed, records the user's decision in a log so it never asks about that kind again, marks the signed-off batch read on the server, ends with ready-to-paste prompts for route agents that build the approved routes, and offers to empty the Trash. Use when the user says "weekly mail sweep", "go through my service mail", "clean up the service folders", "sign off my mail", "mark my service mail read", "what's in my service folders", "empty the trash", or runs /sweep. It never builds routes, edits rules, moves or deletes mail (the one exception: emptying Trash after the user says yes) — that is route (per service) and lane-urgent (generic Urgent keys).
metadata:
  version: "2.0.0"
---

# sweep

One concern: **go through the unread service mail with the user, sign it
off, and notice patterns.** Building anything from those patterns is someone
else's job (route and lane-urgent agents, with the prompts this skill writes
at the end). Meant to run about once a week.

**Started without being asked?** If the user did not ask for a sweep (or
pick it from doctor's prescription), ask "Start the weekly sweep now?"
before reading any mail.

## Before anything

1. Read `$SVETOVID_HOME/sweep/notes.md` if it exists (the user's own decisions; where it
   is more specific than this file, it wins).
2. Settings come from `$SVETOVID_HOME/config.toml`; missing: tell the user to
   run doctor.

```sh
M=<this skill's folder>/scripts/ms
```

## What "service mail" means here

Every sign-up gets its own address, and the rules file it into that
service's folder (the `[folders] service` template, `<svc>`). Urgent and the
routes (feeds, INBOX, other folders) take out what matters; **what is left
in `<svc>` is junk or mail that slipped past the rules**. The user keeps
those folders near empty, and this sweep is how.

In scope: every service folder. Out of scope: INBOX, Urgent, forwarded
accounts' folders, Sent/Drafts/Trash/Junk/Archive, the probe folder, and
every feed or lane folder. Folders come and go with sign-ups, so `ms`
discovers them from the local copy each run; never keep a list here.

With folders by kind (`[folders] scheme = "by-kind"` in the config: no
per-service addresses) there are no service folders and this skill has
little to do; say so and stop.

## Rules

1. **Sync before reading** (`ms sync`). It prints MISMATCH and exits 1 when
   the server's and the local folder sets or unread counts differ. Run it
   once more; if the mismatch stays, report it and stop.
2. **Mark read only what the user signed off**, and only through
   `ms signoff`. It marks exactly the Message-IDs of the scanned batch, so
   mail that arrived later stays unread for next time. Never move, delete,
   expunge or tag mail deleted. Never mark read outside a sign-off. The one
   exception is emptying **Trash** (step 6), only through `ms trash --empty`,
   only after the user said yes to that run's listing.
3. **Never build.** No rule edits, no feeds, no re-files, no settings at the
   sender. An approved pattern is logged (`ms know add`) and goes in the
   hand-off prompt.
4. **Don't ask twice.** A kind of mail the user said stays is in the log
   (`ms scan` marks it `[known Kn stays]`); show those as titles, never
   suggest them again. If a group is clearly the same kind but the matcher
   missed it (reworded subject, new sender subdomain), treat it as known and
   widen the matcher: `$M know set Kn --subject '<wider regex>'`, and say so.
5. **The user's words decide.** Free-text answers override the options;
   record them in `--words`. If an answer is unclear, ask again; don't guess
   a destination.
6. Summaries come from the model running this skill only. Mail content and
   addresses never go to another outside service.

## State (private, in `$SVETOVID_HOME/sweep/`)

| what | file |
|---|---|
| category of each folder (`order` = walk order) | `categories.json` (`ms cat`) |
| **decisions log** (patterns: stays / approved routes) | `known.json` (`ms know`) |
| sign-off log, one line per category per run | `runs.md` (written by `ms signoff`) |
| this week's batch manifests (group ids, Message-IDs) | `$SVETOVID_CACHE/sweep/<YYYY-Www>/<category>.json` |

A run is one ISO week, so a sweep can be paused and resumed the same week.

Log entry fields: `svc` (folder, or `*` for any service), `kind` (plain
words), matchers (`--from` fnmatch glob on the real sender, `--subject`
case-insensitive regex, `--header 'Name=glob'`; none = whole folder),
`decision` (`stays`, `urgent`, `inbox`, `rss`, `folder` (+ `--dest
<Folder>`), `sender-off`, `other`), `dest` (e.g. a proposed `<svc>-rss`),
`words` (the user's), `status` (`final` for stays; `approved` -> `handed` ->
`built`; `dropped`). `other` is a destination none of these names: say which
in `--dest` and `--words`.

## Procedure

### 1. Sync and plan

```sh
$M sync
$M scan                      # overview: categories, unread per folder, open patterns
```

- **UNCATEGORIZED** folders: allocate each one yourself. Use an existing
  category when it fits (`$M cat list`), make a new one only when none
  does: `$M cat set <folder> <category>`. Tell the user what you allocated in
  one line; they can move it.
- **GONE** folders: `$M cat rm <folder>`.
- Show the plan: categories in order with unread counts, in a short table.
  Walk categories with unread mail in the `order` given; skip empty ones. If
  the user wants another order or to skip one, do that (`$M cat order <cat>
  ...` keeps it for next time).

### 2. Each category: scan, read, present

```sh
$M scan <category>           # groups g1.. per folder; writes the batch
$M show g7 g9 -n 2           # bodies of groups you need to summarise
```

Each group is one sender + one subject shape (digits masked), or one type
header value (configurable: `sweep.type_headers`). Flags:

- `LU` = has List-Unsubscribe (marketing at most services, but check it).
- `[known Kn ...]` = in the decisions log.
- `[live rules -> X: n]` = today's deployed rules would file it elsewhere
  (it arrived before the rule existed). These stay unread on sign-off and go
  into the hand-off as a re-file job.
- `> ...` snippet (unknown, non-LU groups; `--snippets all` for every group).

Decide **junk** vs **worth a look** per group yourself. Junk: promotions,
newsletters, referral offers, tips, social bait, review requests,
welcome/onboarding mail, routine policy notices. Worth a look: anything
transactional or personal (receipts, orders, account or plan changes,
security-ish notices that Urgent missed, a person writing, alerts,
deadlines, legal or money notices that matter). When unsure, read it
(`ms show`) and count it as worth a look.

Present the category as one message, in this shape:

```
## Money — 4 folders, 413 unread

**examplebank** (181)
Junk: 120× referral and promo ("Earn €45 for each friend…"), 31× product tips
Worth a look:
- 2026-11-12 "Changes to your account terms": fees rise on 1 Jan; nothing to do.
- 2026-11-03 "Your statement is ready": October statement.
Already decided: 12× K3 savings promos stay

Left unread (live rules would move them): 2× examplepower → examplepower-bills-rss
```

- Junk: titles only, groups merged into one line per kind with counts and
  1–3 real titles. A long backlog stays readable that way.
- Worth a look: one line each: date, title, what it says and whether there
  is anything to do. Several of the same kind become one line with a count
  and the latest date.
- Leave empty sections out.

### 3. Patterns

After the listing, a **Patterns** section: recurring (or clearly recurring)
kinds of *worth a look* mail that are not in the log and should arguably
leave the folder. For each: what it is, count and dates, the discriminator
you can see (sender, subject shape, type header), and your recommendation:
(`ms` groups by a platform's type header only once it has learned it:
`$M type-headers` lists them, `$M type-headers add <Header-Name>` adds one.)

- **Urgent**: the user must see it within minutes (codes, logins, money
  moved, something that breaks unless acted on). First check whether a
  *generic* Urgent key should have caught it (then the pattern is `svc '*'`
  and the hand-off goes to lane-urgent, not route).
- **INBOX**: a person addressing the user (chat, reply, invitation).
- **a feed (`<svc>-rss`)**: things to read at leisure that recur (receipts,
  bills, statements, alerts). One feed per sending service, never shared.
  Don't propose feeds for minor senders.
- **folder**: another folder the user keeps (e.g. a forwarded work
  account's folder for mail about their job); see their notes.
- **sender-off**: recurring junk the user wants stopped at the service
  (route turns it off in the service's settings). Propose only for heavy
  junk, and only once; "leave it" is a valid answer (log it as stays).
- **stays**: nothing to route. Logging this is what stops future questions.

**Mail that belongs to a lane is not a pattern here.** Each `lane-*` skill
owns one kind of mail across every service (lane-deliveries: order and
shipping mail from shops; lane-urgent: what interrupts). Show such mail as
usual (worth a look, one line per order), but don't ask a Patterns question
about it and don't log it; at the end, if any was in the batch, say "N order
mails in <shops>: run lane-deliveries next". Lane folders are skipped with
every other non-service folder.

Ask one question per pattern (several per round is fine): recommended
destination first, then the other plausible ones, `Stays (remember)`, and
`Ask me next time` (log nothing). The question must stand alone: service,
kind, count, two real titles.

Record each answer straight away:

```sh
$M know add --svc examplebank --kind "monthly statement ready" --subject 'statement' \
    --from 'no-reply@examplebank.com' --decision rss --dest examplebank-rss \
    --words "<their words if they typed any>" --group g31
$M know add --svc examplebank --kind "referral and promo offers" --from 'no-reply@examplebank.com' \
    --header 'List-Unsubscribe=*' --decision stays --group g21
```

Keep matchers as narrow as the evidence (precision over recall: an unknown
kind should stay in the folder). `--group` stores sample titles and
Message-IDs for the hand-off (`know set Kn --group gN` replaces them). Group
ids restart in every category scan, so a bare `gN` is taken from the scan
where `gN` is in the folder `--svc` names; for `--svc '*'` pass
`<category>:gN`, or it means the latest scanned category. A group in another
folder is refused, never attached silently.

### 4. Sign off

Ask with the last patterns, or on its own: `Sign off <category> (mark N
read)` (recommended), `Sign off but keep the worth-a-look mail unread`, `Not
yet`. Free text like "keep the terms one" → `--keep g12`.

```sh
$M signoff <category> [--keep g12 --keep <message-id> ...]
```

It marks the batch read locally, syncs, and checks on the server that none
of the signed Message-IDs is still unseen. Report its one-line result. If it
says NOT seen on server, run `$M signoff <category>` again (idempotent); if
that fails too, stop and report. Then the next category, unprompted.

### 5. Hand-off

After the last category (or when the user stops):

```sh
$M handoff                  # approved patterns + handed ones still arriving + leftovers, per service
```

Lane mail never goes in these prompts (see Patterns): point the user to the
lane skill instead.

Write **one prompt per service** for the **route** skill (one service per
agent; the user may run several agents at once), and at most one prompt for
**lane-urgent** for `svc '*'` Urgent patterns. Each prompt is
self-contained, in a fenced block. Write its first line as the user will
type it: `doctor.command_prefix` from the config, then the skill (`/route`
when the skills are linked into a skills folder, `/svetovid:route` from the
plugin). Replace `<sweep skill folder>` with this skill's real path, so the
other session can run it.

```
/route examplebank

The weekly mail sweep (YYYY-MM-DD) found these kinds of mail in the
examplebank folder, and I decided where they go. Build them. Don't ask me
about the destinations again, but do ask about whatever the skill says needs
my say (folder names, settings at the sender, edge cases).

1. K7, monthly "Your statement is ready": 4 mails 2026-08..2026-11 from
   no-reply@examplebank.com. Destination: a feed (examplebank-rss, or a name
   you propose). My words: "...". Discriminator seen: Subject "statement"
   + no List-Unsubscribe; check it against the whole archive.
   Example Message-IDs: <...>, <...>
2. Re-file: 2 unread mails the live rules already route to examplebank-rss
   (they arrived before the rule).

When a pattern is live, mark it built:
<sweep skill folder>/scripts/ms know set K7 --status built
```

`sender-off` items go in the same service prompt (route's settings step, in
the user's browser). Patterns marked handed that are **still arriving** go
in again, saying the route is missing or misses. The lane-urgent prompt has
the same shape: its command, the `svc '*'` patterns with their examples,
and the same closing line.

Then `$M handoff --mark-handed`. The approved patterns are the one thing
this skill passes on: they record the user's decisions, which nothing else
can work out again.

### 6. Empty the Trash

Every run, after the hand-off, offer to empty the Trash (asked only to
empty the Trash: do this step alone):

```sh
$M trash                    # Trash on the server: count, size, one line per mail; remembers the listing
```

Summarise it in one short block (kinds with counts) and call out anything
that does not look like it belongs in Trash (a person writing, receipts,
mail newer than this week). Then ask: `Empty Trash (N mails, permanently)`
(recommended), `Not this week`. If the user names mails to rescue, say this
step cannot keep single mails: they move them out in their mail client
first, then you rerun `$M trash`. Skip the question when Trash is empty.

```sh
$M trash --empty            # deletes exactly the listed mails on the server, syncs, logs a line
```

It deletes only what `ms trash` listed (mail trashed afterwards stays; on a
server without UIDPLUS, also whatever else in Trash was already flagged
deleted) and exits 1 with NOT ALL DELETED if any of them is still there; run
it once more, then report. Deleting is permanent.

End with a short summary: per category read / kept, patterns logged (stays
vs approved), the prompts, Trash emptied or not, and anything odd (sync
mismatch, verification retries, mail that looked like phishing).

## Need (for doctor)

`scripts/need` prints one JSON line: work when unread service mail piles up
(`sweep.need_unread`, default 30 mails, or the oldest older than
`sweep.need_age_days`, default 7), plus notes (approved patterns not handed
yet, folders without a category). No mail content.

## Gotchas

- notmuch tags a message, not a file: if the same Message-ID sits in two
  folders, both copies become read. That is the same mail, so it's fine.
- Mail without a Message-ID gets a synthetic notmuch id; sign-off marks it,
  but the server check cannot see it (counted as verified by the local
  flag).
- `ms` classifies with the deployed rules (mail-rules' sieve-sim on
  origin/<branch>); a route agent landing mid-sweep may change the live
  flags between scans. Rescan, don't worry.
- A category scan prints every group. For a huge backlog (a first run can
  hold ~1,000 mails, ~200 groups) read the output fully, then compress it in
  the presentation.
- `SVETOVID_SWEEP_STATE` / `SVETOVID_SWEEP_CACHE` point `ms` at a scratch
  state for testing changes to the script.

## Keeping this skill current

General lessons go here (public: no names or addresses); the user's choices
go in `$SVETOVID_HOME/sweep/notes.md`. Tell the user what you added.
