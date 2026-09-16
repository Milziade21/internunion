#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Coverage-first internship/traineeship vacancy fetcher -> data/vacancies.csv.

Guardrails (see STRATEGY.md and SOURCES_POLICY.md) -- these are not preferences, they are the rules:
  * Only an ORGANISATION'S OWN careers endpoint, or an official consolidated public view.
  * Never a commercial job board. jobsin.brussels and Idealist forbid automated collection in their
    terms and assert database rights; Devex blocks all access. They are permanently out of scope.
  * robots.txt is checked before every fetch, with our own named user agent.
  * Deterministic only: keyword tables, no model, no fuzzy matching anywhere in the data path.

Add a source by adding one line to data/feeds.csv (org,kind,token,note). Run: python3 data/vacancies.py
Self-test (no network): python3 data/vacancies.py --selftest
"""
import csv, json, re, sys, html, time, pathlib, datetime
import urllib.request, urllib.error, urllib.parse, urllib.robotparser

HERE = pathlib.Path(__file__).parent
FEEDS, OUT = HERE / "feeds.csv", HERE / "vacancies.csv"
UA = "internunion-vacancies/1.0 (+https://github.com/Milziade21/internunion)"
COLS = ["org", "title", "url", "location", "employment_type", "level", "posted", "source_kind", "fetched"]
TODAY = datetime.date.today().isoformat()

# --- deterministic classification -------------------------------------------------------------
# ponytail: plain keyword tables in EN/FR/NL/DE. Ceiling: a title in another language, or a creative
# one ("Young Talent Programme"), is missed -- add the word here rather than reaching for a model.
INTERN_WORDS = ("intern", "internship", "trainee", "traineeship", "stage ", "stagiaire", "stagiair",
                "praktikum", "praktikant", "apprentice", "blue book", "schuman", "graduate programme",
                "study visit", "young professional")
# First match wins, so EXPLICIT seniority markers ("senior", "junior") must be tested before role
# nouns ("officer", "analyst"): otherwise "Senior Policy Officer" is filed as mid. The self-test pins
# exactly this ordering -- reorder these rows and it fails.
LEVELS = [
    ("internship", ("intern", "trainee", "stage ", "stagiaire", "stagiair", "praktik", "study visit",
                    "blue book", "schuman", "apprentice")),
    ("senior (5y+)", ("senior", "head of", "director", "lead ", "principal", "chief")),
    ("entry (0-2y)", ("junior", "graduate", "entry level", "entry-level", "assistant", "young professional")),
    ("mid (2-5y)", ("officer", "analyst", "coordinator", "advisor", "adviser", "manager", "associate")),
]

def level_of(title, etype=""):
    t = (title + " " + (etype or "")).lower()
    for label, words in LEVELS:
        if any(w in t for w in words): return label
    return "unspecified"

def is_internship(title, etype=""):
    t = (title + " " + (etype or "")).lower()
    return any(w in t for w in INTERN_WORDS)

# --- polite fetching ---------------------------------------------------------------------------
_robots = {}
def allowed(url):
    """Check robots.txt for our UA. Fail CLOSED: if robots cannot be read, we do not fetch."""
    p = urllib.parse.urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    if root not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(root + "/robots.txt")
        try: rp.read()
        except Exception: rp = None
        _robots[root] = rp
    rp = _robots[root]
    return bool(rp) and rp.can_fetch(UA, url)

def get(url, data=None, ctype=None):
    if not allowed(url):
        raise PermissionError(f"robots.txt disallows (or is unreadable at) {url}")
    hdr = {"User-Agent": UA, "Accept-Language": "en"}
    if ctype: hdr["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=hdr)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

# --- per-source adapters -----------------------------------------------------------------------
def _views_field(block, name):
    """Drupal views markup: <span class="views-field views-field-NAME">[<span class="views-label">..
    </span>]<span class="field-content">VALUE</span>. Return VALUE, tags stripped."""
    m = re.search(r'views-field-%s"(.*?)(?:<BR>|</div>)' % re.escape(name), block, re.S | re.I)
    if not m: return ""
    inner = m.group(1)
    c = re.search(r"field-content[^>]*>(.*)$", inner, re.S)
    return strip(c.group(1) if c else inner)

def from_epso(org, token):
    """The consolidated EU traineeships view. Rows are `views-row` divs, NOT a table -- the fields are
    span.views-field-*, so parse those. Covers institutions and agencies together."""
    # The view ignores ?page= when the result set fits one page and simply re-serves the same rows,
    # so paginate on NEW keys seen, not on row count -- otherwise every traineeship lands 6 times.
    rows, base, seen = [], "https://eu-careers.europa.eu", set()
    for page in range(6):
        h = get(f"{base}/en/traineeships-open?page={page}")
        blocks = re.split(r"views-row", h)[1:]
        found = 0
        for b in blocks:
            title = _views_field(b, "title")
            if not title: continue
            link = ""
            lm = re.search(r'views-field-field-epso-link"(.*?)(?:<BR>|</div>)', b, re.S | re.I)
            if lm:
                a = re.search(r'href="([^"]+)"', lm.group(1))
                if a: link = urllib.parse.urljoin(base, a.group(1))
            inst = _views_field(b, "field-epso-institution") or org
            key = (inst, title, link)
            if key in seen: continue
            seen.add(key)
            rows.append({"org": inst, "title": title,
                         "url": link, "location": _views_field(b, "field-epso-location"),
                         "employment_type": "traineeship",
                         "posted": _views_field(b, "field-epso-deadline"), "source_kind": "epso"})
            found += 1
        if not found: break
        time.sleep(1)
    return rows

def from_agencies_sitemap(org, token):
    """EU Agencies Network: the sitemap is the only structured handle to vacancy notices."""
    h = get("https://agencies-network.europa.eu/sitemap.xml")
    out = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", h):
        if "vacancy-notice" not in loc: continue
        slug = loc.rstrip("/").rsplit("/", 1)[-1].replace("vacancy-notice-", "")
        out.append({"org": org, "title": slug.replace("-", " ").strip().title(), "url": loc,
                    "location": "", "employment_type": "", "posted": "", "source_kind": "agencies"})
    return out

def from_personio(org, token):
    x = get(f"https://{token}.jobs.personio.com/xml")
    out = []
    for pos in re.findall(r"<position>(.*?)</position>", x, re.S):
        def tag(t):
            m = re.search(r"<%s>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (t, t), pos, re.S)
            return strip(m.group(1)) if m else ""
        out.append({"org": org, "title": tag("name"),
                    "url": f"https://{token}.jobs.personio.com/job/{tag('id')}",
                    "location": ", ".join(f for f in (tag("office"), tag("additionalOffices")) if f),
                    "employment_type": tag("employmentType"), "posted": tag("createdAt")[:10],
                    "source_kind": "personio"})
    return out

def from_recruitee(org, token):
    d = json.loads(get(f"https://{token}.recruitee.com/api/offers/"))
    return [{"org": org, "title": o.get("title", ""), "url": o.get("careers_apply_url", ""),
             "location": o.get("location", ""), "employment_type": o.get("employment_type_code", "") or "",
             "posted": (o.get("created_at") or "")[:10], "source_kind": "recruitee"}
            for o in d.get("offers", [])]

def from_greenhouse(org, token):
    d = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"))
    return [{"org": org, "title": j.get("title", ""), "url": j.get("absolute_url", ""),
             "location": (j.get("location") or {}).get("name", ""), "employment_type": "",
             "posted": (j.get("updated_at") or "")[:10], "source_kind": "greenhouse"}
            for j in d.get("jobs", [])]

def from_lever(org, token):
    d = json.loads(get(f"https://api.lever.co/v0/postings/{token}?mode=json"))
    return [{"org": org, "title": j.get("text", ""), "url": j.get("hostedUrl", ""),
             "location": (j.get("categories") or {}).get("location", "") or "",
             "employment_type": (j.get("categories") or {}).get("commitment", "") or "",
             "posted": datetime.datetime.utcfromtimestamp(j["createdAt"] / 1000).date().isoformat()
                       if j.get("createdAt") else "", "source_kind": "lever"}
            for j in d]

def from_ashby(org, token):
    d = json.loads(get(f"https://api.ashbyhq.com/posting-api/job-board/{token}"))
    return [{"org": org, "title": j.get("title", ""), "url": j.get("jobUrl", ""),
             "location": j.get("location", ""), "employment_type": j.get("employmentType", ""),
             "posted": (j.get("publishedAt") or "")[:10], "source_kind": "ashby"}
            for j in d.get("jobs", [])]

def from_smartrecruiters(org, token):
    d = json.loads(get(f"https://api.smartrecruiters.com/v1/companies/{token}/postings"))
    out = []
    for j in d.get("content", []):
        loc = j.get("location") or {}
        out.append({"org": org, "title": j.get("name", ""),
                    "url": f"https://jobs.smartrecruiters.com/{token}/{j.get('id','')}",
                    "location": ", ".join(f for f in (loc.get("city"), loc.get("country")) if f),
                    "employment_type": "", "posted": (j.get("releasedDate") or "")[:10],
                    "source_kind": "smartrecruiters"})
    return out

ADAPTERS = {"epso": from_epso, "agencies_sitemap": from_agencies_sitemap, "personio": from_personio,
            "recruitee": from_recruitee, "greenhouse": from_greenhouse, "lever": from_lever,
            "ashby": from_ashby, "smartrecruiters": from_smartrecruiters}

def main(internships_only=True):
    feeds = list(csv.DictReader(open(FEEDS, encoding="utf-8")))
    rows, errs = [], 0
    for f in feeds:
        fn = ADAPTERS.get(f["kind"])
        if not fn:
            print(f"SKIP  {f['org']}: unknown kind {f['kind']!r}"); continue
        try:
            got = fn(f["org"], f["token"])
        except (urllib.error.URLError, OSError, ValueError, PermissionError) as e:
            print(f"ERROR {f['org']} ({f['kind']}): {str(e)[:90]}"); errs += 1; continue
        kept = [r for r in got if not internships_only or is_internship(r["title"], r["employment_type"])]
        for r in kept:
            r["level"] = level_of(r["title"], r["employment_type"]); r["fetched"] = TODAY
        rows.extend(kept)
        print(f"OK    {f['org']:46} {len(kept):3} of {len(got):3} kept")
        time.sleep(1)
    seen, uniq = set(), []
    for r in rows:                       # a source can legitimately repeat a posting across pages
        k = (r["org"], r["title"], r["url"])
        if k not in seen: seen.add(k); uniq.append(r)
    dropped, rows = len(rows) - len(uniq), uniq
    if dropped: print(f"      ({dropped} duplicate row(s) collapsed)")
    rows.sort(key=lambda r: (r["org"].lower(), r["title"].lower()))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"\n{len(rows)} open internships -> {OUT.name} ({errs} source error(s))")
    return 0

def selftest():
    assert is_internship("Blue Book Traineeship") and is_internship("Stagiaire communication")
    assert is_internship("Policy Officer", "Internship") and not is_internship("Head of Policy")
    assert level_of("Schuman Trainee") == "internship"
    assert level_of("Junior Policy Analyst") == "entry (0-2y)"
    assert level_of("Senior Policy Officer") == "senior (5y+)"   # explicit seniority beats the role noun
    assert level_of("Head of Communications") == "senior (5y+)"
    assert level_of("Junior Policy Analyst") != "mid (2-5y)"
    assert level_of("Policy Analyst") == "mid (2-5y)"
    assert level_of("Office Cat") == "unspecified"
    assert strip("<p>Hello &amp;   world</p>") == "Hello & world"
    row = ('"><span class="views-field views-field-title"><h2 class="field-content">Traineeships - SatCen'
           '</h2></span><BR><span class="views-field views-field-field-epso-location">'
           '<span class="views-label views-label-field-epso-location">Location(s): </span>'
           '<span class="field-content">Torrejon de Ardoz (Spain)</span></span><BR>')
    assert _views_field(row, "title") == "Traineeships - SatCen"
    assert _views_field(row, "field-epso-location") == "Torrejon de Ardoz (Spain)"   # label stripped
    assert _views_field(row, "field-epso-deadline") == ""
    assert level_of("Traineeships - ACER") == "internship" and is_internship("Traineeships - ACER")
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit(0)
    sys.exit(main(internships_only="--all" not in sys.argv))
