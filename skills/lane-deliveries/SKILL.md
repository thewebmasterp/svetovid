---
name: lane-deliveries
description: The deliveries lane — keeps the user's Deliveries feed complete. Every web shop's order lifecycle (placed, paid, shipped, courier notices, delivered, cancelled) is moved by the rules into the shop's deliveries folder and read as one feed. Each run finds new folders and shops whose order mail is not wired yet, asks per shop (a no is remembered; a shop with an order in progress is deferred), has the rules built from how that shop actually writes, and catches delivery mail the rules missed. Use when the user says "check deliveries", "scan for new shops", "I ordered from a new shop", "wire <shop> into deliveries", "order mail ended up in the <shop> folder", "a parcel notice is missing from Deliveries", runs /lane-deliveries, or after the weekly sweep. Not for other routing (route), Urgent rules (lane-urgent), the weekly sign-off (sweep), or other feeds (feed-wiring).
metadata:
  version: "2.0.0"
---

# lane-deliveries

A **lane** pulls one kind of mail out of every service and sends it to one
place. This lane's kind is **order and shipping mail from shops**; its place
is the Deliveries feed. Everything else about a shop's mail (promos, account
mail, reviews) is not this skill's business.

Every lane does the same five things: detect its kind of mail in any
service, ask the user per service (a no is remembered), write the rules
through mail-rules, send the mail to its destination (through feed-wiring
when it is a feed), and catch what the rules missed.

