---
name: web-feed
description: Turn one website (or a page of it) into a feed in the user's reader — find the cheapest source that really works (the site's own feed, a public feed someone maintains, a stock bridge, a custom RSS-Bridge bridge, or a small dedicated container), survey the page's real format before parsing it, keep the scraping polite, cut the noise with keyword filters first and AI filters only when asked, verify dates and ids against real data, then hand the feed to feed-wiring for the hub tag and the reader. Also fixes a web source that broke or went silent. Use when the user says "make a feed from <site>", "I want <site>'s <section> in my reader", "watch this page for <thing>", "is there an RSS for <site>", "<feed> stopped updating", "add <site> to the <topic> tag", or runs /web-feed. Not for mail (feed-wiring, route) and not for the hub/reader layers alone (feed-wiring).
metadata:
  version: "1.0.0"
---

# web-feed

One website at a time: find the cheapest source that really works, make it
trustworthy, and wire it in. Built from the cases the author did by hand
(outage notices, a water utility's breakdown page, job boards, a social
network's public profiles, release notes); the general lessons are here,
the cases themselves in the user's notes.

**Started without being asked?** Ask before building anything new; fixing a
source doctor reported is fine after one line saying what you will do.

## Before anything

1. Read, if they exist yet, `$SVETOVID_HOME/web-feed/notes.md` (the user's rules) and
   `$SVETOVID_HOME/web-feed/sources.md` (every web source built so far: how
   it works, its quirks). The closest precedent saves most of the work.
2. Wiring into the hub and reader is **feed-wiring**'s job (load it at the
   end). Settings: `[feeds]` and `[web_feed]` in the config.

## 1. Pin down the request

In one round of questions, only what is open: which site and which part of
it, what the user wants to see (every item, or only items about X), where it
goes (an existing topic tag, a new one, straight into the reader), and for
filtered feeds which way to err ("a false pass is better than a miss", or
the reverse).

## 2. Find the source: cheapest that works, in this order

1. **The site's own feed.** Look for `<link rel="alternate" type=
   "application/rss+xml">`, `/feed`, `/rss`, `/atom.xml`, a CMS's default
   paths. **Fetch it and check it is real XML**: some sites serve an HTML page
   at their feed URL. Check how far back it reaches (a feed holding 15 items
   covers only a few hours on a busy site; then the hub must fetch often
   enough) and whether per-category feeds work.
2. **A feed someone already maintains** (community feed repositories, feed
   generator services; for social media profiles a hosted service such as
   [Narro](https://narro.info)). Prefer it over building one, but check it
   is alive (recent commits or items) and says where it comes from.
3. **A mail alert.** Many sites (job boards, shops, forums) mail saved
   searches; a dedicated address routed into a feed folder (route +
   feed-wiring) is often more reliable than scraping.
4. **A stock bridge** (RSS-Bridge's generic XPath/CSS bridges, the hub's
   own scraper) when the page is a plain list with one link per item.
5. **A custom bridge** (one PHP file for RSS-Bridge) when items need logic:
   sections that run until the next heading, several items per page, dates
   inside text, API calls behind the page. Keep it where the user's
   RSS-Bridge loads custom bridges from (their notes say where, and how it
   is deployed) and document it in `sources.md`.
6. **A small dedicated container** only when nothing above can do the job
   (a page that needs a real browser to render, fetching that needs state or
   pacing no bridge can keep). It is real infrastructure: agree on it with
   the user first.

Getting around a login wall, an anti-bot check or a site's terms is out of
scope: svetovid does not help with it, by any of the ways above. If that is
the only way in, say so and propose an alternative (a mail alert, a site that
mirrors the same data, a service that offers the feed).

## 3. Survey the real format before parsing

Read a large sample, not one page: archive pages (`?page=N`) back several
months. Write the format rules down before coding: what opens an item, what
closes it, which notes belong to it, where the date is, how the site writes
the thing the user cares about (abbreviations, spelling variants, typos).
Format edge cases found in the archive become test cases.

## 4. Be polite to the site

- Fetch no more often than the content changes (most lists: 30–60 min).
- Cache what does not change (detail pages); cap pages per run; space
  requests out.
- On 429/503: back off for real (a cooldown of hours, no probing during it)
  and log it where the user can see it. Probing during a ban keeps
  restarting it.
- Errors must not become feed items: configure the bridge to answer with an
  HTTP error, so the hub marks a failed fetch instead.

## 5. Filters: keywords first, AI only when asked

- **Static keywords** in the hub (include or exclude, title or content) cut
  most noise for free. Test them against the surveyed archive: every wanted
  item matches, a sample of unwanted ones does not. Watch the hub's matching
  rules (case folding may be ASCII-only; some feeds rewrite characters such
  as hyphens). svetovid has no command for hub filters: set them in the
  hub's own admin, and record what you set in `sources.md`.
- **AI filters** only when the user asks: they send each item's text to an
  outside model. Say what would be sent. Build the prompt on real data, with
  a test kit of labelled items, and measure misses before switching it on.
  When the user prefers false passes over misses, combine a wide keyword net
  with the AI, never a narrow one.

## 6. Verify

- Run the bridge (or the feed) against the surveyed period and compare item
  by item with what the user would expect (a small script simulating the
  rules is a good referee).
- **Dates:** check that items show the right time in the reader. Time zone
  bugs (a UTC time read as local) shift everything by hours.
- **Ids:** decide what makes an item new. An id from the URL dedupes
  reposts; an id from the content makes a later edit a new item. Ask which
  the user wants when it matters.

## 7. Wire it in (feed-wiring)

```sh
python3 -I <feed-wiring>/feeds source-add --url <feed url> --name "[Site] Topic" --tag <tag> [--every 30]
```

Source names follow the user's prefix rule (their notes). Then the reader
step if the tag is new (`subscribe`). Record the source in
`$SVETOVID_HOME/web-feed/sources.md`: URL, method, bridge file, quirks,
filters, why it was built.

## Fixing a source doctor reported

`<feed-wiring>/feeds web-health` shows every web source with its fetch
status, how long it has been silent and its usual gap.

1. A fetch error: fetch the URL yourself. Gone (404/410) or moved (301):
   find the new address. Blocked: back off, check the bridge's cooldown
   handling. Broken markup: read the page again and adjust the bridge.
2. Silent past its usual gap but fetching fine: look at the site. Nothing
   new published is not a fault (say so; add the name to `web_feed.ignore`
   if the user wants it quiet). Content published but not picked up means
   the parsing broke: back to section 3 above (survey the real format).
3. Note what happened in `sources.md`.

## Need (for doctor)

`scripts/need`: a web source the hub cannot fetch, or one that usually posts
within `web_feed.busy_gap_h` (48 h) and has been silent for more than
`web_feed.silence_factor` (5) times its usual gap and at least 72 h. Slow
sources going quiet is normal. Names in `web_feed.ignore` are skipped.

## Keeping this skill current

General lessons go here (public: no names, hosts or addresses); the user's
sources and rules in `$SVETOVID_HOME/web-feed/`.
