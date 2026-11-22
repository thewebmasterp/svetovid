---
name: mail-rules
description: Shared svetovid skill that changes the user's Sieve mail rules safely — opens a private workspace (git worktree), replays the change over the whole mail archive with sieve-sim (an interpreter for the Sieve subset filing scripts use), lands it under a lock (rebase, validate, upload, verify the server runs it, probe with real mail), re-files mail already on the server, and closes the workspace. Owns the layout of the Sieve script and its tools (sieve-sim, sieve-server, sieve-refile, sieve-probe, rules-*). Used by the route, lane-urgent and lane-deliveries skills whenever they need a rule written or changed, and when the user asks to replay, explain, deploy, probe or re-file. Several agents can use it at once. Not for deciding where mail should go; that is the calling skill's job.
user-invocable: false
metadata:
  version: "2.0.0"
---

# mail-rules

Every rule change in svetovid goes through here, so it is tested the same way
every time: on all the mail the user has ever received, before it is live,
and with real mail after. The calling skill decides *what* the rule does;
this skill makes the change safe.

## Before anything

1. Read `$SVETOVID_HOME/mail-rules/notes.md` if it exists: the user's provider gotchas and
   repo conventions (where changes are logged, block order). Where it is more
   specific than this file, it wins.
2. Settings: `[mail]`, `[rules]`, `[notifier]` in `$SVETOVID_HOME/config.toml`.
   Missing: stop and tell the user to run the doctor skill.

```sh
R=<this skill's folder>/scripts      # prefix every tool below with $R/
```

## The script layout

The skills read and edit one Sieve script (`rules.repo`/`rules.script`, a git
repo). They rely on this shape, also described in STACK.md:

- **Identity first.** The top of the script works out which service a mail
  belongs to and sets the variable named by `rules.service_var` (default
  `svc`), from the address it arrived at. Mail for a forwarded account is
  filed into its own folder and stops before anything else.
- **`# ---- URGENT`** sets the class variable `rules.class_var` (default
  `why`) to a class name (`auth`, `security`, ...) or leaves it empty. It
  only decides; it never files. Its rules read the Subject, so they cover
  any service.
- **`# ---- FOLD`** runs for service mail only. First: a non-empty class
  moves the mail into `rules.urgent_folder` and stops. Then the ROUTE blocks,
  one self-contained block per service (and the lane blocks, e.g.
  DELIVERIES), each ending in `fileinto ...; stop;`. Last:
  `fileinto :create` the service folder (the `[folders] service` template).
- Comment lines `# ---- NAME` mark sections; sieve-sim reports reasons as
  `<SECTION>:L<line>`.

sieve-sim runs this script as written, it does not keep a copy of the rules.
It understands the Sieve subset listed in `sieve-sim --help`; anything else
stops it with the line number. That is on purpose: a rule nobody can replay
is a rule nobody can test, so rewrite the rule instead of extending the
simulator.

## Parallel model

| Shared thing | How it stays safe |
|---|---|
| the rules repo (its main branch is what is live) | each agent works in its own worktree + branch `rules-<name>` from `rules-start`; the main checkout is never edited by hand |
| the live script on the server | only `rules-land` uploads: rebase, validate, upload, verify the server's copy equals yours |
| probe mail (`sieve-probe --clean` deletes all of it) | sent and cleaned inside `rules-land`, under the lock; a hand-run `sieve-probe` for diagnosis may send, but never `--clean` |
| IMAP moves, notifier pause, local sync | `rules-refile`, under the same lock |
| two agents on the same name | `rules-start` refuses (the workspace exists) |

The lock lives in `$SVETOVID_CACHE/rules/land.lock`. A waiting agent prints
"waiting for the lock" and continues by itself. Read-only steps (`rules-sim`,
`sieve-sim`, `sieve-server list/get/check/same`) never take it.

## Procedure

### 1. Open a workspace

```sh
$R/rules-start <name>          # usually the service or lane name
```

Edit `$SVETOVID_CACHE/rules/<name>/sieve/<script>` and the repo's docs there
(`rules-start` prints the path; the cache defaults to `~/.cache/svetovid`).

### 2. Write the change

- A **route** goes in FOLD's ROUTE part, before the final service-folder
  `fileinto`, as one self-contained block (keep blocks in the order the
  user's notes ask for, e.g. alphabetical, so parallel edits stay apart):

  ```sieve
      # <Service> (decided YYYY-MM-DD): what goes where, what stays and why.
      if allof (string :is "${svc}" "<svc>",
                address :domain :is "From" "<domain>", <test>) {
          fileinto :create "<svc>-rss"; stop;          # or fileinto "INBOX"
      }
  ```

- An **Urgent** rule goes in URGENT as `set "why" "<class>"` under a test.
  A scoped undo for one service goes at the end of URGENT:
  `if allof (string :is "${svc}" [...], <test>) { set "why" ""; }`.

### 3. Prove it (read-only)

```sh
$R/rules-sim <name> --diff                 # every message your change files differently (against the script you branched from)
$R/rules-sim <name> --show <folder> -n 50  # what would land in a folder
$R/rules-sim <name> --explain <file>       # trace one message through the script
$R/rules-sim <name> --refile <folder>      # the server's view, dry run: counts must match
```

The whole archive is the regression suite. Every `+ newly into Urgent` line
must be worth an interruption, no `- no longer into Urgent` line may be a
real code or alert, and every other move must be one the caller asked for.
A key that fixes one miss and adds five newsletters is the wrong key.
A `!! delivered to more than one folder` block in the diff means a rule lost
its `stop` (the server would leave a copy in each folder): fix it first.

Then log the change where the user's notes say (e.g. the repo's README and
audit log) and commit on `rules-<name>`.

