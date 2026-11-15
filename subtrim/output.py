"""Write the report (Markdown, HTML, JSON) and the cancellation drafts. Drafts are files. Nothing is sent."""
import html
import json
import pathlib
import re
from email.message import EmailMessage

from .detect import money

CADENCE_WORD = {"weekly": "a week", "monthly": "a month", "quarterly": "a quarter", "yearly": "a year"}
OPEN_WORD = {"yes": "open source", "partial": "open source with conditions", "no": "not open source", "unknown": "licence unknown"}


def day(d):
    return f"{d.day} {d:%b %Y}" if d else "unknown"


def totals_text(totals):
    return " + ".join(money(v, c) for c, v in totals.items()) or "nothing"


def short(text, n=60):
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def alt_line(a):
    cover = {"full": "covers the main jobs", "partial": "covers part of it"}.get(a["coverage"], "coverage unknown")
    return f"{a['name']} ({short(a['licence'], 40)}, {OPEN_WORD.get(a['open_source'], 'licence unknown')}; {cover}) {a['page']}"


def draft(sub, scan):
    """One cancellation request as an .eml file with X-Unsent: 1, so a mail app opens it as a draft."""
    m = EmailMessage()
    m["Subject"] = f"Please cancel my {sub.name} subscription"
    if sub.contact:
        m["To"] = sub.contact
    if sub.account_email:
        m["From"] = sub.account_email
    m["X-Unsent"] = "1"
    lines = ["Hello,", ""]
    if sub.status == "trial":
        end = f" before it ends on {day(sub.trial_ends)}" if sub.trial_ends else ""
        lines.append(f"Please cancel my {sub.name} free trial{end}. I don't want it to turn into a paid plan.")
    else:
        lines.append(f"Please cancel my {sub.name} subscription and turn off auto-renewal.")
        lines.append(f"The last charge was {money(sub.amount, sub.currency)} on {day(sub.last_charge)}.")
        if sub.refund_window:
            lines.append("That renewal was within the last 14 days. Please refund it if your terms allow.")
    if sub.account_email:
        lines.append(f"The account email is {sub.account_email}.")
    lines += ["", "Please confirm in writing that it is cancelled and that no further payments will be taken.", "", "Thank you"]
    m.set_content("\n".join(lines) + "\n")
    return m


def how_to_cancel(sub):
    parts = []
    if sub.contact:
        parts.append(f"draft addressed to {sub.contact}")
    else:
        parts.append("their receipts come from a no-reply address, so the draft has no recipient")
    if sub.manage_link:
        parts.append(f"account page found in their email: {sub.manage_link}")
    return "; ".join(parts)


def to_dict(sub):
    return {
        "name": sub.name, "status": sub.status, "cadence": sub.cadence,
        "amount": sub.amount, "currency": sub.currency, "monthly": sub.monthly,
        "last_charge": sub.last_charge.isoformat() if sub.last_charge else None,
        "charges_seen": len(sub.charges), "flagged": sub.flagged,
        "flags": sub.flags, "notes": sub.notes,
        "trial_ends": sub.trial_ends.isoformat() if sub.trial_ends else None,
        "contact": sub.contact, "manage_link": sub.manage_link,
        "repoquarry_product": sub.product["id"] if sub.product else None,
        "alternatives": [{"name": a["name"], "licence": a["licence"], "coverage": a["coverage"], "page": a["page"]}
                         for a in sub.alternatives],
    }


def summary(scan, catalogue):
    active, flagged = scan.active(), scan.flagged()
    paid_flagged = [s for s in flagged if s.status == "active"]
    return {
        "today": scan.today.isoformat(),
        "emails_read": scan.messages, "emails_unreadable": scan.skipped, "receipts_found": scan.receipts,
        "subscriptions": len(active),
        "monthly_total": scan.totals(),
        "yearly_total": {c: round(v * 12, 2) for c, v in scan.totals().items()},
        "flagged": len(flagged),
        "flagged_monthly": scan.totals(paid_flagged),
        "trials_about_to_charge": sum(1 for s in scan.subs if s.status == "trial"),
        "with_alternatives": sum(1 for s in active if s.alternatives),
        "flagged_with_alternatives": sum(1 for s in flagged if s.alternatives),
        "already_cancelled": sum(1 for s in scan.subs if s.status == "cancelled"),
        "unclear": sum(1 for s in scan.subs if s.status in ("unclear", "lapsed")),
        "one_off_purchases_ignored": len(scan.one_offs),
        "suspicious_receipts_ignored": len(scan.suspicious),
        "catalogue_snapshot": catalogue.snapshot_date,
    }


