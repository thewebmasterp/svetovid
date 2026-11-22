---
name: feed-wiring
description: Shared svetovid skill that connects a source to what the user reads — publishes a mail folder through the mail-to-feed bridge (mailfeed), adds it or any other feed URL to the feed hub under a topic tag (RSSBox), and subscribes the reader to the tag (Miniflux); also lists, checks and removes channels. Used by the route, lane-deliveries and web-feed skills when their work ends in a feed, and when the user asks directly to "make a feed from <service>", "add this to the <topic> tag", "why is <feed> not arriving in the reader", or to list, check or remove a channel. Not for routing mail into folders (mail-rules, route) and not for deciding what a website feed is built from (web-feed).
user-invocable: false
metadata:
  version: "2.0.0"
---

# feed-wiring

The fixed part of every feed: the chain, the agreed constraints, and one
command per layer so nothing has to be rediscovered. Which mail becomes a
feed, and where it goes, is decided case by case with the user.

## Before anything

1. Read the user's notes, if they have any yet: `$SVETOVID_HOME/feed-wiring/notes.md` (their own
   decisions, which win where they are more specific than this file) and,
   when a case goes beyond the commands, `$SVETOVID_HOME/feed-wiring/stack.md`
   (facts about their hosts, timers and known bugs) if it exists.
2. Settings come from the `[feeds]` and `[folders]` tables of
   `$SVETOVID_HOME/config.toml`. If it is missing, stop and tell the user to
   run the doctor skill.

```sh
F=<this skill's folder>/scripts/feeds
python3 -I $F list      # every mail channel and how far down the chain it is wired
python3 -I $F tags      # every hub tag, its sources, its reader feed
```

Start with these two: they show what exists, so the request can be placed
against it (is there a tag for this topic? is the folder already published?).
On "Permission denied" or "no reader token", ask the user to unlock their
key agent or keyring; never look for the secrets elsewhere.

## The chain

```
sender -> an address that sieve files into a folder named by [folders] feed
          (per-service setups: "<svc>-rss")
       -> the bridge's copy of the mail (read-only)
       -> the bridge publishes <bridge_url>/<name>.xml, only for folders
          listed in its feeds.toml (whitelist)
       -> hub source "<source_prefix><title>" under a topic tag
       -> the reader follows the tag (<hub_tag_url>/<tag>)
```

Each arrow is its own layer with its own command; a channel need not use all
of them. With `feeds.hub = "none"` there is no hub: a tag is a reader
category and the reader follows each feed directly.

## Constraints

They hold for every case. If a request conflicts with one, say so and ask.

1. **On request, one channel at a time.** Never turn folders into feeds
   because they look suitable, never "all mail as a feed".
2. **Whitelist only.** A folder is published only when it has a table in the
   bridge's `feeds.toml`. Everything else stays mail.
3. **Mail is the record.** Nothing here moves, deletes or marks mail. The
   bridge's copy is append-only, so never send test mail to a real service
   folder: it would stay in that feed for good. Test with a throwaway feed
   name on an existing folder and remove it afterwards.
4. **A tag is a topic**, and may hold several kinds of source (a newsletter
   and a web page about the same town). The reader follows the tag, so the
   user sees one feed per topic. Adding a source to a tag needs no reader
   change.
5. **A tag's name is its address**: lowercase letters, digits, dashes.
   Renaming it breaks the reader's subscription, so agree on the name first.
6. **Source names carry a type prefix** in the hub (mail sources:
   `feeds.source_prefix`). The user's list of prefixes and reader
   categories is in their notes.
7. **No AI on mail unless asked.** Hub summaries, filters and digests send
   text to an outside model. The user decides per channel; never attach one
   unprompted, and say what would be sent when they ask.
