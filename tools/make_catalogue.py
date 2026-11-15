"""Build subtrim/catalogue.json from a checkout of RepoQuarry's data folder.

Needs PyYAML (pip install pyyaml). The scanner itself needs nothing but Python.

    python tools/make_catalogue.py F:/path/to/RepoQuarry/data --commit 9771f51 --date 2026-11-15

RepoQuarry's data is CC BY 4.0. Facts change, so the snapshot carries its date.
"""
import argparse
import json
import pathlib

import yaml

ORDER = {"full": 0, "partial": 1}
OPEN = {"yes": 0, "partial": 1, "no": 2}


def fact(project, key):
    f = (project.get("facts") or {}).get(key) or {}
    status = {True: "yes", False: "no"}.get(f.get("status"), f.get("status") or "unknown")
    return {"status": status, "value": f.get("value"), "checked_at": f.get("checked_at")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--commit", default="")
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "subtrim" / "catalogue.json"))
    a = ap.parse_args()
    data = pathlib.Path(a.data)

    products = {}
    for p in sorted((data / "products").glob("*.yaml")):
        y = yaml.safe_load(p.read_text(encoding="utf-8"))
        products[y["id"]] = {
            "id": y["id"],
            "name": y["name"],
            "url": y.get("url"),
            "category": y.get("category"),
            "pricing": y.get("pricing"),
            "pricing_checked_at": y.get("pricing_checked_at"),
            "page": f"https://repoquarry.dev/alternatives/{y['id']}/",
            "alternatives": [],
        }

    for p in sorted((data / "projects").glob("*.yaml")):
        y = yaml.safe_load(p.read_text(encoding="utf-8"))
        if y.get("draft") or y.get("status") == "draft":
            continue
        lic = fact(y, "code_license")
        spdx = ((y.get("facts") or {}).get("code_license") or {}).get("spdx")
        for alt in y.get("alternatives") or []:
            prod = products.get(alt.get("product"))
            if not prod:
                continue
            prod["alternatives"].append({
                "id": y["id"],
                "name": y["name"],
                "coverage": alt.get("coverage", "unknown"),
                "licence": spdx or lic["value"] or "unknown",
                "open_source": lic["status"],
                "commercial_use": fact(y, "commercial_use")["status"],
                "runs_locally": fact(y, "runs_locally")["status"],
                "checked_at": lic["checked_at"],
                "page": f"https://repoquarry.dev/projects/{y['id']}/",
            })

    for prod in products.values():
        prod["alternatives"].sort(key=lambda x: (ORDER.get(x["coverage"], 2), OPEN.get(x["open_source"], 3), x["name"].lower()))

    out = {
        "source": "https://repoquarry.dev (data licence CC BY 4.0)",
        "snapshot_date": a.date,
        "commit": a.commit,
        "products": list(products.values()),
    }
    pathlib.Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    n = sum(len(p["alternatives"]) for p in products.values())
    print(f"{len(products)} products, {n} alternative links, written to {a.out}")


if __name__ == "__main__":
    main()