def markdown(scan, catalogue):
    s = summary(scan, catalogue)
    active, flagged = scan.active(), scan.flagged()
    out = [f"# Subtrim report, {day(scan.today)}", ""]
    out.append(f"Read {s['emails_read']} emails and found {s['receipts_found']} receipts for repeat charges.")
    out.append(f"**{len(active)} subscriptions, {totals_text(scan.totals())} a month** "
               f"({totals_text(s['yearly_total'])} a year).")
    out.append(f"**{len(flagged)} flagged.** Nothing has been cancelled, sent or clicked.")
    out += ["", "## Flagged, with a draft for each", ""]
    if not flagged:
        out.append("None. Subtrim only flags a subscription when an email gives a reason, or you name it with `--unused`.")
    for sub in flagged:
        price = (f"{money(sub.amount, sub.currency)} {CADENCE_WORD.get(sub.cadence, '')}".strip()
                 if sub.amount else "price not stated")
        out.append(f"### {sub.name}: {price}" + (" (trial, not charged yet)" if sub.status == "trial" else ""))
        for f in sub.flags:
            out.append(f"- Why: {f}")
        for n in sub.notes:
            out.append(f"- Also: {n}")
        out.append(f"- To cancel: {how_to_cancel(sub)}")
        if sub.alternatives:
            out.append(f"- Free alternatives on RepoQuarry ({sub.product['page']}):")
            out += [f"  - {alt_line(a)}" for a in sub.alternatives]
        else:
            out.append("- Free alternative: none listed on RepoQuarry for this one.")
        out.append("")
    out += ["## Everything you pay for", "", "| Subscription | Charge | A month | Last charged | Seen | Free alternatives on RepoQuarry |",
            "|---|---|---|---|---|---|"]
    for sub in active:
        alts = ", ".join(a["name"] for a in sub.alternatives) or "none listed"
        out.append(f"| {sub.name}{' ⚑' if sub.flagged else ''} | {money(sub.amount, sub.currency)} {CADENCE_WORD[sub.cadence]} | "
                   f"{money(sub.monthly, sub.currency)} | {day(sub.last_charge)} | {len(sub.charges)} | {alts} |")
    notes = [(sub.name, n) for sub in active if not sub.flagged for n in sub.notes]
    if notes:
        out += ["", "## Worth a look", ""] + [f"- **{name}:** {n}" for name, n in notes]
    rest = [x for x in scan.subs if x.status in ("cancelled", "lapsed", "unclear")]
    if rest or scan.one_offs or scan.suspicious:
        out += ["", "## Left out of the total", ""]
        for sub in rest:
            why = {"cancelled": "already cancelled, by their own email",
                   "lapsed": f"no charge since {day(sub.last_charge)}, so it looks finished",
                   "unclear": "charges don't follow a steady gap, so check it yourself"}[sub.status]
            out.append(f"- {sub.name} ({money(sub.amount, sub.currency)}): {why}.")
        for name, when, amount, cur in scan.one_offs:
            out.append(f"- {name} ({money(amount, cur)}, {day(when)}): a one-off purchase, not a subscription.")
        for name, sender, when, amount in scan.suspicious:
            out.append(f"- A receipt for {amount} that says it is from {name} but came from {sender} ({day(when)}). "
                       f"That isn't {name}'s address, so it wasn't counted. Don't click its links.")
    out += ["", f"Alternatives come from RepoQuarry's catalogue as it stood on {catalogue.snapshot_date} (CC BY 4.0). "
                "Licences change, so open the page before you switch.", ""]
    return "\n".join(out)


CSS = """
body{font:16px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif;background:#f5f5f7;color:#1d1d1f;margin:0;padding:32px}
main{max-width:860px;margin:0 auto}
h1{font-size:28px;margin:0 0 4px}.sub{color:#6e6e73;margin:0 0 20px}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.tile{background:#fff;border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.tile b{display:block;font-size:28px;letter-spacing:-.5px}.tile span{color:#6e6e73;font-size:14px}
.card{background:#fff;border-radius:14px;padding:18px 20px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.card h3{margin:0 0 6px;font-size:18px;display:flex;justify-content:space-between;gap:12px}
.card h3 span{color:#b45309;font-weight:600;white-space:nowrap}
.card p{margin:4px 0;font-size:15px}.why{color:#1d1d1f}.lab{color:#6e6e73}
.alt{display:inline-block;background:#e8f5e9;color:#1b5e20;border-radius:999px;padding:2px 10px;margin:2px 4px 2px 0;font-size:13px}
.none{background:#f0f0f2;color:#6e6e73}
h2{font-size:19px;margin:26px 0 10px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06);font-size:14px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #eee;vertical-align:top}th{color:#6e6e73;font-weight:600}
td.n{white-space:nowrap}.flag{color:#b45309;font-weight:600}
ul{padding-left:20px;font-size:15px}.foot{color:#6e6e73;font-size:13px;margin-top:20px}
"""