8. **Private mail stays out of feeds.** Mail whose subject says login code
   or password is skipped by the bridge's file-wide `skip_subject`. That
   pattern is the user's own, in their languages; nothing is built in. Set
   it before the first channel, from the wording of their real mail (their
   Urgent keys for codes and logins are the best source), and extend it when
   a new wording turns up: `feeds skip-subject [--set '<regex>']`. `check`
   warns while there is none. For a service that mixes a newsletter with
   account mail, publish only the newsletter (see the shapes).
9. **The feeds stay inside the private network.** No published port and no
   public proxy host for the bridge: the feeds contain mail.
10. **Do not chase delivery.** New mail takes the bridge's copy interval +
    the bridge's pass + the hub's fetch interval + the reader's polling.
    Leave the timers alone; the commands restart the bridge only so that a
    new channel is live at once.
11. **A folder that feeds RSS is named by the `feed` template** (per-service:
    `<svc>-rss`), so the folder list alone shows what is published. A
    newsletter is signed up with its own address that sieve files into that
    folder, separate from the account address at the same service. Never
    publish a plain service folder without asking.
12. **Rules move, never copy, never drop.** A rule that fills a feed folder
    moves the mail there (mail-rules does that). Slop is not filtered with
    rules at all: it is switched off in the service's own settings (the
    route skill does that, with the user).
13. **Not every channel goes to the reader.** A source can live in the hub
    only, untagged (`source-add` without `--tag`), when the user wants to
    look at it there first. Do not subscribe it unless asked.

## Working out a case

Ask only for what the request leaves open, in one question:

- **Which mail?** A folder, and whether all of it or one sender.
- **Where does it go?** An existing tag, a new tag, or straight into the
  reader with no bundling.
- **For anything new in the reader:** which category, and the title.

If the user has not signed up yet, give them the address that files into the
feed folder (per-service: `<svc>-rss@<their service domain>`, or an alias
that starts with `<svc>-rss.`) and carry on: a channel can exist before its
first mail and stays empty until then. Check first whether a plain `<svc>`
folder already holds their account mail and say so: it is why the newsletter
gets its own address.

Look at the folder before deciding its shape:

```sh
python3 -I $F senders <folder>
```

It lists each sender with a count, how many of their mails carry
mailing-list headers, and the latest subject (long digit runs masked). Tell
the user which senders would be in and which stay out: that is the privacy
decision.

### Shapes a channel can take

| Situation | Shape |
|---|---|
| New sign-up (the default) | Address that files into `<svc>-rss`; publish the whole folder |
| The newsletter already arrives in a plain `<svc>` folder next to account mail | First choice: the user re-subscribes with the feed address. Otherwise a rule (route skill, through mail-rules) moves the wanted mail into `<svc>-rss`, then publish that folder whole |
| Same, and the user explicitly accepts publishing from the service folder | `--from <newsletter sender>`; account mail never enters the feed. Breaks constraint 11, so only on their say |
| One sender address sends both newsletter and account mail | A sender filter cannot split it. Re-subscribe with a feed address, or no channel |
| Read-everything source that needs no bundling or filtering | `--direct`: the reader reads the mail feed itself, the hub is skipped |
| Topic with several sources | One tag; add each source to it, mail or not |
| Notification-heavy platform | First tune the platform's email settings with the user, then a rule moves the wanted kind (often by a type header) into `<svc>-rss` and personal mail to INBOX (route skill) |
| User wants it in the hub but not the reader yet | `feed-add`, then `source-add` without `--tag` |

## Commands

Every `add` is idempotent: after a failure, run the same line again and it
completes what is missing. `--dry-run` on `feed-add` and `add` validates
without changing anything.

**Whole chain, the common case:**

```sh
# mail folder -> feed -> hub source "<prefix><title>" under a tag -> reader
python3 -I $F add --name <name> --tag <tag> [--folder <folder>] [--title "Title"] \
    [--from <sender> ...] [--category <Category>] [--miniflux-title "Title"] [--title-prefix "Shop"]

# mail folder -> feed -> reader directly, no hub
python3 -I $F add --name <name> --direct --category <Category> [--title "Title"]
```

