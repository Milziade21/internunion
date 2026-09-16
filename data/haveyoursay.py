#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Org discovery: which Brussels organisations are active on a policy file?

The Commission's Have Your Say portal publishes every feedback submission on every initiative.
Each one carries the respondent's ORGANISATION, its type, its country and — the useful part — its
EU Transparency Register number, which joins straight onto data/institutions.csv. So a policy file
gives us a targeted list of the bodies lobbying it, and therefore the employers to send the
questionnaire to next. It is not a vacancy source; it is a targeting source.

GDPR: every record also carries firstName, surname and login. Those are DISCARDED at ingest and
never written to disk. We keep only organisation-level fields.

  python3 data/haveyoursay.py --selftest         # no network
  python3 data/haveyoursay.py --search "traineeship"
  python3 data/haveyoursay.py --publication 10120 --out data/hys_orgs.csv

ponytail: this is the portal's own SPA backend, not a documented API -- no ToS, no stability
guarantee. Fail soft, cache what you pull, and never make it a build-time dependency.
"""
import csv, json, sys, time, pathlib, urllib.parse, urllib.request, urllib.error

BASE = "https://ec.europa.eu/info/law/better-regulation"
UA = "internunion-discovery/1.0 (+https://github.com/Milziade21/internunion)"
HERE = pathlib.Path(__file__).parent
# Organisation-level only. firstName/surname/login are deliberately absent from this list.
KEEP = ["organization", "userType", "country", "companySize", "trNumber", "dateFeedback",
        "publicationId", "referenceInitiative"]

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def search_initiatives(q, size=20):
    url = f"{BASE}/brpapi/searchInitiatives?{urllib.parse.urlencode({'text': q, 'page': 0, 'size': size})}"
    d = _get(url)
    page = d.get("initiativeResultDtoPage") or {}
    out = []
    for it in page.get("content", []):
        cur = next((c for c in (it.get("currentStatuses") or []) if c.get("isCurrent")), {})
        title = ""
        for t in (it.get("initiativeTranslations") or []):
            if t.get("languageCode") in ("EN", "en"): title = t.get("shortTitle") or t.get("title") or ""; break
        out.append({"id": it.get("id"), "reference": it.get("reference"),
                    "title": title or it.get("shortTitle") or "",
                    "status": it.get("initiativeStatus"),
                    "feedback": cur.get("receivingFeedbackStatus", "")})
    return out, page.get("totalElements", 0)

def feedback_orgs(publication_id, size=200, max_pages=25):
    """Organisation-level rows for one publication. Personal fields are dropped here, not later."""
    rows, seen = [], set()
    for page in range(max_pages):
        url = f"{BASE}/api/allFeedback?{urllib.parse.urlencode({'publicationId': publication_id, 'page': page, 'size': size})}"
        try: d = _get(url)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as e:
            print(f"  stopped at page {page}: {str(e)[:70]}"); break
        content = d.get("content") or []
        if not content: break
        for f in content:
            org = (f.get("organization") or "").strip()
            if not org: continue                       # individual respondent: not our business
            key = (org, f.get("trNumber") or "")
            if key in seen: continue
            seen.add(key)
            rows.append({k: f.get(k, "") for k in KEEP})
        if len(content) < size: break
        time.sleep(0.5)
    return rows

def main(argv):
    if "--search" in argv:
        q = argv[argv.index("--search") + 1]
        items, total = search_initiatives(q)
        print(f"{total} initiatives match {q!r}; showing {len(items)}\n")
        for it in items:
            print(f"  id={it['id']:<8} {it['feedback']:<8} {it['reference']:<22} {it['title'][:60]}")
        print("\nThen: python3 data/haveyoursay.py --publication <id>")
        return 0
    if "--publication" in argv:
        pid = argv[argv.index("--publication") + 1]
        rows = feedback_orgs(pid)
        print(f"{len(rows)} distinct organisations responded to publication {pid}")
        known = {r["name"] for r in csv.DictReader(open(HERE / "institutions.csv", encoding="utf-8"))}
        new = [r for r in rows if r["organization"] not in known]
        print(f"{len(rows)-len(new)} already in institutions.csv, {len(new)} new candidates")
        if "--out" in argv:
            out = pathlib.Path(argv[argv.index("--out") + 1])
            with open(out, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=KEEP); w.writeheader(); w.writerows(rows)
            print(f"wrote {out}")
        else:
            for r in rows[:25]:
                print(f"  {r['userType']:<22} {r['country']:<5} TR={r['trNumber'] or '-':<18} {r['organization'][:46]}")
        return 0
    print(__doc__); return 1

def selftest():
    assert "firstName" not in KEEP and "surname" not in KEEP and "login" not in KEEP, \
        "personal fields must never be in the keep list"
    assert "trNumber" in KEEP, "the Transparency Register number is the join key"
    assert set(KEEP) <= {"organization", "userType", "country", "companySize", "trNumber",
                         "dateFeedback", "publicationId", "referenceInitiative"}
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit(0)
    sys.exit(main(sys.argv))
