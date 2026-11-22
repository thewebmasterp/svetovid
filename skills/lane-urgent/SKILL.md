---
name: lane-urgent
description: The Urgent lane — audit and maintain which service mail is moved to the Urgent folder (and so interrupts the user with a notification). Finds mail that should have interrupted and did not, and mail that interrupted and should not have, adjusts the Urgent rules (through mail-rules), proves the change on the whole archive, deploys it and logs it. Use whenever the user asks to audit, check, review, tune or fix urgent mail or mail notifications, says an important mail (a code, a login alert, a failed payment) did not notify or "got lost", says a mail notified that should not have, mentions new sign-ups and wants their urgent mail caught, asks to add or remove an Urgent rule, says notifications stopped arriving, or runs /lane-urgent. The rules go stale as services appear and reword their mail, so it is meant to run every few weeks. Not for filing mail into folders (route), feeds (feed-wiring), or the weekly sign-off (sweep).
metadata:
  version: "2.0.0"
---

# lane-urgent

A **lane** pulls one kind of mail out of every service and sends it to one
place. This lane's kind is **mail the user must act on or know now**; its
place is the Urgent folder, which the notifier announces within seconds.

Keep the Urgent rules true: find service mail that should have interrupted
and did not, find mail that interrupted and should not have, adjust the
rules, prove the change, deploy it, and log it.

**Started without being asked?** If the user did not ask for an audit (or
pick it from doctor's prescription), ask before starting.

## Before anything

1. **Read `$SVETOVID_HOME/lane-urgent/notes.md`** if it exists: what the user decided is
   urgent and what is not, in their words. Those decisions override the
   defaults below; never re-open one without a strong reason.
2. Rule changes go through **mail-rules** (load it for step 3). Settings:
   `[rules]` and `[notifier]` in `$SVETOVID_HOME/config.toml`.

```sh
<mail-rules> = <this skill's folder>/../mail-rules/scripts
<sweep>      = <this skill's folder>/../sweep/scripts
```

## How it works

```
service mail -> the URGENT section sets a class (auth, security, money, ...)
             -> FOLD: a set class MOVES the mail into Urgent (not a copy),
                before any route, so Urgent wins over every feed
             -> the notifier (IMAP IDLE) sees it in Urgent
             -> a notification within seconds
```

- **Urgent is a move, not a copy.** An urgent mail exists in Urgent and
  nowhere else, so Urgent is cleared by archiving, not deleting.
- Only **service mail** can go to Urgent. A forwarded account's folder and
  INBOX are watched (or not) as whole folders: never write an Urgent rule
  for them.
- A new rule only moves mail that arrives after the deploy. To apply it to
  mail already in service folders: mail-rules' `rules-refile <svc>
  --quiet-urgent`, which pauses the notifier so a backfill does not burst.

## Defaults (the user's notes win)

- **Generic first.** A rule should match wording any service might use
  ("verification code", "new login"), so the next sign-up is covered
  without a change. Scope a rule to one service (`svc` + subject) only when
  its wording cannot be matched generically without false alarms.
  Updating a scoped rule when a service rewords is fine and expected.
- **Urgent means act-or-know-now:** codes and login links, security alerts,
  money moving, something broken or about to break, travel, parcels waiting
  with a deadline (unless a lane takes them: lane-deliveries undoes the
  parcel class for wired shops).
- **The test:** can the user act on it right now? A failure of something
  running at this moment is urgent; a nightly job failure goes to a feed.
- **Demoting:** don't delete a generic key that is right for other
  services. Add a scoped undo at the end of URGENT and a route to the
  sender's own feed (route skill). Re-file with `rules-refile Urgent --to
  <svc>-rss` so nothing else in Urgent moves.
- **Digest, not urgent:** messages on platforms, bills and statements, order
  progress (lane-deliveries), newsletters, terms-of-service notices. A new
  kind in that spirit: leave it; unsure: ask rather than add.
- A false alarm costs attention every time; a missed code costs a minute of
  opening the mail client. Prefer a slightly narrow rule to a noisy one,
  but never leave a real code or security alert uncaught.

## The audit

### 1. Get current

```sh
<config mail.sync_command>              # the archive must be fresh
<this skill's folder>/scripts/check     # the notifier runs
```

A notifier that is down explains "nothing notified" better than any rule
does, so check it before reading mail. Take the start date from the newest
line in `$SVETOVID_HOME/lane-urgent/runs.md` (no line yet: 30 days back).

### 2. Read the report

```sh
<mail-rules>/sieve-sim --live --audit --since <date of last audit>
```

Four sections; read all of them, the output is small enough.

- **A. Filed into Urgent.** Each group is a notification the user got. Would
  they want to be interrupted for it? Marketing, digests or anything on the
  digest list is a false alarm: find the key that matched (in brackets) and
  narrow it.
- **B. Not urgent, service mail.** Everything else, most suspicious first.
  Flags: `B` the body reads urgent (it opens with one of the learned body
  phrases, below), `N` the sender has never been seen before, `T` not bulk
  mail.
  Read every line, not only the flagged ones: the flags are a sort order,
  not a filter. You are looking for subjects that mean "act now" in words
  the rules do not know yet, in any language. Open the message in the local
  copy when unclear.
- **C. New services.** Signed up since last time, never checked against the
  rules: look at each one's mail in A and B with extra care, including what
  a sign-up flow sends (verify-your-email, first login alert).
- **D. Server check.** The real Urgent folder against the prediction. "In
  Urgent but not predicted" means the server and the replay disagree:
  investigate before touching rules. "Predicted but not in Urgent" is mail
  still in its service folder (arrived before the rule: re-file it) or mail
  the user archived; it matters most when a whole kind is missing (every
  non-ASCII subject, say), which means the server reads a rule differently.

Keep mail content inside this session: do not paste it into web searches or
other services.

**Body phrases (learned, never built in).** The `B` flag and the need script
look for wording that means "act now" in the opening of a mail whose subject
gave nothing away. That wording is the user's own, in their languages, so
none ships with svetovid: it lives in
`$SVETOVID_HOME/lane-urgent/body-phrases.txt`, one regex per line (`#`
starts a comment). With no file there is no `B` flag. In the first audit,
build it from the user's mail: read how the mail already in Urgent opens
(`<mail-rules>/sieve-sim --live --urgent` lists it by class; open two or
three of each) and write down how codes, alerts and deadlines are worded.
Add a line whenever an audit finds urgent mail the flag missed; drop one
that keeps flagging newsletters.