`--category` and `--miniflux-title` only matter when the reader does not
follow the tag yet; an existing subscription is left alone.

**One layer at a time, for cases that do not fit:**

```sh
# bridge only: the subjects no feed may publish (show it, or set it)
python3 -I $F skip-subject [--set '<regex>']
# bridge only: what the alias service's module knows (real sender, banner);
# run it once at setup and after the module changes. `check` warns when it is due.
python3 -I $F alias-sync

# bridge only: publish a folder (optionally one sender) as /<name>.xml
python3 -I $F feed-add --name <name> [--folder F] [--title T] [--from ADDR ...] \
    [--keep-codes] [--max-entries 50] [--title-regex R --title-item I --title-format T] [--title-prefix P]
python3 -I $F feed-remove --name <name>

# hub only: ANY feed URL as a source under a tag (a mail feed, a web feed, a
# video channel, a blog). This is how a second source joins a topic.
python3 -I $F source-add --url <feed url> --name "<prefix> Name" [--tag <tag>] [--every 60]
python3 -I $F source-remove --url <feed url> [--purge]

# reader only: follow a tag, or a URL directly
python3 -I $F subscribe --tag <tag> --category <Category> [--title "Title"]
python3 -I $F subscribe --url <feed url> --category <Category> [--title "Title"]
```

**Removing a channel** (confirm first: stored entries are deleted):

```sh
python3 -I $F remove --name <name> [--purge]
```

It takes the table out of `feeds.toml` (refusing to write a broken file) and
deletes the hub source. A tag with other sources is never touched. A tag left
empty, its reader feed and a direct subscription are kept unless `--purge` is
given: the user may want the history or plan another source. Without a hub
(`feeds.hub = "none"`) it takes the feed off the bridge and, with `--purge`,
out of the reader.

**Entry titles:** `--title-prefix "<Shop>"` puts `"<Shop> · "` before every
entry title. Lane feeds that merge many senders (lane-deliveries) use it so
courier mail still names the shop. `--title-regex/--title-item/--title-format`
build titles from the body (named groups), e.g. an amount on an invoice.

**Naming:** `--name` is the feed address and the `feeds.toml` table
(lowercase, digits, dash, underscore). Use the folder name. `--folder` is
needed when it differs from the name, e.g. a folder with a dot.

## Check (for doctor)

`scripts/check` prints one line per finding and exits non-zero when
something is wrong: every channel in `feeds.toml` is published, its source
is in the hub with a working fetch, and the reader follows its tag without
errors. With no `[feeds]` in the config (mail only) it says so and passes.

## Report

After any change run `list` (or `tags`) and tell the user plainly what is
published (whole folder or which sender), which tag and reader feed it is in,
and how many entries are there now. If the first mail is a "confirm your
subscription" message, remind them to click it.

## When something is off

- **0 entries although mail arrived:** `senders <folder>`. Wrong folder name,
  a `--from` that does not match (forwards from alias services are matched on
  the original sender), or the subject hit the login-code filter.
- **Mail arrived minutes ago:** wait for the bridge's copy
  (`mail-rules/scripts/rules-wait-mirror <folder>`), then check the bridge's logs.
- **In the hub but not in the reader:** the hub fetches on its own interval;
  repeating `add` or `source-add` forces a fetch.
- **An alias service's banner or "deactivate alias" link in an entry:** the
  banner patterns missed a new layout. Fix them in the service's module
  (`lib/aliases/`), then `feeds alias-sync` hands them to the bridge: those
  signed links must not be published.
- Anything else: the user's `stack.md`.

## Keeping this skill current

When a case teaches something lasting, put it where it belongs, in the same
session, and tell the user: a general rule or command here (it is public:
no names, hosts or addresses), anything about the user's own setup or
choices in `$SVETOVID_HOME/feed-wiring/notes.md` or `stack.md`.
