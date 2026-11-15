"""Read an mbox file (Google Takeout gives you one) into plain messages. Nothing is changed or sent."""
import email.utils
import html
import mailbox
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header, make_header


@dataclass
class Msg:
    sender_name: str
    sender_email: str
    reply_to: str
    to: str
    subject: str
    date: datetime
    body: str
    links: list

    @property
    def domain(self):
        return self.sender_email.rsplit("@", 1)[-1].lower() if "@" in self.sender_email else ""


def _header(value):
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(str(value)))).strip()
    except Exception:
        return str(value).strip()


def _strip_html(text):
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return html.unescape(text)


def _body(message):
    plain, rich = [], []
    for part in message.walk():
        if part.get_content_maintype() != "text" or part.get_filename():
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        (rich if part.get_content_subtype() == "html" else plain).append(text)
    raw_html = "\n".join(rich)
    links = re.findall(r'https?://[^\s"\'<>)\]]+', "\n".join(plain) + "\n" + raw_html)
    text = "\n".join(plain) if plain else _strip_html(raw_html)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    seen, unique = set(), []
    for link in links:
        link = link.rstrip(".,;")
        if link not in seen:
            seen.add(link)
            unique.append(link)
    return text, unique


def read_mbox(path):
    """Every readable message in the file, oldest first. Unreadable ones are counted, not guessed."""
    out, skipped = [], 0
    box = mailbox.mbox(path, create=False)
    try:
        for message in box:
            try:
                name, addr = email.utils.parseaddr(_header(message.get("From")))
                when = email.utils.parsedate_to_datetime(message.get("Date"))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                body, links = _body(message)
                out.append(Msg(
                    sender_name=name or addr.split("@")[0],
                    sender_email=addr.lower(),
                    reply_to=email.utils.parseaddr(_header(message.get("Reply-To")))[1].lower(),
                    to=email.utils.parseaddr(_header(message.get("To")))[1].lower(),
                    subject=_header(message.get("Subject")),
                    date=when,
                    body=body,
                    links=links,
                ))
            except Exception:
                skipped += 1
    finally:
        box.close()
    out.sort(key=lambda m: m.date)
    return out, skipped