**Started without being asked?** If the user did not ask for this lane (or
pick it from doctor's prescription), ask before starting.

## Before anything

1. **Read `$SVETOVID_HOME/lane-deliveries/notes.md` if it exists.** It holds the user's
   decisions in their words (what counts as delivery mail, how courier mail
   is filed, per-shop notes). Where it is more specific than this file, it
   wins. Add to it whenever the user decides something new.
2. Settings: `[folders] deliveries` (per-service `<shop>-deliveries-rss`, or
   one shared folder), `[lanes.deliveries] tag`, and the rest of
   `$SVETOVID_HOME/config.toml`.

```sh
D=<this skill's folder>/scripts/deliv
# Siblings: <mail-rules> = <this skill's folder>/../mail-rules/scripts,
#           <feed-wiring> = <this skill's folder>/../feed-wiring/scripts
```

## The pipeline

```
shop / courier -> the shop's own address (identity = the shop)
  -> URGENT: the parcel class is undone for wired shops
  -> ROUTE, DELIVERIES block: courier mail at a wired shop's identity, or the
     shop's own order mail (sender + Subject allowlist) -> the shop's deliveries folder
  -> bridge feed /<folder>.xml with title prefix "<Shop> · "
  -> hub source "<prefix><Shop> Deliveries" in the lane's tag
  -> the reader follows the tag
```

A wired shop is in **three lists in the script that must agree**: the shop
list of the parcel undo at the end of URGENT, the shop list of the courier
block at the top of DELIVERIES, and its own block(s) in DELIVERIES; plus its
bridge channel and its place in the hub tag. `deliv check --remote`
verifies all of them. (sieve-sim runs the script itself, so there is no
second copy of the rules to keep in step.)

### The lane's rules (written once, with the first shop)

`deliv check` finds the lists by their exact shape. A new setup has none of
them (the check says so and passes); write them in the workspace when the
first shop is wired. `${why}` and `${svc}` stand for the script's class and
service variables (`rules.class_var`, `rules.service_var`):

1. **A `parcel` class** among the generic URGENT keys, if the script has
   none: the notices that mean a parcel is waiting or on its way ("out for
   delivery", "ready for pickup", in the user's languages) set the class to
   `parcel`.
2. **The undo, at the end of URGENT** (rule 2 below has the exact text).
3. **The courier block, first in a DELIVERIES part of ROUTE:**

   ```sieve
   if allof (string :is "${svc}" ["<shop>", ...],
             anyof (address :domain :is "From" ["<courier domain>", ...],
                    header :contains "<original-sender header>" ["<courier domain>", ...])) {
       fileinto :create "<the shop's deliveries folder>"; stop;
   }
   ```

   The second `anyof` line is only for alias-service forwards (the header is
   `SENDER_HEADERS` in the service's module, `lib/aliases/`). Each shop's
   own block(s) follow it.

## Rules

1. **The shop owns its order.** Courier mail that reaches a shop's identity
   goes to *that shop's* folder, never a courier folder. Order confirmations
   and "thank you" mails count too.
2. **Parcel notices go to the feed, not Urgent**, for wired shops: the
   URGENT undo is `allof (string :is "${why}" ["parcel"], string :is
   "${svc}" [shops]) { set "why" ""; }`. Only the parcel class: a pickup
   code (auth), a payment problem (action) or a security notice still
   interrupts. Shops not wired yet keep the Urgent parcel behaviour.
3. **In scope:** order placed/confirmed, payment received for an order,
   order receipts, shipped / handed to courier / on the way, courier
   notices, delivery updates, delivered, cancelled, returns and their
   shipments, subscription *shipments* ("ships soon", "skipped delivery").
   **Out:** review requests, "did it arrive?" check-ups, promos (also those
   that say "delivery"), subscription sign-up/cancel, rewards, account mail,
   digital purchases where nothing ships. Unsure: ask.
4. **Ask before wiring a shop.** One question per shop. "No" is recorded
   (`deliv set <shop> declined --words ...`) and the shop is never offered
   again. "Ask me next time" records nothing.
5. **Don't wire an order in progress.** If a shop's newest delivery-like
   mail is recent and not a final step (delivered, cancelled, review
   request), more mail is coming and its wording is not known yet: `deliv
   set <shop> deferred --note "<what is open>"`, do not ask, revisit next
   run. Speed is not a goal; complete rules are.
6. **Precision in the rules, recall in the scan.** Rules are allowlists
   built from the shop's real mail (sender, then Subject keys); an unknown
   kind stays in `<shop>`. The scanner casts wide on purpose; a recurring
   false hit gets an `ignore` rule, never a looser filing rule.
7. **Mail is moved, never copied or dropped**, and only through `rules-refile`
   after the rules are live. Never mark mail read, never delete.

## The vocabulary (learned from the user's mail, never built in)

`deliv` recognises delivery mail by four lists it keeps in the user's
state. The repository ships none of them: no word, no language, no courier.

| list | what it holds | example |
|---|---|---|
| `subject` | regex: words that mark order and shipping mail | `order`, `shipped` |
| `final` | regex: words that end an order | `delivered`, `cancel` |
| `courier` | sender domains of couriers and tracking services | `courier.example` |
| `sender` | globs on the sender address | `shipping@*` |

Couriers named in the script's courier block count without being listed.

**Learn it before the first scan, and again whenever something new shows
up** (a shop writing in another language, a courier you have not seen):

```sh
$D learn                     # the evidence, from the user's own mail
$D vocab add --subject '<word>' --final '<word>' --courier <domain> --sender '<glob>'
$D vocab list
```

`learn` prints three things: senders that reach several services (a courier
writes to every shop's address; so do payment and review platforms, which
are not couriers), mail already in a deliveries folder that the vocabulary
would miss, and subjects carrying an order-like number that nothing
recognises. Read them, open what is unclear (`$D show <svc>`), and record
the wording you judge to mean an order or a parcel, in every language the
user's shops write in. Prefer a short stem that survives inflection over a
whole phrase. A wrong word costs a false hit in the scan (silence it with an
ignore rule, or `vocab rm`); a missing one hides a shop.

## State (private, in `$SVETOVID_HOME/lane-deliveries/`)

| what | file |
|---|---|
| the vocabulary: `subject`, `final`, `courier`, `sender` | `state.json` (`deliv vocab`) |
| per folder: `wired` / `declined` / `deferred` / `none`, words, notes, feed prefix; ignore rules; `last_scan` | `state.json` (`deliv set`, `deliv ignore`) |
| the user's decisions in their words | `notes.md` |
| one line per run | `runs.md` (`deliv done`) |
| last scan's groups `g1..` | `$SVETOVID_CACHE/lane-deliveries/last-scan.json` |

"New folder" means not in `state.json`. `deliv done` records every new
folder without delivery-like mail as `none`, so the next run only looks at
folders created after it. A `none` folder is still scanned every run: a
service that later sends order mail shows up under CANDIDATES.

## Procedure

### 1. Sync, check, scan

```sh
$D sync
$D check                     # lists agree? fix an INCONSISTENT before anything else
$D learn                     # first run, or when the scan says there is no vocabulary
$D scan
```

The scan has four sections; groups are `g<n>` (one sender + subject shape):

- **MISSED / REFILE** (wired shops): `REFILE` = the deployed rules already
  route it but the mail was never moved (arrived before a rule): just
  `rules-refile`. `MISSED` = no rule takes it: read it (`$D show gN`); if it
  is in scope (rule 3), widen that shop's block; if not, add an ignore
  rule. Mail the rules send to Urgent (codes, payment) is left out of this
  section by design.
- **NEW folders** since the last scan, each with its delivery-like mail
  and an `IN PROGRESS?` hint (newest mail recent and not final).
- **CANDIDATES**: known folders (`none` or `deferred`) that now have
  delivery-like mail. A deferred shop shows its note: decide whether the
  open order has finished.
- DEFERRED / GONE / declined lines for bookkeeping.

### 2. Judge each shop

For every NEW or CANDIDATE folder with delivery-like mail, read enough
(`$D show <svc>` lists every mail of the identity in all folders, `*` =
delivery-like; `--body` adds a snippet; `$D show gN` reads one group):

| it is | do |
|---|---|
| false hits only (promos that say "delivery", digital orders) | `$D ignore add --svc <svc> --kind "<what>" --subject '<re>' [--from '<glob>']`; no question |
| a shop with complete orders (each reached a final step) | ask (step 3) |
| a shop with an order still open | `$D set <svc> deferred --note "<order N, last step …>"`; tell the user, no question |
| one order mail so far, wording of the later steps unknown | deferred, same |

### 3. Ask

One question per shop, self-contained: shop, how many orders and when, 2–3
real subjects, which senders (couriers included). Options: `Wire into
Deliveries` (recommended when it is a real shop), `No, never ask again`,
`Ask me next time`.

- yes: build it (step 4).
- no: `$D set <svc> declined --words "<their words>"`.
- next time: record nothing, and close the run with `$D done --force`
  (step 5), which leaves the folder undecided.

Free-text answers win over the options; if one changes a rule above, write
it to `notes.md` and ask whether this skill should change too.

### 4. Build (one workspace per run, all shops together)

Load **mail-rules** and follow its procedure with the workspace name
`deliveries`:

```sh
<mail-rules>/rules-start deliveries
$D show <shop> --body | less               # every mail of the identity, all folders
```

1. **Find the senders.** Which addresses send order mail; is any of them
   order-only (some shops use a separate shipping sender or a tracking
   service)? Alias-service forwards carry the real sender in their own
   header (From is the alias), so every sender test is `anyof (address …
   "From" …, header :contains "<original-sender header>" …)`. Couriers are
   covered by the courier block; a courier not in its domain list gets
   added there (`deliv` then counts it too).
2. **Pick Subject keys** when the sender also sends promos or reviews: one
   key per lifecycle step seen, short but specific (`order shipped`, not
   `order`, when "order now" promos exist). See mail-rules' gotchas for
   non-ASCII keys. `List-Unsubscribe` is useless when an alias service adds
   it to everything.
3. **Edit** the workspace's script: add the shop to the URGENT undo list
   and the courier block's shop list, and add its block(s) in alphabetical
   position inside DELIVERIES, with a comment saying what goes and what
   deliberately stays.
4. **Replay** (read-only):

   ```sh
   <mail-rules>/rules-sim deliveries --show <shop folder> -n 100   # everything in scope, nothing else
   <mail-rules>/rules-sim deliveries --show <shop> -n 100          # what stays: no order mail left
   <mail-rules>/rules-sim deliveries --diff                        # only "- no longer into Urgent (parcel)" lines expected
   <mail-rules>/rules-sim deliveries --refile <shop> --to <shop folder> --show 3   # the server agrees
   ```
5. **Log and commit** as mail-rules says (the user's notes say where).
6. **Land and re-file:**

   ```sh
   <mail-rules>/rules-land deliveries
   <mail-rules>/rules-refile <shop> --to <shop folder>
   <mail-rules>/rules-refile Urgent --to <shop folder>      # only if the diff showed parcel mail
   ```
7. **Feed** (feed-wiring):

   ```sh
   <mail-rules>/rules-wait-mirror <shop folder> <count>
   python3 -I <feed-wiring>/feeds add --name <shop folder> --title "<Shop> Deliveries" \
       --title-prefix "<Shop>" --tag <lanes.deliveries.tag> [--category "<reader category>"]
   $D set <shop> wired --prefix "<Shop>" --title "<Shop> Deliveries" --words "<their words>"
   ```

   `--category` is needed once: while the reader does not follow the
   lane's tag yet (ask the user which category), `feeds` says "NOT
   subscribed" without it. A feed name takes a-z, 0-9, dash and underscore
   only: for a folder with a dot, give another `--name` and pass the folder
   with `--folder`. `<Shop>` is the shop's own spelling. A folder created by
   the re-file holds only what was moved; a shop with nothing to re-file
   gets its folder at its first order mail (`fileinto :create`), and its
   feed can be added before (it stays empty until then).

For MISSED mail at a wired shop: same steps without the list edits (widen
its block), land, `rules-refile <shop> --to <shop folder>`.

**One shared folder** (`[folders] deliveries` without `{svc}`): every
shop's block files into the same folder, there is one feed, and the title
prefix comes from the sender's name instead; wiring a shop is only its
rule.

### 5. Close

```sh
$D check --remote            # script lists, bridge channels, hub tag all agree
<mail-rules>/rules-done deliveries
$D done --note "<one line: wired X, declined Y, deferred Z>"
```

`done` refuses while a new folder with delivery mail has no decision;
`--force` is for a shop the user left for next time.

Report: shops wired (mails re-filed per shop, feed entries), declined,
deferred and why, missed mail fixed, ignore rules added, anything odd (a
courier at an unexpected identity, a shop using two identities).

## Need and check (for doctor)

- `scripts/need`: escaped delivery mail at wired shops, and new or known
  shops whose order mail is waiting with no order in progress (an open
  order is a note, not work). Counts, names and dates only: never a subject.
- `scripts/check`: `deliv check --remote` (the three script lists, state,
  bridge channels, hub tag).

## Gotchas

- `deliv` reads the deployed rules: before `rules-land` the scan still shows
  the old routing. Rescan after.
- `deliv check` before landing a new shop reports it missing from the
  script's lists if you already `set` it wired; set wired after landing.
- A shop writing from two identities (an old address and an alias) is one
  shop only if the user merged the identity; otherwise ask.
- The bridge keeps the newest `max_entries` per feed; older ones stay in
  the folder.
- Two mails with the same subject are two entries with the same title; some
  readers collapse them.
- The sweep skips lane folders, so wired mail never shows up there; order
  mail it sees in shop folders is this skill's MISSED/CANDIDATES.
- `SVETOVID_DELIVERIES_STATE` / `SVETOVID_DELIVERIES_CACHE` point `deliv`
  at a scratch state for testing changes to the script.

## Keeping this skill current

General lessons go here (public: no names or addresses); the user's
decisions in `$SVETOVID_HOME/lane-deliveries/notes.md`.
