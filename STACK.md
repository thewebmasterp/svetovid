# STACK.md — what svetovid needs underneath

This is the card for the system svetovid looks after. It states **what each
part must do** so the skills can work with it, which stack the author runs
(the *reference*, tested end to end), what else should work, and what you
lose without a part. It is not an install guide: point your agent at this
file, decide with it what to build for your own situation, and let
`doctor` check the result.

## What you must have

**A mail provider that runs Sieve filter rules you write yourself,** and
gives ordinary IMAP over TLS. The rules reach it by ManageSieve, by your own
upload hook on `git push`, or by pasting into the provider's web form
(`rules.upload`). What the providers offer:

- **Migadu** (reference), **mailbox.org**, **your own Dovecot server**:
  ManageSieve, so the skills upload the script and check that the server
  runs it.
- **Fastmail**: Sieve only through its web editor, no ManageSieve. Set
  `rules.upload = "browser"` and `rules.verify = "none"`; you paste, and
  only the probe mail proves what is live. Its editor mixes your code with
  blocks it generates itself.
- **Proton** runs Sieve on paid plans, but gives IMAP only through its
  Bridge app (on this machine, with STARTTLS and its own certificate), which
  the scripts do not speak. Not usable for now.

**Gmail and Outlook are not supported.** Their filters cannot express what
the skills rely on (variables, a defined order with "stop", header tests,
real folders). If your mail lives there, get an address at a Sieve provider
and forward the old account to it. Forwarded mail all arrives at one
address, so it cannot be told apart per service: treat it as one watched
folder ("Accounts you can't move") or sort it by kind ("Two ways to sort
mail"), and sign up to services with your new addresses from then on.

**A local copy of your mail**, kept in sync, with notmuch on top (the
"Local copy of your mail" row below). The skills replay every rule change
over it before the change goes live, and count from it.

**A Linux machine to run the skills on**, with Python 3.11 or newer, git,
and the usual tools the scripts call (`flock`, `timeout`, `pgrep`). Nothing
else is installed: the scripts use Python's standard library only.

## Two ways to sort mail

| | Per-service addresses (recommended) | Folders by kind (quick start) |
|---|---|---|
| How | every sign-up gets its own address (`<service>@<your domain>`, `you+<service>@`, or an alias service such as addy.io); the rules file each into its own folder | one address; the rules file mail by what it is (`deliveries-rss`, `newsletters-rss`) using the sender's domain |
| You get | you always know which service wrote; spam shows itself when it arrives at an address you never gave that sender; aliases keep you anonymous; a weekly sweep per service | the lanes (Urgent, deliveries) and feeds with much less setup |
| You lose | — | weaker evidence (shops send from several domains), no per-service folders for the sweep, "never ask again" is remembered per sender domain |
| Config | `[folders] service = "{svc}"`, `feed = "{svc}-rss"`, `deliveries = "{svc}-deliveries-rss"` | `deliveries = "deliveries-rss"` (no `{svc}`) |

The skills never hard-code a folder name; they read these templates.

## The parts

Each part by its role. **Reference** is the tested stack; alternatives are
described, not tested.

| Part | What the skills need from it | Reference | Alternatives (not tested) | Without it |
|---|---|---|---|---|
| **Mail provider with Sieve** | runs your script on delivery; IMAP over TLS with MOVE; ManageSieve to verify the live script (or `rules.verify = "none"`) | Migadu | mailbox.org, Dovecot + Pigeonhole; Fastmail without ManageSieve (see above) | nothing works |
| **Per-service addresses** | an address per sign-up that the script can tell apart (a header with the delivery address, or an alias header) | own domain `<svc>@me.<domain>` + `me+<svc>@`, addy.io aliases | plus addresses; another alias service (SimpleLogin, Fastmail masked email) once it has a module, see "Alias services" | use folders by kind |
| **Local copy of your mail** | a Maildir the skills replay rules over and read counts from; notmuch for tags and search | mbsync + notmuch | offlineimap + notmuch | rule changes can't be proven before they go live: **required** |
| **Notifier for Urgent** | announces new mail in the Urgent folder; can be paused, told what is already seen, and resumed (for big re-files); a health command | a small IMAP IDLE script of the author's with desktop notifications (not part of this repo) | a phone mail app that can notify for one folder (K-9/Thunderbird on Android); a desktop client's folder notifications | Urgent is just a folder |
| **Mail-to-feed bridge** | publishes listed mail folders as Atom feeds (interface below) | [mailfeed](https://github.com/thewebmasterp/mailfeed) | your own, built to the interface | deliveries and newsletters stay mail folders |
| **Feed hub** | groups several sources under a topic tag served as one feed; keyword (and optional AI) filters; reachable by the reader | [RSSBox](https://github.com/versun/RSSBox) | none tested: set `feeds.hub = "none"` and use reader categories | one feed per source in the reader |
| **Reader with an API** | create categories and subscriptions, report fetch errors | Miniflux | FreshRSS (different API: feed-wiring would need an adapter); any reader by hand via OPML | feeds are built but you subscribe by hand |
| **Website-to-feed** | turns a page into a feed | RSS-Bridge (stock and custom bridges), RSSBox; [Narro](https://narro.info) (a paid service) for social media profiles | any feed builder | web-feed can only use sites' own feeds |
| **Always-on host** | runs the bridge, hub and reader | a Raspberry Pi 5 with Docker | a NAS, a VPS, a hosted reader | feeds update only while your laptop runs |
| **Way in from the phone** | reach the reader from outside home | WireGuard | public HTTPS with login, Cloudflare Tunnel | read on the laptop only |

## Where the services run

| Setup | What works | What you lose |
|---|---|---|
| **Mail only** (Sieve provider + local copy) | Urgent, routing, sweep, lanes | lane mail ends in a mail folder, not a feed |
| **Docker on your laptop** | everything | feeds update only while the laptop runs; no reading from the phone |
| **An always-on box at home** (reference) | everything, the phone through a VPN | the box to look after |
| **Rented** (a VPS, a hosted reader) | everything | your mail credentials sit on someone else's machine; a monthly bill |

One thing stated precisely, so nobody is misled: **phone notifications for Urgent
do not need the always-on box.** Urgent is a folder on your provider's
server; any phone mail app that can notify for one folder does it. What the
box adds is feeds that keep updating while your laptop is off, and the reader
on your phone.

## Alias services

An alias service forwards mail to you and rewrites it on the way: From
becomes the alias, the real sender moves into a header of the service's
own, and a banner lands on top of the body. What svetovid knows about one
service is one small file, `lib/aliases/<service>.py`: which headers carry
the real sender and the alias, and what the banner looks like. Set
`mail.alias_service` to plug yours in.

The module that exists is addy.io's, because that is what the author uses.
For another service, copy `lib/aliases/addy_io.py` (it explains every
field), fill it in from a few real forwards in your mailbox, and contribute
it: a pull request with that one file is all the next user of the service
needs. Doctor tells you when your service has no module yet; until it has,
senders behind its forwards show as the alias.

## Accounts you can't move

A work account on Outlook or an old Gmail can still join, as one watched
folder:

1. Forward the account to its own alias on your Sieve provider (`work@`).
2. One rule near the top of the script files that alias into its own folder
   and stops, before the service rules.
3. The notifier watches that folder as a whole (optionally only in working
   hours). The skills leave it alone: list it under `[[forwarded]]` in the
   config.

You lose per-service sorting for that mail (it all arrives at one address).
Many companies block forwarding to outside addresses; Gmail asks you to
confirm the forwarding address first.

## The Sieve script

The skills edit one script kept in a git repository (`rules.repo`,
`rules.script`) that has a remote named `origin`: its `rules.branch` there
is what counts as live, and every workspace is branched from it. Any git
host will do, or a bare repository on the same machine. A starter with the
structure and no keywords is in [examples/main.sieve](examples/main.sieve).
The skills rely on this shape:

```sieve
require ["variables", "fileinto", "mailbox"];

# 1. Identity: which service is this mail for?
set "svc" "";
if header :matches "X-Envelope-To" "*@me.example.org" { set :lower "svc" "${1}"; }
# (plus forms, alias headers, ...)

# 2. Accounts you can't move: their folder, stop.
if header :is "X-Envelope-To" "work@example.org" { fileinto :create "Work"; stop; }

# ---- URGENT: decide only (sets the class, never files)
set "why" "";
if header :contains "Subject" ["verification code", "new login"] { set "why" "auth"; }
# ...

# ---- FOLD: service mail only
if not string :is "${svc}" "" {
    if not string :is "${why}" "" { fileinto :create "Urgent"; stop; }   # Urgent is a move
    # ROUTE blocks: one self-contained block per service or lane
    if allof (string :is "${svc}" "example", header :contains "Subject" "invoice") {
        fileinto :create "example-rss"; stop;
    }
    fileinto :create "${svc}"; stop;
}
# anything else: implicit keep (INBOX)
```

- The service variable (`rules.service_var`, default `svc`) and the class
  variable (`rules.class_var`, default `why`) carry those names; Urgent is
  `rules.urgent_folder`.
- Comment lines `# ---- NAME` mark sections.
- The skills' replay (`sieve-sim`) runs the script as written. It knows the
  Sieve that filing needs (`sieve-sim --help` lists it); a rule outside that
  set stops it, on purpose: rewrite the rule.
- Your provider must accept the same script (the skills ask its ManageSieve
  `CHECKSCRIPT` before every upload when it has one).
- After every landing the skills send real test mail and check where it
  arrived (`[[rules.probe.case]]` in the config: an address, the folder it
  must land in). Sending needs port 25 out to your provider's MX
  (`via = "mx"`), or authenticated submission (`via = "submit"`). Without
  cases the step is skipped and doctor warns: an upload alone does not prove
  that the provider runs your script on delivery.

## The mail-to-feed bridge (interface)

The skills (feed-wiring) talk to the bridge through files and HTTP:

- It reads a **read-only copy** of the mail (a Maildir), never the live
  mailbox. Nothing in the chain moves, flags or deletes mail.
- Its config is a TOML file, `feeds.toml`, in `feeds.bridge_dir`, re-read
  on every pass. File-wide settings on top, then one table per feed:

  ```toml
  skip_subject = "..."        # regex of subjects no feed publishes (login codes, passwords), in your own wording
  sender_headers = ["..."]    # your alias service: the header with the real sender,
  strip_html = ["..."]        #   its banner in HTML bodies (regexes),
  strip_text_lines = ["..."]  #   and in plain-text ones (feed-wiring writes these three from the module)

  [example-rss]               # the feed's name = its address /<name>.xml
  folder = "example-rss"      # default: the name
  title = "Example Newsletter"
  from = ["news@example.com"] # optional: only these senders (globs; alias forwards: the original sender)
  skip_subject = "..."        # optional: this feed's own pattern ("" publishes everything)
  max_entries = 50
  title_prefix = "Shop"       # optional: "Shop · " before every entry title
  title_regex = "..."         # optional: entry titles from the body (named groups),
  title_item = "{a} {b}"      #   with title_item per match and
  title_format = "{items}"    #   title_format over {items} {subject} {date}
  ```
- It serves `<bridge_url>/<name>.xml` (Atom, one `<entry>` per mail) inside
  your private network only. It has no login: whoever can reach it can read
  the feeds.
- It runs in a Docker container (`feeds.bridge_container`) with a health
  check, on the port named in `feeds.bridge_url`, from an image that has
  `python`. feed-wiring restarts it, asks its health and counts a feed's
  entries from inside it.
- Its host (`feeds.host_command`) has `docker`, `flock` and Python 3.11 or
  newer, and holds both `feeds.bridge_dir` and the mail copy
  (`feeds.mirror`).

**Acceptance checks** for your own bridge (each one was a real bug):
the real sender behind alias forwards is used for `from` and the author;
an alias service's banner and "deactivate" links never reach an entry;
entry ids stay stable, so a mail never shows up twice; digest mails can be
split into one entry per item; the title prefix works; the host name is one
your hub accepts as a URL (some reject names without a dot: use
`<name>.internal`).

## The hub and the reader (interfaces)

- **Hub:** feed-wiring drives RSSBox through its Django shell
  (`docker exec -i <hub_container> python manage.py shell`) on the host
  reached with `feeds.host_command`. A tag's feed is
  `<hub_tag_url>/<tag>`. Without a hub, set `feeds.hub = "none"`.
- **Reader:** the Miniflux API at `feeds.reader_url` with a token printed by
  `feeds.reader_token_command`.

## Secrets

Never in the config. The config holds commands that print them
(`mail.password_command`, `feeds.reader_token_command`), typically keyring
lookups. The skills read them at run time and never store or print them.

## Checking your setup

Run the doctor skill. Its first run, with no config, asks what you have,
writes `config.toml` from `config.example.toml` and a build plan for the
parts you lack, and stops; you have your agent build the plan in a fresh
session. Every later run checks the parts above, then each skill's own
health and need.
