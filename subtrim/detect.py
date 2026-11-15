"""Turn a pile of emails into a list of subscriptions, with the evidence for each one.

Rules of the house:
- A charge counts only if the email has receipt wording and an amount.
- A subscription counts only if charges repeat on a steady gap, or a single receipt says it renews.
- A flag needs evidence you can read: their own "we miss you" email, a trial about to turn paid, or your say-so.
- Anything unclear is listed as unclear, never guessed.
"""
import re
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .catalogue import brand_label, norm

SYMBOL = {"£": "GBP", "$": "USD", "€": "EUR"}
SIGN = {"GBP": "£", "USD": "$", "EUR": "€"}
AMOUNT = re.compile(
    r"(?:(?P<c1>£|\$|€|GBP|USD|EUR)\s?(?P<n1>\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+(?:\.\d{2})?))"
    r"|(?:(?P<n2>\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+\.\d{2})\s?(?P<c2>GBP|USD|EUR))"
)
PROCESSORS = {"stripe", "paddle", "paypal", "apple", "google", "gumroad", "lemonsqueezy", "fastspring", "gocardless"}
NO_REPLY = re.compile(r"(?i)no[-_.]?reply|do[-_.]?not[-_.]?reply|donotreply|^receipts@|^notifications?@|^invoice\+")
RECEIPT = re.compile(r"(?i)\b(receipt|invoice|payment (?:received|confirmation|successful|of)|thanks for your payment|"
                     r"you(?:'ve| have) been charged|we(?:'ve| have) charged|has been charged|subscription renew(?:ed|al)|"
                     r"renewal confirmation|billing statement|amount paid|order total)\b")
CANCELLED = re.compile(r"(?i)\b(subscription (?:has been|was|is now) cancel+ed|we(?:'ve| have) cancel+ed your|"
                       r"your cancel+ation is confirmed|cancel+ation confirmed|you(?:'ve| have) cancel+ed)\b")
TRIAL = re.compile(r"(?i)\b(free )?trial (?:ends|is ending|will end|expires|is about to end)\b|\btrial ending\b")
INACTIVE = re.compile(r"(?i)we miss you|haven'?t (?:seen|heard from) you|you haven'?t (?:logged|signed|recorded|used|opened|created|been)|"
                      r"it'?s been a while|still there\?|come back to|no activity (?:in|for)|inactive for")
PRICE_NOTICE = re.compile(r"(?i)price (?:is|will be) (?:changing|increasing|going up)|new price|price (?:change|increase|update)")
ONE_OFF = re.compile(r"(?i)\b(order (?:confirmation|confirmed|#|number)|your order|has shipped|dispatch|delivery|tracking number)\b")
YEARLY = re.compile(r"(?i)\b(annual(?:ly)?|yearly|per year|a year|/\s?year|/\s?yr|every year|12[- ]month)\b")
MONTHLY = re.compile(r"(?i)\b(monthly|per month|a month|/\s?month|/\s?mo\b|every month)")
QUARTERLY = re.compile(r"(?i)\b(quarterly|every (?:3|three) months|per quarter)\b")
RENEWS = re.compile(r"(?i)\b(renews?|renewal|next (?:billing|payment|charge)|auto[- ]?renew|recurring|subscription)\b")
MANAGE = re.compile(r"(?i)billing|account|subscription|manage|cancel|settings|plans?")
STRIP_WORDS = re.compile(r"(?i)\b(team|billing|receipts?|support|payments?|accounts?|invoices?|inc\.?|ltd\.?|llc|limited|"
                         r"the|hello|from|via .*)\b")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
PER_MONTH = {"weekly": 52 / 12, "monthly": 1, "quarterly": 1 / 3, "yearly": 1 / 12}
PERIOD_DAYS = {"weekly": 7, "monthly": 31, "quarterly": 92, "yearly": 366}


def money(amount, currency):
    return f"{SIGN.get(currency, currency + ' ')}{amount:,.2f}"


