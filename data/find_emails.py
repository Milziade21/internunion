#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Local, one-off: find a contact email for each CURATED Brussels org, for sending the
questionnaire. Fetches the org's own website (homepage + a few contact pages) and extracts an
email, preferring a generic mailbox (info@, contact@, careers@) over a named person.

Output -> data/contacts.local.csv (GITIGNORED). Emails are contact data, much of it personal:
never commit them, never publish them, and before any mass send check GDPR + the anti-spam rules
on unsolicited communication (prefer generic addresses, offer opt-out). This script only builds
the list. Run: python3 find_emails.py

ponytail: curated set only (~60 orgs). Do NOT point this at the 3,300 register orgs -- mass
scraping is slow, brittle, and legally fraught; those are candidates, not questionnaire targets yet.
"""
import csv, re, time, ssl, urllib.request, urllib.error, pathlib
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).parent
UA = "internunion-bot/1.0 (+https://internunion.com; contact@internunion.com)"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
GENERIC = ("info", "contact", "office", "hello", "welcome", "careers", "career", "jobs", "job",
           "hr", "recruitment", "recruiting", "traineeship", "stage", "internship", "secretariat",
           "general", "mail", "press", "communication")
JUNK = ("example.com", "sentry", "wixpress", "wix.com", "godaddy", "@2x", ".png", ".jpg", ".gif",
         "domain.com", "email.com", "yourdomain", "u003e", "core.min", "schema.org")
PAGES = ("", "/contact", "/en/contact", "/contact-us", "/careers", "/jobs", "/about")

def fetch(url):
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
        return r.read(600_000).decode("utf-8", "ignore")

def candidates(html, domain):
    found = {}
    for e in EMAIL_RE.findall(html):
        e = e.lower().rstrip(".")
        if any(j in e for j in JUNK):
            continue
        local, _, dom = e.partition("@")
        score = (2 if domain and domain in dom else 0) + (1 if local in GENERIC else 0)
        found[e] = max(found.get(e, -1), score)
    return found

def best_email(url):
    host = urlparse(url if "://" in url else "https://" + url).netloc.lower()
    domain = ".".join(host.split(".")[-2:]) if host else ""
    base = f"https://{host}" if host else url
    pool = {}
    for path in PAGES:
        try:
            pool.update(candidates(fetch(base + path), domain))
        except Exception:
            pass
        if any(s == 3 for s in pool.values()):   # domain-matched generic: good enough, stop early
            break
        time.sleep(0.5)
    # keep ONLY emails on the org's own domain -> drops cross-domain scraping noise
    pool = {e: s for e, s in pool.items()
            if domain and (e.split("@")[1] == domain or e.split("@")[1].endswith("." + domain))}
    if not pool:
        return "", "none", ""
    email = max(pool, key=pool.get)
    kind = "generic" if email.split("@")[0] in GENERIC else "personal"
    others = ";".join(sorted(pool, key=pool.get, reverse=True)[:4])
    return email, kind, others

def main():
    rows = list(csv.DictReader(open(HERE / "institutions.csv")))
    targets = [r for r in rows if r["city"] == "Brussels" and r.get("loc", "exact") != "approx"]
    out = []
    for r in targets:
        try:
            email, kind, others = best_email(r["source_url"])
        except Exception as e:
            email, kind, others = "", f"error:{type(e).__name__}", ""
        out.append({"name": r["name"], "type": r["type"], "email": email, "kind": kind,
                    "candidates": others, "website": r["source_url"]})
        print(f'{kind:>8}  {email or "-":<38} {r["name"][:34]}')
        time.sleep(0.6)
    with open(HERE / "contacts.local.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "type", "email", "kind", "candidates", "website"])
        w.writeheader(); w.writerows(out)
    got = sum(1 for o in out if o["email"])
    gen = sum(1 for o in out if o["kind"] == "generic")
    print(f"\n{got}/{len(out)} emails found ({gen} generic). -> data/contacts.local.csv (gitignored)")

if __name__ == "__main__":
    main()
