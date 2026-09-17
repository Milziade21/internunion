#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Structured source check: does each organisation's own page still show the stipend we publish?

For every row with a stipend and a source_url, fetch the page (own pages only, polite UA, weekly at
most) and report MATCH / DRIFT / ERROR. Optional per-org regex in fetchers.csv (name,regex) for pages
where the figure needs a specific pattern; the regex's first group must capture the amount.
Exit 1 on any DRIFT so CI can open an issue. --update stamps last_checked on MATCH rows.
Deterministic, stdlib only, no AI in the data path.

ponytail: content rendered by JavaScript is invisible to urllib; such orgs need a regex against a
JSON/API endpoint in fetchers.csv, or evidence class B (questionnaire reply) instead.
"""
import csv, re, sys, html, pathlib, datetime, urllib.request, urllib.error

HERE = pathlib.Path(__file__).parent
CSV, FETCHERS = HERE / "institutions.csv", HERE / "fetchers.csv"
UA = "internunion-source-check/1.0 (+https://github.com/Milziade21/internunion)"

def forms(amount):
    """All textual spellings of a EUR amount: 1538.16 -> {1538, 1 538, 1.538, 1,538, 1538.16, 1538,16 ...}"""
    n = float(amount); whole = int(n); out = set()
    for w in {str(whole), f"{whole:,}", f"{whole:,}".replace(",", "."), f"{whole:,}".replace(",", " ")}:
        out.add(w)
        if n != whole:
            dec = f"{n:.2f}".split(".")[1]
            out |= {f"{w}.{dec}", f"{w},{dec}"}
    return out

def text_of(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))

def check(row, regex):
    url, amt = row["source_url"].strip(), row["monthly_stipend_eur"].strip()
    if not url or not amt or "transparency-register" in url: return None
    try: page = text_of(url)
    except (urllib.error.URLError, OSError, ValueError) as e: return ("ERROR", str(e)[:80])
    if regex:
        m = re.search(regex, page)
        found = m.group(1) if m else ""
        ok = bool(m) and re.sub(r"[^\d]", "", found) == re.sub(r"[^\d]", "", f"{float(amt):.2f}").rstrip("0") \
             or (m and re.sub(r"[^\d]", "", found) == str(int(float(amt))))
        return ("MATCH" if ok else "DRIFT", f"regex -> {found!r}")
    hit = next((f for f in forms(amt) if re.search(rf"(?<![\d.,]){re.escape(f)}(?![\d])", page)), None)
    return ("MATCH" if hit else "DRIFT", f"found {hit!r}" if hit else "figure not on page")

def main(update=False):
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    rx = {r["name"]: r["regex"] for r in csv.DictReader(open(FETCHERS, encoding="utf-8"))} if FETCHERS.exists() else {}
    drift = 0; month = datetime.date.today().strftime("%Y-%m")
    for r in rows:
        res = check(r, rx.get(r["name"]))
        if not res: continue
        state, note = res; drift += state == "DRIFT"
        if state == "MATCH" and update: r["last_checked"] = month
        print(f"{state:5} {r['name'][:40]:40} {r['monthly_stipend_eur']:>8}  {note}")
    if update:
        with open(CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"\n{drift} DRIFT" if drift else "\nall sourced figures still on their pages")
    return 1 if drift else 0

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert {"1538", "1,538", "1.538", "1 538", "1538.16", "1538,16"} <= forms("1538.16")
        assert forms("950") == {"950"}
        assert "1538" in forms("1538.00") and "1538.00" not in forms("1538.00")
        print("selftest OK"); sys.exit(0)
    sys.exit(main(update="--update" in sys.argv))