def find_amounts(text):
    out = []
    for m in AMOUNT.finditer(text or ""):
        cur = m.group("c1") or m.group("c2")
        num = m.group("n1") or m.group("n2")
        out.append((float(num.replace(",", "")), SYMBOL.get(cur, cur)))
    return out


def charge_amount(msg):
    """The amount on a 'total' or 'charged' line if there is one, else the first amount found."""
    best = None
    for line in msg.body.splitlines():
        if re.search(r"(?i)\b(total|amount paid|amount charged|charged|payment of|you paid)\b", line):
            found = find_amounts(line)
            if found:
                best = found[-1]
                if re.search(r"(?i)\btotal\b", line):
                    break
    if best:
        return best
    for text in (msg.subject, msg.body):
        found = find_amounts(text)
        if found:
            return found[0]
    return None


def parse_day(text):
    """First calendar date written in the text, e.g. '20 November 2026', 'Nov 20, 2026', '2026-11-20'."""
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})|(\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]{3,9}),? (\d{4})|([A-Za-z]{3,9}) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})", text or ""):
        try:
            if m.group(1):
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if m.group(4):
                return date(int(m.group(6)), MONTHS[m.group(5)[:3].lower()], int(m.group(4)))
            return date(int(m.group(9)), MONTHS[m.group(7)[:3].lower()], int(m.group(8)))
        except (KeyError, ValueError):
            continue
    return None


def sentence_with(pattern, text):
    for s in re.split(r"(?<=[.!?])\s+|\n+", text or ""):
        if pattern.search(s):
            return " ".join(s.split())[:160]
    return ""


def clean_name(name):
    name = STRIP_WORDS.sub(" ", name or "")
    name = re.sub(r"[^\w&.+' -]", " ", name)
    return " ".join(name.split()).strip(" -.")


def merchant_of(msg):
    """(key, display name, is_processor). Receipts sent by Stripe, PayPal and the like name the real shop
    in the subject, so we read it from there."""
    label = brand_label(msg.domain)
    if label in PROCESSORS:
        for pat in (r"(?i).*\b(?:receipt|invoice|payment|subscription) (?:from|to|for|with) (.+?)(?:\s+#|\s+-\s|\s+\(|[.,:!]|$)",
                    r"(?i)your (.+?) (?:subscription|receipt|invoice|payment|plan|membership)"):
            m = re.search(pat, msg.subject)
            if m and clean_name(m.group(1)):
                return norm(clean_name(m.group(1))), clean_name(m.group(1)), True
        name = clean_name(msg.sender_name)
        if name and norm(name) not in PROCESSORS:
            return norm(name), name, True
        return "", "", True
    name = clean_name(msg.sender_name) or label.capitalize()
    return label, name, False


@dataclass
class Sub:
    key: str
    name: str
    currency: str = ""
    amount: float = 0.0
    cadence: str = "unclear"
    status: str = "active"          # active, trial, cancelled, lapsed, unclear
    charges: list = field(default_factory=list)   # (date, amount)
    last_charge: date = None
    monthly: float = 0.0
    flags: list = field(default_factory=list)     # reasons to cancel, each with evidence
    notes: list = field(default_factory=list)     # worth a look, not a reason on their own
    account_email: str = ""
    contact: str = ""
    manage_link: str = ""
    via: str = ""
    product: dict = None
    alternatives: list = field(default_factory=list)
    trial_ends: date = None
    refund_window: bool = False

    @property
    def flagged(self):
        return bool(self.flags) and self.status in ("active", "trial")


@dataclass
class Scan:
    today: date
    messages: int = 0
    skipped: int = 0
    receipts: int = 0
    subs: list = field(default_factory=list)
    one_offs: list = field(default_factory=list)      # (name, date, amount, currency)
    suspicious: list = field(default_factory=list)    # (claimed name, sender, date, amount text)
    mentions: int = 0                                  # emails that mention money but are not receipts for a repeat charge

    def active(self):
        return [s for s in self.subs if s.status == "active"]

    def flagged(self):
        return [s for s in self.subs if s.flagged]

    def totals(self, subs=None):
        out = {}
        for s in (self.active() if subs is None else subs):
            if s.status == "active":
                out[s.currency] = out.get(s.currency, 0.0) + s.monthly
        return {c: round(v, 2) for c, v in sorted(out.items())}


