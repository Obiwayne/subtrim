# Subtrim build log

Build 4 in RepoQuarry's queue. Built by a scheduled, unattended run on 15 November 2026 (Windows 11, Python 3.13.5). Times are from the PC's clock, UK time.

| Time | What |
|---|---|
| 08:35 | Start. Queue entry 4 picked: no Subtrim folder or review row yet. One build (Prepnote) was waiting, so the stop rule didn't apply. |
| 08:36 | Parts checked. The queue lists no outside repos for Subtrim. Its only source is RepoQuarry's own catalogue (CC BY 4.0), read from `origin/main` at commit 9771f51. |
| 08:37 | Catalogue snapshot made: 90 paid products, 549 links to open-source alternatives. |
| 08:37-08:43 | Preview tool written: mailbox reader, receipt and subscription rules, catalogue match, report and drafts. Sample inbox of 62 made-up emails written. |
| 08:43 | 42 tests pass. Sample run gives the numbers below. |
| 08:44 | Three lookups run against the live RepoQuarry MCP server and one Markdown page fetched, to check what the skill relies on. |
| 08:44-08:46 | Skill, routine and README written. |
| 08:46-08:53 | Voiceover (one ElevenLabs pass: 7 new lines, line 1 reused from the approved take), stills checked in both sizes, 20 s video rendered in 16:9 and 9:16 at -14.0 LUFS. |
| 08:53-08:56 | Cover, two screenshots, six slides, guide page and posts written. Two faults found in the pictures and fixed (see below). |
| 08:56-09:00 | Guide checked on its branch: validate and build pass; tests 1,150 of 1,160, the 9 tar-archive failures that also fail on untouched main on this PC, and 1 that passed when run again alone. |
| 09:00 | End of the build. Nothing pushed or posted. |

## Numbers measured (sample inbox, "today" set to 15 Nov 2026)

- 62 emails read, 0 unreadable. 33 receipts for repeat charges.
- 10 subscriptions, £112.54 a month, £1,350.48 a year. All in pounds.
- 3 flagged, each with a draft:
  - Loom, £12.00 a month. Its own email of 2 Nov said "You haven't recorded a video in 60 days."
  - Evernote, £99.99 a year (£8.33 a month). "We miss you" email of 12 Oct. Renewed 6 Nov, 9 days before, so the draft asks for a refund.
  - Framecast (a made-up company), free trial turning paid on 20 Nov at £14.00 a month. Not charged yet, so not in the total.
- The two flagged subscriptions already being paid for: £20.33 a month.
- 2 of the 3 drafts had no recipient, because the receipts came from no-reply addresses. Both got the account page from the company's own email instead.
- 8 of 10 subscriptions matched a RepoQuarry product, with 3 alternatives shown for each. 2 (Spotify, Brightline Mobile) got "none listed".
- Left out of the total: 1 already cancelled (Skillpath), 2 one-off purchases (Deskhaus, Oak & Iron Coffee through PayPal), 1 fake receipt using Notion's name (£89.00). An invoice the user had sent, and a client's email mentioning £650.00, were ignored.
- Notes without a flag: Zapier's price up from £19.99 to £24.99, the phone bill down from £19.10 to £18.75, and two pairs RepoQuarry lists for the same kind of job (Notion with Evernote, 1Password with LastPass).

Every email, price and date in the sample is invented. Real product names are used only to show the catalogue match.

## Live checks

- `https://repoquarry.dev/mcp`, tool `search_projects`, limit 3. "Loom": named as a paid product, 11 matches (the snapshot also has 11). "Evernote": named as a paid product. "Spotify": no paid product named, two loosely related results. The skill tells the Bot to use results only when a paid product is named.
- `https://repoquarry.dev/alternatives/loom.md` returned 200 as Markdown. This is the skill's fallback when MCP can't be added.

## Found and fixed during the build

- A charge pattern with gaps of 8, 113 and 33 days was called "monthly" because only the middle gap was checked. Now most gaps must fit.
- "Make It Studio" matched the product Make and would have been called a fake receipt. Now only plan words (Pro, Plus, Premium...) may follow a product's name.
- The HTML report printed `\1` instead of names under "Worth a look".
- The refund line in the draft said "I haven't used the service since", which Subtrim can't know. Removed.

## Not tested, and why

- **Grok Bot.** No plan to test on. The skill and routine come from xAI's documentation.
- **A real inbox.** Only the sample: tidy, in English, all in pounds. Mixed currencies are covered by a unit test only.
- **PDF-only receipts, other languages, app-store subscriptions with no email.**
- **Adding the MCP server to a Bot through chat.** Described by Composio, not by xAI.
- **Share of the Grok Bot weekly allowance.** Not measurable without a plan.

## Cost

- Plan: X Premium ($30/month) or higher for Grok Bot.
- Runs: 1 scheduled run a month (12 a year), plus 1 each time you ask for drafts.
- Cap: one run a month, no retry loop, the list only past 70% of the allowance, no Bot-to-Bot hand-offs.
- RepoQuarry's MCP server and pages: free, no account.
