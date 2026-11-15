"""Match a merchant to a paid product in the RepoQuarry snapshot and list its open-source alternatives."""
import json
import pathlib
import re

DEFAULT = pathlib.Path(__file__).with_name("catalogue.json")
PLAN_WORDS = {"pro", "plus", "premium", "business", "personal", "team", "teams", "individual", "family", "families",
              "basic", "starter", "standard", "enterprise", "cloud", "app", "subscription", "membership"}


def norm(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def brand_label(url):
    """'https://www.notion.com/pricing' -> 'notion'."""
    host = re.sub(r"^https?://", "", url or "").split("/")[0].lower()
    parts = [p for p in host.split(".") if p not in ("www",)]
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org") and len(parts[-1]) == 2:
        return parts[-3]
    return parts[-2] if len(parts) >= 2 else (parts[0] if parts else "")


class Catalogue:
    def __init__(self, path=None):
        raw = json.loads(pathlib.Path(path or DEFAULT).read_text(encoding="utf-8"))
        self.snapshot_date = raw.get("snapshot_date", "unknown")
        self.products = raw["products"]
        self._by_name = {}
        for p in self.products:
            self._by_name[norm(p["name"])] = p
            self._by_name[norm(p["id"])] = p
            label = brand_label(p.get("url"))
            if label and len(label) > 3:
                self._by_name.setdefault(norm(label), p)

    def match(self, merchant):
        """Exact name, id or website label only. A near miss returns None: we would rather say
        'not in RepoQuarry' than point at the wrong product."""
        key = norm(merchant)
        if key in self._by_name:
            return self._by_name[key]
        # 'Canva Pro' is Canva. 'Make It Studio' is not Make: only plan words may follow the name.
        words = [w for w in re.split(r"[^A-Za-z0-9]+", merchant or "") if w]
        if len(words) > 1 and norm(words[0]) in self._by_name and all(w.lower() in PLAN_WORDS for w in words[1:]):
            return self._by_name[norm(words[0])]
        return None

    def alternatives(self, product, limit=3):
        return (product or {}).get("alternatives", [])[:limit]
