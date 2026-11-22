# A starter for the one script svetovid looks after: the structure only.
#
# Copy it into your rules repository as the file `rules.script` names, replace
# the example addresses, and land it. It holds no keywords on purpose: which
# words mean "urgent" or "delivery" in your mail is something the skills learn
# from your own mail and then write here (lane-urgent, lane-deliveries, route).
#
# The sections are marked "# ---- NAME"; the skills find their place by them.
# STACK.md, "The Sieve script", explains the shape.

require ["variables", "fileinto", "mailbox"];

# ---- IDENTITY: which service is this mail for?
# One address per sign-up. The service is read from the address the mail was
# delivered to, which your provider stamps into a header: X-Envelope-To here;
# Delivered-To or X-Original-To at many others. Keep the forms you use.
set "svc" "";
if header :matches "X-Envelope-To" "*@me.example.org" {          # <service>@me.example.org
    set :lower "svc" "${1}";
} elsif header :matches "X-Envelope-To" "you+*@example.org" {    # you+<service>@example.org
    set :lower "svc" "${1}";
}
# An alias service: the alias the mail was sent to is in the service's own
# header (lib/aliases/ names it for the services svetovid knows).

# ---- FORWARDED: accounts you can't move
# One watched folder each, before anything else can file their mail.
# if header :is "X-Envelope-To" "work@example.org" { fileinto :create "Work"; stop; }

# ---- URGENT: decide only. Sets the class; never files.
# One list of Subject keys per class, in your own languages, then scoped
# rules and undos for single services. lane-urgent writes and audits these.
set "why" "";
# if header :contains "Subject" ["<how your services word a login code>"] { set "why" "auth"; }

# ---- FOLD: service mail only
if not string :is "${svc}" "" {
    # Urgent is a move: the mail is in Urgent and nowhere else.
    if not string :is "${why}" "" { fileinto :create "Urgent"; stop; }

    # ---- ROUTE: one self-contained block per service or lane, each ending
    # in stop. Lane blocks first, then the services in alphabetical order.
    # if allof (string :is "${svc}" "example", header :contains "Subject" "<key>") {
    #     fileinto :create "example-rss"; stop;
    # }

    # Whatever no block took stays in the service's own folder, for the sweep.
    fileinto :create "${svc}"; stop;
}
# Anything else is from a person: implicit keep (INBOX).
