# Subtrim routine for Grok Bot

Status: **not yet tested on Grok Bot.**

## The one scheduled run

Ask your Bot:

> Create a routine called "Subtrim monthly". On the 1st of each month at 08:00 in my time zone, run the Subtrim skill's dry run (steps 1 to 3) and send me the result as one message. Run it once. Don't retry more than once if it fails, and tell me if it did. Don't write any drafts until I ask.

That is 12 scheduled runs a year. Subscriptions change slowly, so a daily or weekly run would spend your allowance and tell you nothing new.

## Drafts happen when you ask

Reply "draft Loom, Evernote" and the Bot writes one Gmail draft for each. Reply "send Loom" to send one. Nothing goes out without that.

## Connecting RepoQuarry

Ask your Bot to add the MCP server at `https://repoquarry.dev/mcp`. It is read-only and needs no key. Adding MCP servers through chat is described by Composio, not in xAI's own documentation, so it may not work on every plan. If it doesn't, the skill reads the same facts from pages such as `https://repoquarry.dev/alternatives/loom.md`.

## Cost

| | |
|---|---|
| Plan needed | X Premium ($30/month) or higher, which includes Grok Bot |
| Scheduled runs | 1 a month |
| Extra runs | 1 each time you ask for drafts |
| Share of the weekly allowance | Not measured. We have no Grok Bot plan to test on yet. The first run reads 13 months of receipts, so expect it to be the biggest. |
| RepoQuarry | Free: the MCP server and the pages need no account |

## Before the first run

Try the preview tool in this repo on an export of your mail. It shows what a scan finds on your own computer, before any agent reads your inbox.
