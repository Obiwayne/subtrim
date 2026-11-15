# Subtrim

Finds the subscriptions hiding in your email, drafts the cancellation for the ones you don't use, and suggests a free open-source alternative for each from [RepoQuarry](https://repoquarry.dev).

Subtrim is two things:

1. **A Grok Bot skill and routine** (`grok-bot/`). Once a month the Bot reads the receipts in your Gmail, lists what you pay for, and flags a subscription only when it can show you why. It writes a cancellation draft when you ask, and sends one only when you say "send". **Not yet tested on Grok Bot.**
2. **A preview tool** (`subtrim/`). It does the same scan on your own computer from an exported mailbox, so you can see what you'd get before any agent reads your mail. Python 3.10 or later, nothing to install, and it sends nothing. This part is tested.

## Try it in a minute

```
python -m subtrim scan --mbox sample/mail.mbox --me sam@carterstudio.example --today 2026-11-15 --out my-report --print
```

Open `my-report/report.html`. Everything in `sample/` is made up, including every price. Real product names are used only to show the RepoQuarry match.

## Use your own mail

1. Export your mail from [Google Takeout](https://takeout.google.com) (Mail only). You get an `.mbox` file.
2. Run `python -m subtrim scan --mbox "All mail.mbox" --me you@example.com`.
3. Add `--unused "Canva,Spotify"` to flag things you know you don't use.

You get, in `subtrim-out/`:

- `report.md` and `report.html`: every subscription with its charge, cost a month, last charge date and free alternatives
- `subscriptions.json`: the same as data
- `drafts/`: one `.eml` cancellation request per flagged subscription. Open it in your mail app to read and send it yourself.

## What counts, and what doesn't

- **A charge** is an email with receipt wording and an amount. Receipts sent by Stripe, PayPal and the like are filed under the company named in the subject.
- **A subscription** is a charge that repeats on a steady gap (weekly, monthly, every three months, yearly), or a single receipt that says it renews.
- **Flagged** means there is a reason you can read: the company's own "we miss you" email from the last 120 days, a free trial about to turn paid, or your own `--unused`. Subtrim can't see how much you use something, and doesn't guess.
- **Worth a look** covers price changes and two tools RepoQuarry lists for the same job. These are notes, not flags.
- **Left out of the total:** things already cancelled, charges that stopped, one-off orders, mail you sent yourself, and receipts that use a known company's name from an address that isn't theirs.
- Each currency is totalled on its own. Pounds are never added to dollars.

## The alternatives

`subtrim/catalogue.json` is a snapshot of RepoQuarry's catalogue taken on 15 November 2026: 90 paid products and the open-source projects listed for each, with licence and how much of the job each covers. The data is CC BY 4.0. Licences change, so open the linked page before you switch. To refresh the snapshot from a RepoQuarry checkout: `python tools/make_catalogue.py <path to data> --date <today>` (needs PyYAML).

A subscription only gets alternatives when its name matches a product exactly. If RepoQuarry doesn't cover it, the report says "none listed".

## What we tested (15 November 2026, Windows 11, Python 3.13.5)

- 42 automated tests pass (`python -m unittest discover -s tests`).
- On the sample inbox of 62 emails, Subtrim found 33 receipts and 10 subscriptions costing £112.54 a month (£1,350.48 a year).
- It flagged 3: one where the company's own email said no video had been recorded in 60 days, one "we miss you" on a yearly plan that had renewed 9 days earlier (so the draft asks for a refund), and one free trial due to turn paid 5 days later. The two already being paid for cost £20.33 a month.
- 8 of the 10 subscriptions matched a RepoQuarry product and got three alternatives each. The other 2 got "none listed".
- It left out 1 subscription already cancelled, 2 one-off purchases, 1 invoice the user had sent, and 1 fake receipt that used Notion's name from another address.
- The same three lookups were run against the live RepoQuarry MCP server (`https://repoquarry.dev/mcp`): Loom and Evernote came back named as paid products with alternatives, and Spotify came back with no product named, which is how the skill knows to say "none listed".

## What we haven't tested

- The skill and routine on a real Grok Bot plan, or how much of the weekly allowance a run uses.
- A real inbox. The sample receipts are tidy and all in English and pounds. Real receipts vary a lot, so expect misses and check the report against your bank statement.
- Receipts that arrive as PDF attachments only, or in other languages. Subtrim reads the email text.
- Subscriptions billed through an app store with no email receipt. Subtrim can't see those.

## Licences

Subtrim is MIT. The catalogue snapshot is RepoQuarry data, CC BY 4.0.

`sample/make_sample.py` rebuilds the sample inbox.
