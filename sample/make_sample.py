"""Write sample/mail.mbox: a made-up inbox for a made-up freelancer, Sam Carter.

Everything here is invented, including every price, date and email. Real product names are used
only so the RepoQuarry match can be shown. None of these emails was ever sent by those companies.

    python sample/make_sample.py
"""
import mailbox
import pathlib
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime

ME = "sam@carterstudio.example"
OUT = pathlib.Path(__file__).with_name("mail.mbox")
msgs = []


def add(when, sender, subject, body, html=False, reply_to=None, to=ME):
    m = EmailMessage()
    m["From"] = sender
    m["To"] = to
    m["Subject"] = subject
    m["Date"] = format_datetime(datetime(*when, tzinfo=timezone.utc))
    if reply_to:
        m["Reply-To"] = reply_to
    if html:
        m.set_content(body, subtype="html")
    else:
        m.set_content(body)
    msgs.append((datetime(*when), m))


def monthly(months, dom, sender, subject, body, amounts, **kw):
    for month, amount in zip(months, amounts):
        add((2026, month, dom, 7, 12), sender, subject, body.format(amount=amount), **kw)


# --- Subscriptions -----------------------------------------------------------------------------
monthly([8, 9, 10, 11], 3, "Notion <team@mail.notion.so>", "Your Notion receipt",
        "Thanks for your payment.\n\nPlus plan, billed monthly\nTotal: £{amount}\n\n"
        "Your plan renews next month. Manage billing: https://www.notion.so/settings/billing\n",
        ["9.50"] * 4)

add((2026, 11, 6, 6, 40), "Evernote <no-reply@evernote.com>", "Your Evernote subscription renewed",
    "Your Evernote Personal annual subscription has renewed.\n\nAmount charged: £99.99\n"
    "It renews every year until you cancel.\nManage your subscription: https://www.evernote.com/billing\n")
add((2026, 10, 12, 9, 5), "Evernote <hello@email.evernote.com>", "We miss you, Sam",
    "It's been a while since you opened Evernote. Your notes are waiting for you.\n")

monthly([8, 9, 10, 11], 10, "Zapier <billing@zapier.com>", "Zapier invoice paid",
        "Invoice paid.\n\nProfessional plan (monthly subscription)\nAmount paid: £{amount}\n\n"
        "Billing settings: https://zapier.com/app/settings/billing\n",
        ["19.99", "24.99", "24.99", "24.99"])
add((2026, 8, 28, 10, 0), "Zapier <billing@zapier.com>", "A change to your Zapier plan price",
    "From your next invoice the price of your plan is changing. Nothing else about your plan changes.\n")

monthly([8, 9, 10, 11], 14, "Loom <receipts@stripe.com>", "Your receipt from Loom #2291-4410",
        "Receipt from Loom\n\nBusiness plan, monthly subscription\nAmount paid: £{amount}\n\n"
        "Questions? Visit https://www.loom.com/settings/billing\n",
        ["12.00"] * 4)
add((2026, 11, 2, 8, 30), "Loom <hello@loom.com>", "Your Loom library is quiet",
    "Hi Sam. You haven't recorded a video in 60 days. Record one in a click.\n"
    "Manage your plan: https://www.loom.com/settings/billing\n")

monthly([8, 9, 10], 21, "Canva <no-reply@canva.com>", "Your Canva Pro receipt",
        "<html><body><h2>Thanks for your payment</h2><table><tr><td>Canva Pro, monthly subscription</td></tr>"
        "<tr><td>Total: &pound;{amount}</td></tr></table>"
        "<p><a href=\"https://www.canva.com/settings/billing-and-teams\">Billing settings</a></p></body></html>",
        ["10.99"] * 3, html=True)

for month in (8, 11):
    add((2026, month, 5, 11, 20), "Grammarly <billing@grammarly.com>", "Your Grammarly receipt",
        "Thanks for your payment.\n\nGrammarly Pro, billed quarterly\nTotal: £30.00\n"
        "Your subscription renews every 3 months. https://account.grammarly.com/subscription\n")

monthly([8, 9, 10, 11], 1, "1Password <billing@1password.com>", "Your 1Password invoice",
        "Invoice for your 1Password subscription.\n\nIndividual plan, monthly\nAmount paid: £{amount}\n"
        "https://my.1password.com/billing\n",
        ["3.49"] * 4)

add((2026, 9, 20, 13, 0), "LastPass <billing@lastpass.com>", "Your LastPass Premium receipt",
    "Thanks for your payment.\n\nLastPass Premium, annual subscription\nTotal: £30.00\n"
    "Your subscription renews annually. Manage it at https://lastpass.com/account/billing\n")

monthly([8, 9, 10, 11], 8, "Spotify <no-reply@spotify.com>", "Your Spotify Premium receipt",
        "Here is your receipt.\n\nPremium Individual, monthly subscription\nTotal: £{amount}\n"
        "https://www.spotify.com/account/subscription\n",
        ["11.99"] * 4)

monthly([8, 9, 10, 11], 12, "Brightline Mobile <bills@brightlinemobile.example>", "Your Brightline bill has been paid",
        "Your monthly bill is ready and your payment of £{amount} has been charged to your card.\n"
        "This is a recurring monthly payment. https://brightlinemobile.example/account/bills\n",
        ["18.40", "19.10", "19.10", "18.75"])