def html_report(scan, catalogue):
    e = html.escape
    s = summary(scan, catalogue)
    active, flagged = scan.active(), scan.flagged()
    h = [f"<!doctype html><meta charset='utf-8'><title>Subtrim report</title><style>{CSS}</style><main>",
         f"<h1>Subtrim report</h1><p class='sub'>{day(scan.today)} · {s['emails_read']} emails read · "
         f"{s['receipts_found']} receipts · nothing cancelled, sent or clicked</p><div class='tiles'>",
         f"<div class='tile'><b>{len(active)}</b><span>subscriptions</span></div>",
         f"<div class='tile'><b>{e(totals_text(scan.totals()))}</b><span>a month ({e(totals_text(s['yearly_total']))} a year)</span></div>",
         f"<div class='tile'><b>{len(flagged)}</b><span>flagged, each with a draft</span></div></div>",
         "<h2>Flagged</h2>"]
    for sub in flagged:
        price = (f"{money(sub.amount, sub.currency)} {CADENCE_WORD.get(sub.cadence, '')}" if sub.amount else "price not stated")
        tag = " · trial, not charged yet" if sub.status == "trial" else ""
        h.append(f"<div class='card'><h3>{e(sub.name)}<span>{e(price)}{tag}</span></h3>")
        for f in sub.flags:
            h.append(f"<p class='why'><span class='lab'>Why:</span> {e(f)}</p>")
        for n in sub.notes:
            h.append(f"<p><span class='lab'>Also:</span> {e(n)}</p>")
        h.append(f"<p><span class='lab'>To cancel:</span> {e(how_to_cancel(sub))}</p><p><span class='lab'>Free alternatives:</span> ")
        h.append("".join(f"<span class='alt'>{e(a['name'])} · {e(short(a['licence'], 28))}</span>" for a in sub.alternatives)
                 or "<span class='alt none'>none listed on RepoQuarry</span>")
        h.append("</p></div>")
    h.append("<h2>Everything you pay for</h2><table><tr><th>Subscription</th><th>Charge</th><th>A month</th>"
             "<th>Last charged</th><th>Free alternatives on RepoQuarry</th></tr>")
    for sub in active:
        alts = ", ".join(a["name"] for a in sub.alternatives) or "none listed"
        flag = " <span class='flag'>flagged</span>" if sub.flagged else ""
        h.append(f"<tr><td>{e(sub.name)}{flag}</td><td class='n'>{e(money(sub.amount, sub.currency))} {CADENCE_WORD[sub.cadence]}</td>"
                 f"<td class='n'>{e(money(sub.monthly, sub.currency))}</td><td class='n'>{day(sub.last_charge)}</td><td>{e(alts)}</td></tr>")
    h.append("</table>")
    md = markdown(scan, catalogue)
    for title in ("Worth a look", "Left out of the total"):
        m = re.search(rf"## {title}\n\n((?:- .*\n?)+)", md)
        if m:
            items = "".join(f"<li>{re.sub(r"[*][*](.+?)[*][*]", lambda m: "<b>" + m.group(1) + "</b>", e(l[2:]))}</li>" for l in m.group(1).strip().splitlines())
            h.append(f"<h2>{title}</h2><ul>{items}</ul>")
    h.append(f"<p class='foot'>Alternatives from RepoQuarry's catalogue as it stood on {e(catalogue.snapshot_date)} (CC BY 4.0). "
             "Licences change, so open the page before you switch.</p></main>")
    return "\n".join(h)


def write_all(scan, catalogue, out_dir):
    out = pathlib.Path(out_dir)
    (out / "drafts").mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(markdown(scan, catalogue), encoding="utf-8")
    (out / "report.html").write_text(html_report(scan, catalogue), encoding="utf-8")
    data = {"summary": summary(scan, catalogue), "subscriptions": [to_dict(s) for s in scan.subs]}
    (out / "subscriptions.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    written = []
    for sub in scan.flagged():
        path = out / "drafts" / (re.sub(r"[^a-z0-9]+", "-", sub.name.lower()).strip("-") + ".eml")
        path.write_bytes(bytes(draft(sub, scan)))
        written.append(path)
    return written