def _cadence(days, texts):
    gaps = [(b - a).days for a, b in zip(days, days[1:])]
    if gaps:
        mid = statistics.median(gaps)
        for name, lo, hi in (("weekly", 6, 8), ("monthly", 26, 35), ("quarterly", 80, 100), ("yearly", 340, 390)):
            # The usual gap must fit, and so must most of the gaps: one late or skipped payment is fine.
            if lo <= mid <= hi and sum(lo <= g <= hi for g in gaps) / len(gaps) >= 0.6:
                return name
    blob = "\n".join(texts)
    if not RENEWS.search(blob):
        return "one-off" if not gaps else "unclear"
    for name, pat in (("yearly", YEARLY), ("quarterly", QUARTERLY), ("monthly", MONTHLY)):
        if pat.search(blob):
            return name
    return "unclear"


def scan(messages, catalogue, today, me="", unused=(), skipped=0):
    result = Scan(today=today, messages=len(messages), skipped=skipped)
    groups = {}
    for msg in messages:
        if msg.date.date() > today or (me and msg.sender_email == me.lower()):
            continue  # mail from the future, or mail you sent yourself (your own invoices)
        key, name, via_processor = merchant_of(msg)
        if not key:
            continue
        text = msg.subject + "\n" + msg.body
        product = catalogue.match(name)
        amount = charge_amount(msg)
        is_receipt = bool(RECEIPT.search(text)) and amount is not None

        # A receipt that uses a known brand's name from an address that isn't theirs is not counted.
        if is_receipt and product and not via_processor:
            labels = set(msg.domain.split("."))
            wanted = {brand_label(product.get("url")), norm(product["name"])}
            if not (labels & wanted):
                result.suspicious.append((product["name"], msg.sender_email, msg.date.date(), money(*amount)))
                continue

        g = groups.setdefault(key, {"name": name, "product": product, "charges": [], "other": [], "via": via_processor})
        if product and not g["product"]:
            g["product"], g["name"] = product, name
        if CANCELLED.search(text):
            g["other"].append(("cancelled", msg))
        elif TRIAL.search(text):
            g["other"].append(("trial", msg))
        elif is_receipt and not (ONE_OFF.search(text) and not RENEWS.search(text)):
            g["charges"].append((msg, amount))
            result.receipts += 1
        elif is_receipt:
            result.one_offs.append((name, msg.date.date(), amount[0], amount[1]))
            g["shop"] = True
        elif INACTIVE.search(text):
            g["other"].append(("inactive", msg))
        elif PRICE_NOTICE.search(text):
            g["other"].append(("price", msg))
        else:
            g["other"].append(("other", msg))

    marked = {norm(u) for u in unused}
    for key, g in groups.items():
        charges, other = g["charges"], g["other"]
        name = g["name"]  # the name on their own emails; the catalogue match is only used for alternatives
        trials = [m for kind, m in other if kind == "trial"]
        if not charges and not trials:
            continue
        sub = Sub(key=key, name=name, product=g["product"], via="a payment processor" if g["via"] else "")
        sub.alternatives = catalogue.alternatives(g["product"])
        all_msgs = [m for m, _ in charges] + [m for _, m in other]
        sub.account_email = me or next((m.to for m in all_msgs if m.to), "")

        if charges:
            days = [m.date.date() for m, _ in charges]
            sub.charges = [(m.date.date(), a[0]) for m, a in charges]
            sub.amount, sub.currency = charges[-1][1]
            sub.last_charge = days[-1]
            sub.cadence = _cadence(days, [m.subject + "\n" + m.body for m, _ in charges])
            if sub.cadence == "one-off":
                # A shop or a payment processor is listed as a one-off. A person mentioning money is just counted.
                if g["via"] or g.get("shop"):
                    result.one_offs.append((name, days[-1], sub.amount, sub.currency))
                else:
                    result.mentions += len(charges)
                result.receipts -= len(charges)
                continue
            if sub.cadence == "unclear":
                sub.status = "unclear"
            else:
                sub.monthly = round(sub.amount * PER_MONTH[sub.cadence], 2)
                if (today - sub.last_charge).days > PERIOD_DAYS[sub.cadence] * 1.5:
                    sub.status = "lapsed"
            if any(kind == "cancelled" and m.date.date() >= sub.last_charge for kind, m in other):
                sub.status = "cancelled"
            earlier = [a for _, a in sub.charges[:-1] if abs(a - sub.amount) > 0.004]
            if earlier and sub.status == "active":
                word = "up" if sub.amount > earlier[-1] else "down"
                sub.notes.append(f"Price went {word} from {money(earlier[-1], sub.currency)} to {money(sub.amount, sub.currency)}.")
            if sub.cadence == "yearly" and sub.status == "active" and (today - sub.last_charge).days <= 14:
                sub.refund_window = True
                sub.notes.append(f"Charged {(today - sub.last_charge).days} days ago for a year. Worth asking for a refund if you cancel now.")
        else:
            trial = trials[-1]
            text = trial.subject + "\n" + trial.body
            sub.status = "trial"
            sub.trial_ends = parse_day(text)
            found = find_amounts(text)
            if found:
                sub.amount, sub.currency = found[0]
                sub.cadence = "yearly" if YEARLY.search(text) and not MONTHLY.search(text) else "monthly"
                sub.monthly = round(sub.amount * PER_MONTH[sub.cadence], 2)
            if sub.trial_ends and sub.trial_ends < today:
                continue  # the trial date has passed and no charge arrived, so nothing to cancel
            when = f"on {sub.trial_ends:%d %b %Y}".replace(" 0", " ") if sub.trial_ends else "soon"
            price = f" at {money(sub.amount, sub.currency)} a {sub.cadence[:-2]}" if found else ""
            sub.flags.append(f"Free trial turns paid {when}{price}. Their email: “{sentence_with(TRIAL, text)}”")

        if sub.status == "active":
            for kind, m in other:
                if kind == "inactive" and (today - m.date.date()).days <= 120:
                    quote = sentence_with(INACTIVE, m.subject + "\n" + m.body)
                    sub.flags.append(f"Their own email on {m.date:%d %b %Y} says: “{quote}”".replace(" 0", " "))
                    break
            if norm(sub.name) in marked or key in marked:
                sub.flags.append("You said you don't use it.")

        # Where to cancel: a reply address that takes replies, and a link on the sender's own site.
        newest = (charges[-1][0] if charges else trials[-1])
        for addr in (newest.reply_to, newest.sender_email):
            if addr and not NO_REPLY.search(addr) and brand_label(addr.split("@")[-1]) not in PROCESSORS:
                sub.contact = addr
                break
        own = {key, brand_label(newest.domain)} | ({brand_label(g["product"].get("url"))} if g["product"] else set())
        for m in reversed(all_msgs):
            hit = next((l for l in m.links if MANAGE.search(l) and brand_label(l) in own), "")
            if hit:
                sub.manage_link = hit
                break
        result.subs.append(sub)

    # Two tools in the same RepoQuarry category: worth a look, but not a reason to cancel by itself.
    by_cat = {}
    for s in result.active():
        if s.product and s.product.get("category"):
            by_cat.setdefault(s.product["category"], []).append(s)
    for cat, subs in by_cat.items():
        if len(subs) > 1:
            for s in subs:
                others = ", ".join(o.name for o in subs if o is not s)
                s.notes.append(f"You also pay for {others}, which RepoQuarry lists for the same kind of job ({cat.replace('-', ' ')}).")

    order = {"active": 0, "trial": 1, "unclear": 2, "lapsed": 3, "cancelled": 4}
    result.subs.sort(key=lambda s: (order[s.status], not s.flagged, -s.monthly, s.name.lower()))
    return result