### 4. Land (locked)

```sh
$R/rules-land <name>
```

| Exit | Meaning |
|---|---|
| 0 | live, verified, probes passed |
| 1 | stopped before the script was live; the message says why (bad workspace name, lock timeout, the push was refused, the server runs another script). Fix that and rerun |
| 2 | rebase conflict: another agent landed next to you. In the worktree: `git rebase origin/<branch>`, keep both blocks, `git rebase --continue`, rerun |
| 4 | deployed but a probe failed: investigate now (`$R/sieve-probe --report <token>`); the failing case's hint is printed |
| 5 | `rules.upload = browser`: paste the printed file into the provider's editor, then `rules-land <name> --uploaded` |

The probe step needs `[[rules.probe.case]]` in the config. With none it is
skipped, and `rules-land` says the landing was not proven with real mail.

### 5. Re-file existing mail (locked)

```sh
$R/rules-refile <folder> [--to <dest> ...] [--quiet-urgent]
```

It classifies with the deployed script. Use `--to` to move only what the
caller decided (other destinations are not its decision). Use
`--quiet-urgent` when unread mail will move into Urgent: the notifier is
paused and told the moved mail is already seen. Report before/after counts.

### 6. Wait for the bridge, close

```sh
$R/rules-wait-mirror <folder> [count]   # until the feed bridge's copy has it (if there is one)
$R/rules-done <name>                    # refuses while anything is unlanded
```

Feeds for the new folders are feed-wiring's job.

## The tools

| Tool | What it does |
|---|---|
| `sieve-sim` | runs the script over the local copy: summary, `--show`, `--moved`, `--urgent`, `--audit --since D`, `--diff OLD`, `--explain FILE`, `--live`, `--check` |
| `sieve-server` | ManageSieve: `list`, `get`, `check FILE` (the server validates), `put`, `activate`, `same FILE` |
| `sieve-refile` | re-file one server folder with a script (dry run unless `--apply`) |
| `sieve-probe` | real mail through the provider per `[[rules.probe.case]]`; `--report`, `--clean` |
| `rules-*` | the workspace cycle above |
| `check` | health for doctor (below) |

Other skills import sieve-sim as a module (`Script`, `load`, `outcome`,
`classify`, `live_script`) instead of re-implementing filing.

## Check (for doctor)

`scripts/check`: the server's active script is exactly what is on the repo's
main branch, sieve-sim can execute every rule in it, the main checkout is
clean and current (a clean checkout that is only behind is fast-forwarded:
the replay reads it), and probe cases exist. One line per finding
(OK/WARN/FAIL), exit 1 on FAIL.

## Sieve gotchas

- The default comparator folds case for ASCII only: a key in another script
  (Cyrillic, Greek) matches case-sensitively. Drop the word's first letter,
  so the key matches it both capitalised and in lower case.
- Senders sometimes use look-alike letters from another alphabet in a
  Subject: match the sender instead.
- `address` tests take address headers only (From, To, Cc, Sender, Reply-To);
  for `X-*` headers use `header`.
- Forwarded mail from an alias service carries the real sender in a header
  of the service's own; match it, not From. The service's module names it
  (`SENDER_HEADERS` in `lib/aliases/<service>.py`).
- `:regex`: the server reads POSIX regex, the replay Python's. sieve-sim
  refuses POSIX classes (`[[:digit:]]`); write them out (`[0-9]`).
- `[[rules.pin]]` in the config keeps old mail where it is, in the replay
  and in `rules-refile` alike (mail no rule describes any more). The server
  never sees pins.
- `envelope` is often a no-op on hosted providers; providers stamp the
  delivery address in a header (e.g. `X-Envelope-To`) instead. sieve-sim
  does not run `envelope`.
- "MISMATCH or still in transit" from a probe is usually transit; `rules-land`
  re-checks once. Never run `sieve-probe --clean` outside `rules-land`.
- A temporary SMTP refusal (4xx) while probing means several agents probed
  within minutes. The deploy already happened: wait a few minutes and rerun
  `rules-land <name> --uploaded`.

## Keeping this skill current

General lessons go here (public: no names, hosts or addresses); anything
about the user's provider, repo or choices goes in
`$SVETOVID_HOME/mail-rules/notes.md`. Tell the user what you added.