# --- A trial about to turn paid (made-up company) ---------------------------------------------
add((2026, 11, 8, 9, 0), "Framecast <team@framecast.example>", "Your Framecast free trial ends soon",
    "Hi Sam. Your free trial ends on 20 November 2026. After that you'll be charged £14.00 a month "
    "unless you cancel.\nManage your plan: https://framecast.example/account/billing\n")

# --- Already cancelled (made-up company) ------------------------------------------------------
monthly([8, 9], 12, "Skillpath <billing@skillpath.example>", "Your Skillpath receipt",
        "Thanks for your payment.\n\nSkillpath Plus, monthly subscription\nTotal: £{amount}\n", ["12.00"] * 2)
add((2026, 9, 30, 16, 0), "Skillpath <billing@skillpath.example>", "Your Skillpath subscription has been cancelled",
    "Your subscription has been cancelled. You won't be charged again.\n")

# --- Things that must not be counted ----------------------------------------------------------
add((2026, 10, 17, 12, 0), "Deskhaus <orders@deskhaus.example>", "Order confirmation #88231",
    "Thanks for your order.\n\nMonitor arm x1\nOrder total: £48.00\nYour order has shipped. Tracking number DH4410.\n")
add((2026, 10, 3, 8, 15), "service@paypal.com", "Receipt for your payment to Oak & Iron Coffee",
    "You sent a payment of £7.20 to Oak & Iron Coffee.\n")
add((2026, 11, 9, 2, 14), "Notion Billing <billing@notion-payments.example>", "Invoice: your Notion renewal",
    "Your Notion renewal payment of £89.00 has been charged. If this wasn't you, view the invoice now: "
    "http://notion-payments.example/login\n")
add((2026, 10, 1, 9, 0), f"Sam Carter <{ME}>", "Invoice 104 from Carter Studio",
    "Hi Mei,\n\nInvoice 104 for the October retainer (monthly subscription to design support).\nTotal: £650.00\n",
    to="mei@northwinddental.example")

# --- Ordinary mail ----------------------------------------------------------------------------
ordinary = [
    ((2026, 8, 6), "Notion <team@mail.notion.so>", "What's new in Notion", "New this month: faster search and a tidier sidebar."),
    ((2026, 9, 9), "Notion <team@mail.notion.so>", "Three templates for freelancers", "Try these templates for client work."),
    ((2026, 10, 14), "Notion <team@mail.notion.so>", "Your weekly digest", "4 pages were edited in your workspace this week."),
    ((2026, 8, 19), "Zapier <updates@zapier.com>", "Your Zaps ran 212 times this month", "Top Zap: new invoice to spreadsheet."),
    ((2026, 10, 19), "Zapier <updates@zapier.com>", "Your Zaps ran 198 times this month", "Top Zap: new invoice to spreadsheet."),
    ((2026, 9, 2), "Canva <hello@canva.com>", "New fonts just landed", "Fresh fonts for your next design."),
    ((2026, 8, 11), "Indie Notes <hello@indienotes.example>", "Issue 41: pricing your retainer", "Paid issues are £5 a month. This one is free."),
    ((2026, 9, 15), "Indie Notes <hello@indienotes.example>", "Issue 42: saying no to scope creep", "A short one this week."),
    ((2026, 10, 13), "Indie Notes <hello@indienotes.example>", "Issue 43: the quiet quarter", "What to do when work slows down."),
    ((2026, 8, 4), "Mei Tan <mei@northwinddental.example>", "Logo files", "Hi Sam, could you send the logo as an SVG? Thanks, Mei"),
    ((2026, 8, 25), "Mei Tan <mei@northwinddental.example>", "Re: Invoice 102", "Paid today, thanks. £650.00 should reach you by Friday."),
    ((2026, 9, 22), "Jordan Lee <jordan@harbourlabs.example>", "Workshop date", "Does Thursday 1 October suit you for the workshop?"),
    ((2026, 10, 6), "Jordan Lee <jordan@harbourlabs.example>", "Re: Workshop date", "Great, see you then."),
    ((2026, 9, 1), "Harrow Bank <alerts@harrowbank.example>", "Your statement is ready", "Your September statement is ready to view in online banking."),
    ((2026, 10, 1), "Harrow Bank <alerts@harrowbank.example>", "Your statement is ready", "Your October statement is ready to view in online banking."),
    ((2026, 11, 1), "Harrow Bank <alerts@harrowbank.example>", "Your statement is ready", "Your November statement is ready to view in online banking."),
    ((2026, 9, 27), "Priya Shah <priya@carterstudio.example>", "Holiday cover", "I can cover the inbox the week of 12 October."),
    ((2026, 10, 28), "Spotify <no-reply@spotify.com>", "Your autumn mix is here", "New music picked for you."),
    ((2026, 11, 4), "1Password <hello@1password.com>", "A new sign-in to your account", "A new device signed in to your 1Password account."),
    ((2026, 11, 11), "Grammarly <info@send.grammarly.com>", "Your weekly writing update", "You wrote 4,812 words last week."),
]
for (y, mo, d), sender, subject, body in ordinary:
    add((y, mo, d, 10, 30), sender, subject, body + "\n")

msgs.sort(key=lambda pair: pair[0])
if OUT.exists():
    OUT.unlink()
box = mailbox.mbox(OUT)
for _, m in msgs:
    box.add(m)
box.flush()
box.close()
print(f"{len(msgs)} emails written to {OUT}")
