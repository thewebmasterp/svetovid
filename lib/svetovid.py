#!/usr/bin/env python3
"""Shared helpers for svetovid's scripts: where your data lives, and your config.

Your data never lives in this repo. It lives in SVETOVID_HOME:

    $SVETOVID_HOME                       (default: $XDG_CONFIG_HOME/svetovid)
    ├── config.toml                      the filled-in card (see config.example.toml)
    └── <skill>/                         notes.md, state.json, runs.md, ...

Scratch files go to SVETOVID_CACHE (default: $XDG_CACHE_HOME/svetovid).

From Python (a script in skills/<name>/scripts/):

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
    import svetovid as sv
    sv.get("rules.repo")            -> value (KeyError if unset and no default)
    sv.path("mail.maildir")         -> expanded Path
    sv.folder("deliveries", "exampleshop") -> "exampleshop-deliveries-rss" (from [folders])

From a shell script:

    lib/svetovid.py get rules.repo
    lib/svetovid.py path mail.maildir
    lib/svetovid.py home | cache
"""
import os
import subprocess
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
_MISSING = object()
_CONFIG = None


def home():
    env = os.environ.get("SVETOVID_HOME")
    if env:
        return Path(env).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(base).expanduser() / "svetovid"


def cache():
    env = os.environ.get("SVETOVID_CACHE")
    if env:
        p = Path(env).expanduser()
    else:
        p = Path(os.environ.get("XDG_CACHE_HOME") or "~/.cache").expanduser() / "svetovid"
    p.mkdir(parents=True, exist_ok=True)
    return p


def skill_home(skill):
    """Private data folder of one skill, created on first use."""
    p = home() / skill
    p.mkdir(parents=True, exist_ok=True)
    return p


def config_path():
    return home() / "config.toml"


def config():
    global _CONFIG
    if _CONFIG is None:
        p = config_path()
        if not p.exists():
            raise SystemExit(f"svetovid: no config at {p}. Run the doctor skill: its first run "
                             "walks you through setup (or copy config.example.toml there).")
        with open(p, "rb") as fh:
            _CONFIG = tomllib.load(fh)
    return _CONFIG


def get(dotted, default=_MISSING):
    node = config()
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            if default is _MISSING:
                raise KeyError(f"svetovid: '{dotted}' is not set in {config_path()}")
            return default
    return node


def path(dotted, default=_MISSING):
    v = get(dotted, default)
    return None if v is None else Path(os.path.expanduser(str(v)))


def folder(kind, svc=""):
    """Folder name for a kind of mail, from the [folders] templates.

    kind is service | feed | deliveries | <any key under [folders]>. With
    scheme = "by-kind" a template has no {svc} and every service shares it.
    """
    return str(get(f"folders.{kind}")).format(svc=svc)


def not_service_folders():
    """Folders that never hold service mail: INBOX, Urgent, forwarded accounts,
    rules.not_routed (the server's own folders: sent mail, drafts, ...), the
    trash, archive and junk folders, the probe folder, rules.extra_not_service.
    No folder name is assumed: doctor reads them from the server (folder_roles)."""
    out = {"INBOX", str(get("rules.urgent_folder", "Urgent")), str(get("rules.probe.tag", "sieveprobe"))}
    out |= {str(get(f"mail.{role}_folder", "")) for role in ("trash", "archive", "junk")}
    out |= {f["folder"] for f in get("forwarded", []) if isinstance(f, dict) and f.get("folder")}
    out |= set(get("rules.not_routed", []))
    out |= set(get("rules.extra_not_service", []))
    out.discard("")
    return out


def folder_roles(m):
    """What the server itself says its folders are for (IMAP SPECIAL-USE):
    {"sent": "Sent", "drafts": ..., "trash": ..., "junk": ..., "archive": ...}.
    Empty when the server marks none."""
    import re
    roles = {}
    for line in m.list()[1]:
        if isinstance(line, tuple):
            flags, name = line[0].decode("utf-8", "replace"), line[1].decode("utf-8", "replace")
        else:
            mm = re.match(r'\((.*?)\) (?:"[^"]*"|NIL) (.*)$', line.decode("utf-8", "replace"))
            if not mm:
                continue
            flags, name = mm.group(1), mm.group(2).strip().strip('"')
        for flag in flags.split():
            role = flag.lstrip("\\").lower()
            if role in ("sent", "drafts", "trash", "junk", "archive"):
                roles.setdefault(role, name)
    return roles


def _template_rx(tpl):
    import re
    parts = [re.escape(p) for p in str(tpl).split("{svc}")]
    return re.compile("^" + ".+".join(parts) + "$")


def is_service_folder(name):
    """True for a folder that holds one service's leftover mail (the [folders]
    service template), false for INBOX, Urgent, forwarded accounts, feed and
    lane folders (every other [folders] template)."""
    if name in not_service_folders():
        return False
    for kind, tpl in get("folders", {}).items():
        if kind in ("scheme", "service") or not isinstance(tpl, str):
            continue
        if _template_rx(tpl).match(name):
            return False
    return bool(_template_rx(get("folders.service", "{svc}")).match(name))


