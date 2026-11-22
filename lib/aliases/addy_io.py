"""addy.io (formerly AnonAddy): what svetovid needs to know about its forwards.

An alias service receives mail at an alias and forwards it to your mailbox,
rewriting it on the way. This file is the whole of svetovid's knowledge about
one such service; `mail.alias_service = "addy.io"` in config.toml plugs it in.

To support another service (SimpleLogin, Fastmail masked email, ...), copy
this file to lib/aliases/<name>.py (lower case, anything that is not a letter
or digit becomes "_"), fill it in from a few real forwards in your mailbox,
set mail.alias_service to the name, run doctor, and please contribute the
file: a pull request with the module is all another user of that service
needs. Leave a field empty when the service has no such thing.
"""

NAME = "addy.io"

# The forward's From is the alias. Where the real sender is:
SENDER_HEADERS = ("X-AnonAddy-Original-Sender",)        # the address that sent it (the envelope sender)
DISPLAY_HEADERS = ("X-AnonAddy-Original-From-Header",)  # the From line the sender wrote, name included

# The alias the mail was addressed to (what the script reads the service from):
RECIPIENT_HEADERS = ("X-AnonAddy-Original-To",)

# Headers the service adds that say nothing about what kind of mail this is
# (a regex on the lower-cased header name; hidden when a folder is broken down):
NOISE_HEADERS = r"x-anonaddy-(authentication|original-(to|envelope))"

# The service adds its own List-Unsubscribe to every forward. A link to one of
# these hosts is the service's, so it does not make the mail a mailing:
OWN_DOMAINS = ("addy.io", "anonaddy")

# The banner on top of every forward, as it reads once the body is plain text
# on one line (regexes, tried in order, each removed once from the start):
BANNER_TEXT = (
    r"^This email was sent to .{0,400}?deactivate this alias",
    r"^.{0,400}?Block domain\s*",
)

# The same banner in an HTML body, and the links that act on the alias. They
# are signed one-click links: they must never be published in a feed.
BANNER_HTML = (
    r"<div\b[^>]*\bid=[\"']addy-banner[\"'].*?</div>",
    r"<a\b[^>]*href=[\"']https://app\.(?:addy\.io|anonaddy\.com)/[^>]*>.*?</a>",
)

# In a plain-text body, lines holding one of these are the service's own:
BANNER_LINES = ("app.addy.io/", "app.anonaddy.com/")
