import argparse
import sys
from datetime import date

from .catalogue import Catalogue
from .detect import scan
from .mail import read_mbox
from .output import day, markdown, summary, totals_text, write_all


def main(argv=None):
    ap = argparse.ArgumentParser(prog="subtrim", description="Find the subscriptions in an exported mailbox. Reads only; sends nothing.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="read an mbox file and write a report plus cancellation drafts")
    s.add_argument("--mbox", required=True, help="mail export, e.g. from Google Takeout")
    s.add_argument("--me", default="", help="your email address, used in the drafts")
    s.add_argument("--today", default="", help="YYYY-MM-DD, defaults to today")
    s.add_argument("--unused", default="", help='names you know you don\'t use, e.g. "Canva,Spotify"')
    s.add_argument("--out", default="subtrim-out", help="folder for the report and drafts")
    s.add_argument("--catalogue", default=None, help="another RepoQuarry snapshot (see tools/make_catalogue.py)")
    s.add_argument("--print", action="store_true", help="print the full report as well")
    a = ap.parse_args(argv)

    today = date.fromisoformat(a.today) if a.today else date.today()
    catalogue = Catalogue(a.catalogue)
    messages, skipped = read_mbox(a.mbox)
    result = scan(messages, catalogue, today, me=a.me, unused=[u for u in a.unused.split(",") if u.strip()], skipped=skipped)
    drafts = write_all(result, catalogue, a.out)
    info = summary(result, catalogue)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.print:
        print(markdown(result, catalogue))
    print(f"{day(today)}: read {info['emails_read']} emails, {info['receipts_found']} receipts.")
    print(f"{info['subscriptions']} subscriptions, {totals_text(info['monthly_total'])} a month "
          f"({totals_text(info['yearly_total'])} a year).")
    print(f"{info['flagged']} flagged ({totals_text(info['flagged_monthly'])} a month being paid now), "
          f"{info['flagged_with_alternatives']} of them with free alternatives on RepoQuarry.")
    print(f"Left out: {info['already_cancelled']} already cancelled, {info['one_off_purchases_ignored']} one-off, "
          f"{info['suspicious_receipts_ignored']} suspicious, {info['unclear']} unclear.")
    print(f"Report: {a.out}/report.md and report.html. Drafts: {len(drafts)} in {a.out}/drafts. Nothing was sent.")
    return 0