def last_run(skill):
    """Date (YYYY-MM-DD) of the newest '- <date>...' line in <skill>/runs.md, or None."""
    import re
    p = home() / skill / "runs.md"
    try:
        dates = re.findall(r"(?m)^-\s*(\d{4}-\d{2}-\d{2})", p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    return max(dates) if dates else None


def need_report(skill, work, routine_days, notes=()):
    """Print a skill's need as one JSON line, the format doctor reads:

    {"skill", "work": [evidence, ...] (empty = nothing specific found),
     "last_run", "routine_days" (a routine check-up is due after this many
     days without one), "notes": [context that is not work]}
    """
    import json
    print(json.dumps({"skill": skill, "work": list(work), "last_run": last_run(skill),
                      "routine_days": routine_days, "notes": list(notes)}, ensure_ascii=False))


def run(cmd, **kw):
    """Run a configured shell command string (never with untrusted input)."""
    return subprocess.run(cmd, shell=True, text=True, **kw)


def password():
    """The mailbox password, from mail.password_command. Never stored."""
    out = run(get("mail.password_command"), capture_output=True)
    pw = out.stdout.strip()
    if out.returncode or not pw:
        raise SystemExit("svetovid: mail.password_command gave no password (keyring locked?)")
    return pw


def tls():
    """A TLS context that checks the server's certificate and host name.

    imaplib and smtplib check neither unless they are handed a context, so
    every connection that sends the mailbox password must use this one."""
    import ssl
    return ssl.create_default_context()


def imap(timeout=60):
    """A logged-in IMAP connection to the mailbox (mail.imap_host, mail.imap_port,
    default 993), over TLS with the certificate checked."""
    import imaplib
    m = imaplib.IMAP4_SSL(get("mail.imap_host"), int(get("mail.imap_port", 993)),
                          ssl_context=tls(), timeout=timeout)
    m.login(get("mail.address"), password())
    return m


# --------------------------------------------------------------------------
# The alias service (mail.alias_service): one module in lib/aliases/ per
# service says what its forwards look like. addy_io.py explains the fields.
# --------------------------------------------------------------------------
class _NoAlias:
    NAME = ""
    SENDER_HEADERS = DISPLAY_HEADERS = RECIPIENT_HEADERS = ()
    OWN_DOMAINS = BANNER_TEXT = BANNER_HTML = BANNER_LINES = ()
    NOISE_HEADERS = ""


_ALIAS = None


def alias_module_path():
    """Where the module for mail.alias_service lives (None when none is set)."""
    import re
    name = str(get("mail.alias_service", "") or "")
    if not name:
        return None
    return REPO / "lib" / "aliases" / (re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") + ".py")


def alias():
    """The module of the user's alias service, or one with every field empty
    (no alias service, or no module for it yet: doctor says which)."""
    global _ALIAS
    if _ALIAS is None:
        try:
            path = alias_module_path()
        except SystemExit:          # no config at all (a tool run on its own)
            path = None
        if path is None or not path.exists():
            _ALIAS = _NoAlias
        else:
            import importlib.util
            spec = importlib.util.spec_from_file_location("svetovid_alias", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for field in ("SENDER_HEADERS", "DISPLAY_HEADERS", "RECIPIENT_HEADERS", "OWN_DOMAINS",
                          "BANNER_TEXT", "BANNER_HTML", "BANNER_LINES"):
                setattr(mod, field, tuple(getattr(mod, field, ()) or ()))
            mod.NOISE_HEADERS = getattr(mod, "NOISE_HEADERS", "") or ""
            _ALIAS = mod
    return _ALIAS


def real_sender(msg, display=False):
    """The From of whoever really wrote a message: through an alias service
    that is in the service's own header, and From is the alias. display=True
    prefers the header that keeps the sender's name."""
    a = alias()
    names = a.DISPLAY_HEADERS + a.SENDER_HEADERS if display else a.SENDER_HEADERS + a.DISPLAY_HEADERS
    for name in names:
        try:
            value = msg.get(name)
        except Exception:
            value = None
        if value:
            return str(value)
    try:
        return str(msg.get("From") or "")
    except Exception:
        return ""


def strip_alias_banner(text):
    """Body text (one line, plain) without the alias service's banner on top."""
    import re
    for pattern in alias().BANNER_TEXT:
        text = re.sub(pattern, "", text, count=1)
    return text


def _main(argv):
    if len(argv) >= 2 and argv[0] in ("get", "path"):
        default = argv[2] if len(argv) > 2 else _MISSING
        try:
            v = get(argv[1], default) if argv[0] == "get" else path(argv[1], default)
        except KeyError as e:
            print(e.args[0], file=sys.stderr)
            return 1
        if isinstance(v, (list, tuple)):
            print("\n".join(str(x) for x in v))
        else:
            print(v)
        return 0
    if argv == ["home"]:
        print(home())
        return 0
    if argv == ["cache"]:
        print(cache())
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
