---
name: doctor
description: The entry point of svetovid. Examines the user's mail and feed system and prescribes which skills to run and why — setup (the system against the card and the config), health (every skill's check: is what it built still right?) and need (every skill's need: is there real work, with evidence) — and never runs a skill itself. Its first run, with no config yet, walks the user through setup from STACK.md. Run it whenever you want to know whether everything is flowing and what needs attention. Not for fixing or building anything: it names the skill, or the part of the card, that does.
disable-model-invocation: true
metadata:
  version: "1.0.0"
---

# doctor

Doctor examines and prescribes; it never runs a skill. It knows *when*
each skill is worth running and *whether* each skill's work still holds.
The user decides what to run.

```sh
DR=<this skill's folder>/scripts/doctor
```

## First run: setup

If `$SVETOVID_HOME/config.toml` does not exist (`$DR --setup` says so),
this is a first run. Doctor asks, writes two files (the config and a build
plan) and stops. It never builds anything.

1. Read `STACK.md` (the repo root, two folders up from this skill) in full.
2. **Ask first where their mail is.** That one answer decides whether the
   rest is worth asking. Sieve is a language for filter rules the user
   writes and the mail provider runs as each message arrives. Gmail and
   Outlook cannot run it; Migadu, mailbox.org, Fastmail and a Dovecot server
   can (STACK.md, "What you must have", says what each one offers).
3. **No Sieve, stop.** Say so in those plain words (they may never have
   heard of Sieve) and tell them what STACK.md says to do: get an address at
   a provider that runs Sieve and forward the old account to it. Be honest
   about what that gives: forwarded mail all arrives at one address, so old
   sign-ups cannot be sorted per service ("What you must have", "Accounts
   you can't move"). Ask nothing more, write nothing, and tell them to run
   doctor again when they have the address.
4. **Ask what else they have now**, not what they want: the mailbox address
   they log in with and a command that prints its password (a keyring
   lookup), whether they use per-service addresses (or folders by kind),
   whether mail reaches them through an alias service (addy.io, SimpleLogin,
   a provider's masked addresses), accounts they can't move, where they can run services (only this
   machine, an always-on box, rented), which parts of the card they already
   run (a local copy of the mail, a rules repository, notifier, bridge, hub,
   reader), and whether they want feeds or mail only.
5. **Write `$SVETOVID_HOME/config.toml`** from `config.example.toml`, with
   values for the parts they already have (`SVETOVID_HOME` defaults to
   `~/.config/svetovid`). Secrets never go in the file: only commands that
   print them (keyring lookups). Set `doctor.command_prefix` to how these
   skills are installed, so the commands doctor prints can be typed as they
   are: `/svetovid:` from the plugin, `/` when they are linked into a skills
   folder. Leave out the keys of parts that do not exist yet (the local
   copy's `maildir` and sync commands, `[notifier]`, the probe, all of
   `[feeds]`): doctor lists them as missing until they are built, and that
   list is the plan's checklist. For the provider's hosts use what the user
   or the provider's own documentation says; whatever you could not verify,
   say so in the plan. Nothing about the user's mailbox is assumed:
   - **Folders.** Once the mailbox answers, `$DR --folders` prints what the
     server itself says its folders are for. Write them into
     `rules.not_routed` and `mail.trash_folder` / `junk_folder` /
     `archive_folder`.
   - **Alias service.** Set `mail.alias_service` to theirs. If `lib/aliases/`
     has no module for it, the plan gets a section: write the module
     (`addy_io.py` is the model and explains every field) from a few real
     forwards in their mailbox, and open a pull request with it, so the next
     user of that service has it.
6. **Write `$SVETOVID_HOME/doctor/build-plan.md`** (create the folder), a
   prompt for the user's agent, one section per missing part. Mail parts
   first: the provider's settings (per-service addresses), the local copy,
   the rules repository and script (STACK.md, "The Sieve script": every
   setup needs them, though they are not a row in the parts table; the
   starter is `examples/main.sieve` in the repo root), the
   probe cases, the notifier. Then the feed parts, if they want feeds. Each
   section says:
   - what the part must do (from STACK.md, the constraints only);
   - the reference choice and the alternatives that fit what they told you
     (e.g. no always-on box: Docker on this machine, and what that loses);
   - which config keys to fill in when it's built;
   - how doctor will check it: a setup check, or the skill's check that
     covers it. Say so when nothing can check it (a phone app as the
     notifier has no health command).
   Start the file with one line saying it was written by doctor on a date,
   for the agent that will build it in a fresh session. End it with the
   facts still open: what you asked and they did not know.
7. Run `$DR --setup` once and show its lines. On a first run they are what
   the plan still has to build, not errors to fix now.
8. Tell the user, and stop: "Start a new session and ask your agent to build
   what's in `<the full path of build-plan.md>`. When it's done, run doctor
   again." Don't offer to build it in this session.

## Later runs while a build plan is open

If `build-plan.md` exists, run `$DR` and check each part in the plan against
the result. Mark the parts that now pass as done in the plan; rewrite the ones
still missing or broken with what is wrong. Tell the user what passed and what
is left (another fresh session for the rest). When every part passes, delete
`build-plan.md` and continue as an ordinary run.

The skills' own checks run only once the setup checks pass (config, mailbox,
local copy), so those parts come first. After that the feed parts are judged
by feed-wiring's check, the notifier by lane-urgent's, the rules by
mail-rules'.

## Every other run

```sh
$DR                 # about a minute: setup, health, need, prescriptions, changes since last time
```

Present the result short and in this order:

1. **Anything failing**, each with who fixes it: a skill the user can start,
   a plain request (when the fix belongs to an internal skill such as
   mail-rules or feed-wiring, e.g. ask: "fix the failing feed"), or the card
   section when the failure is outside svetovid (the notifier, the server,
   the network).
2. **Prescriptions**, numbered, in the order doctor prints them (sweep
   first, since its decisions feed route): the skill, the evidence in one
   line, and the command. A routine check-up says so ("nothing specific
   found, last run N days ago").
3. **Notes** that are not work yet (an order still in progress, folders to
   categorise), one line each.
4. **Since last time**: what got fixed, what is new.

Then stop. Do not start a prescribed skill, not even when the user says
"go": tell them to run the command (`<prefix><skill>`), and if several are
prescribed, suggest a fresh session for each long one (the sweep is long).
Each prescribed skill looks again when it starts (its own scan or audit,
which sees at least what its need script saw) and decides its own scope, so
nothing has to be passed on.

## Rules

1. **Never fix anything.** Doctor reads and reports. The skill that owns a
   part fixes it. The only files doctor writes are the first run's config
   and build plan, and its own history.
2. **Signals first.** A skill is prescribed for evidence of work. Time since
   its last run only makes a "routine check-up", with the reason.
3. **Blind to mail content.** Checks and needs print counts and names;
   never open mail to explain a prescription. The prescribed skill does
   that.
4. **No need, no prescription.** A skill with no evidence and no routine
   due is not mentioned.

## What the scripts are

Every skill folder may hold:

- `scripts/check` — health. One line per finding: `OK|WARN|FAIL <text>`;
  exit 1 on FAIL. A check reports and changes nothing, with one exception:
  mail-rules' check fast-forwards a clean rules checkout that is only behind.
- `scripts/need` — need. One JSON line: `{"skill", "work": [evidence],
  "last_run", "routine_days", "notes": []}`. `last_run` is the newest
  `- YYYY-MM-DD` line of `$SVETOVID_HOME/<skill>/runs.md`.

Doctor finds them by looking at its sibling skill folders, runs them in
parallel, and adds its own setup checks. A new skill joins by shipping them:
its check is run, and its need is prescribed after the skills doctor already
orders (add it to `ORDER` in `scripts/doctor` to place it).

History: `$SVETOVID_HOME/doctor/health-history.jsonl`, one line per run.
`doctor --json` prints the whole report for scripts or a timer.

Settings: `doctor.sync_max_age_h` (24: older local copy = warning),
`doctor.command_prefix` (`/`, or `/svetovid:` when installed as a plugin).