### 3. Change the rules (mail-rules)

`rules-start urgent`, then edit the URGENT section of the workspace script:

- Generic keys the user approved in the weekly sweep are this lane's to
  build (`<sweep>/ms know list --open`, the ones with svc `*`). After
  landing, mark each: `<sweep>/ms know set Kn --status built`.
- Add a key to the generic list of the right class when the wording is
  general. Keep keys as short as they can be while still specific:
  `"verify"` is fine, `"is your"` is not (it matches "Inspiration is
  yours").
- Senders whose Subject is a user-written title (issue trackers) get an undo
  for their generic matches, with a scoped rule for their real signals.
- A source that only ever mails when something is broken can be a scoped
  class by `svc`.

### 4. Prove it before deploying

```sh
<mail-rules>/rules-sim urgent --diff
```

`+ newly into Urgent` lines are mail the new rules would additionally move;
`- no longer into Urgent` lines ones they no longer move. The whole archive
is the regression suite: every `+` line must be worth an interruption and no
`-` line may be a real code or alert. A key that fixes one miss and adds
five newsletters is the wrong key; try a narrower one or a scoped rule.

### 5. Deploy, verify, log

Log the change where the user's notes say (date, period covered, what was
missed, what was noisy, keys added or removed, anything decided "digest"),
commit, then `rules-land urgent` (it uploads, verifies the server runs it and
probes with real mail: the cases in `[[rules.probe.case]]`, which should
include a non-ASCII key when the rules have one), `rules-refile` where the
diff showed mail to move, `rules-done urgent`. If nothing needed changing,
still log a short entry.

Then add a line to `$SVETOVID_HOME/lane-urgent/runs.md`:
`- YYYY-MM-DD <period covered, what changed>` (doctor reads it).

## Report

Short and concrete:

- period covered, mails read, how many went to Urgent
- **missed:** each kind of mail that should have notified, with the fix
- **noisy:** each false alarm, with the fix
- **new services** and whether their mail is covered
- what was deployed and that the probe passed, or that nothing changed
- anything left undecided, as a question

## When a single mail is the complaint

"X didn't notify": find the message, then walk the chain in order; each
step has a different fix.

1. Did it arrive in a service folder? Mail in INBOX or a forwarded
   account's folder notifies through that folder's watch, not Urgent.
2. `<mail-rules>/sieve-sim --explain <file>` traces it through the script:
   which class was set, where it was filed. Not filed into Urgent: the rules
   do not know the wording; go to step 3 of the audit.
3. Predicted into Urgent but not in the server's Urgent: the deployed
   script is stale or the server reads the rule differently: mail-rules'
   `check`, then `sieve-probe` (sending is safe; never `--clean` by hand,
   and not while another agent is landing: its clean-up removes your probes
   too).
4. In Urgent but no notification: the notifier (`scripts/check`, its logs;
   a locked keyring often shows as repeated password errors).

"X shouldn't have notified": `sieve-sim --explain <file>` shows the key;
narrow it, and run step 4 of the audit to see what else the key carries
before removing it.

## Need and check (for doctor)

- `scripts/need`: generic Urgent keys approved in the sweep and not built;
  and since the last audit, new services never checked, service
  mail whose opening reads urgent but was not filed into Urgent (sender
  domains only), and the server's Urgent disagreeing with the replay. A
  routine audit is due after `lanes.urgent.routine_days` (default 28)
  without a specific signal.
- `scripts/check`: the notifier runs.

## Keeping this skill current

General lessons go here (public: no names or addresses); the user's
decisions in `$SVETOVID_HOME/lane-urgent/notes.md`.
