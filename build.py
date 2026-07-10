#!/usr/bin/env python3
"""Generate the internunion static site from data/institutions.csv.

Zero dependencies (stdlib only). Output -> public/. Deploy that folder anywhere
static (Railway, Cloudflare Pages, GitHub Pages). Run: python3 build.py

Discoverability baked in per the 2026 GEO/SEO research: server-rendered HTML,
answer-first content, schema.org Dataset + Organization + WebSite + FAQPage
JSON-LD, robots.txt allowing AI crawlers, llms.txt, sitemap.xml, visible date.
"""
import csv, shutil, html, json, datetime, pathlib

# --- one thing to change: your real domain + TLD -----------------------------
DOMAIN = "https://internunion.eu"          # ponytail: single source of truth for all URLs
# -----------------------------------------------------------------------------
ROOM_RENT_EUR = 509                        # market-wide shared room, Brussels (Brukot/Federia 2025)
LIVABLE_FLOOR_EUR = 770                    # rent+utilities+groceries+transport(<25, registered)

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "public"
TODAY = datetime.date.today().isoformat()

rows = list(csv.DictReader(open(ROOT / "data" / "institutions.csv")))
paid = [r for r in rows if r["monthly_stipend_eur"].strip()]
stipends = sorted(float(r["monthly_stipend_eur"]) for r in paid)
median = stipends[len(stipends) // 2]
lo, hi = stipends[0], stipends[-1]
burden = round(ROOM_RENT_EUR / median * 100)
low_end = [r for r in paid if float(r["monthly_stipend_eur"]) <= 1100]
brussels = [r for r in rows if r["city"] == "Brussels"]

def esc(s): return html.escape(s or "")

# --- structured data (JSON-LD @graph) ----------------------------------------
graph = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Dataset", "@id": f"{DOMAIN}/#dataset",
            "name": "Internships in Brussels: who hosts them, who pays, and affordability",
            "description": ("Open dataset of organisations in Brussels and the EU that offer "
                            "internships/traineeships, with type, whether the internship is paid, "
                            "monthly stipend in EUR, a response-status field, address and source. "
                            "Includes a housing-affordability index against Brussels rent."),
            "url": DOMAIN + "/", "keywords": ["Brussels", "internships", "traineeships", "EU",
            "stipend", "housing", "cost of living", "open data", "labour rights"],
            "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True,
            "creator": {"@id": f"{DOMAIN}/#org"}, "dateModified": TODAY, "version": TODAY,
            "spatialCoverage": {"@type": "Place", "name": "Brussels-Capital Region, Belgium"},
            "distribution": [{"@type": "DataDownload", "name": "institutions.csv",
                "contentUrl": f"{DOMAIN}/institutions.csv", "encodingFormat": "text/csv"}],
        },
        {"@type": "Organization", "@id": f"{DOMAIN}/#org", "name": "internunion", "url": DOMAIN + "/",
         "description": "Open data on internships in Brussels and across the EU.",
         "sameAs": ["https://github.com/Milziade21/internunion"]},
        {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": DOMAIN + "/", "name": "internunion",
         "publisher": {"@id": f"{DOMAIN}/#org"}, "inLanguage": "en"},
        {"@type": "ItemList", "@id": f"{DOMAIN}/#directory",
         "name": "Brussels internship providers", "numberOfItems": len(brussels),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {
             "@type": "Organization", "name": r["name"],
             "address": {"@type": "PostalAddress", "streetAddress": r["address"],
                         "addressLocality": "Brussels", "addressCountry": "BE"}}}
             for i, r in enumerate(brussels)]},
        {"@type": "FAQPage", "@id": f"{DOMAIN}/#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in [
                ("What is internunion?",
                 "internunion is a self-funded open-data project mapping internships and "
                 "traineeships in Brussels and the EU: who hosts them, who pays, and whether an "
                 "intern can afford to live in the city."),
                ("How much are interns paid in Brussels?",
                 f"In this sample of {len(paid)} paid internships the median monthly stipend is "
                 f"about EUR {median:.0f}, ranging from EUR {lo:.0f} to EUR {hi:.0f}."),
                ("Can an intern afford to live in Brussels on a stipend?",
                 f"A single room in a shared Brussels flat costs about EUR {ROOM_RENT_EUR}/month, "
                 f"{burden}% of the median stipend. At the low end (EUR {lo:.0f}-1100) interns are "
                 f"left with little after the ~EUR {LIVABLE_FLOOR_EUR}/month minimum cost of living."),
                ("How is the data collected and verified?",
                 "Compiled from public sources (EU Transparency Register, EU Whoiswho, official "
                 "traineeship portals). Each row carries a response-status: 'classified' (research, "
                 "unverified), 'answered', or 'not answered'. Missing data is shown, never invented."),
                ("What licence applies?",
                 "The data is licensed CC BY 4.0; reuse it freely with attribution to internunion."),
            ]]},
    ],
}

# --- rows -> table -----------------------------------------------------------
def stipend_cell(r):
    s = r["monthly_stipend_eur"].strip()
    return f"&euro;{float(s):.0f}" if s else "&mdash;"

status_label = {"classified": "unverified", "answered": "answered", "not answered": "no reply"}
table_rows = "\n".join(
    f'<tr><td>{esc(r["name"])}</td><td>{esc(r["type"])}</td><td>{esc(r["city"])}</td>'
    f'<td>{esc(r["paid"])}</td><td class="num">{stipend_cell(r)}</td>'
    f'<td><span class="st st-{r["response_status"].split()[0]}">{status_label[r["response_status"]]}</span></td>'
    f'<td><a href="{esc(r["source_url"])}" rel="nofollow">source</a></td></tr>'
    for r in sorted(rows, key=lambda r: (r["city"] != "Brussels", r["name"]))
)

index_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Internships in Brussels: who pays, and can you afford to live here? | internunion</title>
<meta name="description" content="Open data on {len(rows)} organisations in Brussels and the EU offering internships: who pays, how much, and whether an intern can afford Brussels rent. Median stipend ~&euro;{median:.0f}/month; a shared room is {burden}% of it.">
<link rel="canonical" href="{DOMAIN}/">
<meta property="og:type" content="website">
<meta property="og:title" content="Internships in Brussels: who pays, and can you afford to live here?">
<meta property="og:description" content="Open data: who hosts internships in Brussels, who pays, and whether interns can afford to live here.">
<meta property="og:url" content="{DOMAIN}/">
<script type="application/ld+json">
{json.dumps(graph, ensure_ascii=False, indent=1)}
</script>
<style>
  :root {{ --ink:#1a1a1a; --mut:#666; --line:#e2e2e2; --accent:#0b5; --bg:#fff; }}
  * {{ box-sizing:border-box; }}
  body {{ font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; color:var(--ink);
         background:var(--bg); margin:0; }}
  main {{ max-width:920px; margin:0 auto; padding:2rem 1.1rem 4rem; }}
  h1 {{ font-size:1.9rem; line-height:1.2; margin:.2rem 0 1rem; }}
  h2 {{ font-size:1.25rem; margin:2.4rem 0 .6rem; }}
  .tldr {{ font-size:1.08rem; color:#333; }}
  .stat {{ display:flex; flex-wrap:wrap; gap:1.2rem; margin:1.4rem 0; }}
  .stat div {{ flex:1 1 200px; border:1px solid var(--line); border-radius:10px; padding:1rem 1.1rem; }}
  .stat b {{ display:block; font-size:2rem; line-height:1.1; }}
  .stat span {{ color:var(--mut); font-size:.9rem; }}
  .scroll {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; font-size:.92rem; }}
  th,td {{ text-align:left; padding:.5rem .6rem; border-bottom:1px solid var(--line); white-space:nowrap; }}
  td.num {{ text-align:right; }}
  th {{ position:sticky; top:0; background:var(--bg); border-bottom:2px solid var(--ink); }}
  .st {{ font-size:.78rem; padding:.1rem .45rem; border-radius:20px; }}
  .st-classified {{ background:#eee; color:#555; }}
  .st-answered {{ background:#dff3e6; color:#0a5; }}
  .st-not {{ background:#fde8e8; color:#c33; }}
  .box {{ background:#fafafa; border:1px solid var(--line); border-radius:10px; padding:1rem 1.2rem; }}
  a {{ color:#06c; }}
  footer {{ color:var(--mut); font-size:.85rem; margin-top:3rem; border-top:1px solid var(--line); padding-top:1rem; }}
  details {{ margin:.5rem 0; }}
  summary {{ cursor:pointer; font-weight:600; }}
</style>
</head>
<body>
<main>
  <h1>Internships in Brussels: who pays, and can you afford to live here?</h1>
  <p class="tldr"><strong>internunion</strong> is open data on {len(rows)} organisations in Brussels
  and across the EU that host interns &mdash; whether the internship is paid, the monthly stipend,
  and how far that goes against the real cost of living. The median stipend in this sample is about
  <strong>&euro;{median:.0f}/month</strong>; a single room in a shared Brussels flat costs
  ~&euro;{ROOM_RENT_EUR}, or <strong>{burden}% of it</strong> &mdash; before food, transport and utilities.</p>

  <div class="stat">
    <div><b>&euro;{median:.0f}</b><span>median monthly stipend ({len(paid)} paid roles)</span></div>
    <div><b>{burden}%</b><span>of the median stipend goes to one room's rent</span></div>
    <div><b>&euro;{lo:.0f}&ndash;{hi:.0f}</b><span>stipend range across the sample</span></div>
  </div>
  <p>At the low end (&euro;{lo:.0f}&ndash;1100/month &mdash; {", ".join(esc(r["name"]) for r in low_end[:4])}
  and others) an intern is left with little to nothing after the ~&euro;{LIVABLE_FLOOR_EUR}/month
  minimum cost of living &mdash; while doing real work, often with sensitive documents.</p>

  <h2>The directory</h2>
  <div class="scroll">
  <table>
    <thead><tr><th>Organisation</th><th>Type</th><th>City</th><th>Paid</th>
    <th class="num">Stipend/mo</th><th>Status</th><th>Source</th></tr></thead>
    <tbody>
    {table_rows}
    </tbody>
  </table>
  </div>
  <p><a href="/institutions.csv">Download the full dataset (CSV, CC BY 4.0)</a> &middot;
  <a href="https://github.com/Milziade21/internunion">Source & contributions on GitHub</a></p>

  <h2>Method</h2>
  <div class="box">
    <p>Compiled from public sources: the EU Transparency Register, EU Whoiswho and official
    traineeship portals. Every figure is traceable to its <em>source</em> link.</p>
    <p>Each row carries a <strong>response status</strong>: <span class="st st-classified">unverified</span>
    means compiled from research and not yet confirmed; <span class="st st-answered">answered</span> means
    the organisation replied to our standardised questionnaire; <span class="st st-not">no reply</span> means
    it was contacted and did not answer. <strong>Missing data is shown, never invented.</strong></p>
  </div>

  <h2>Questions</h2>
  <details><summary>How much are interns paid in Brussels?</summary>
    <p>In this sample of {len(paid)} paid internships the median monthly stipend is about
    &euro;{median:.0f}, ranging from &euro;{lo:.0f} to &euro;{hi:.0f}.</p></details>
  <details><summary>Can an intern afford to live in Brussels on a stipend?</summary>
    <p>A single room in a shared flat costs about &euro;{ROOM_RENT_EUR}/month, {burden}% of the
    median stipend. The minimum monthly cost of living is around &euro;{LIVABLE_FLOOR_EUR}
    (room, utilities, groceries, subsidised transport), so the lowest stipends leave almost nothing.</p></details>
  <details><summary>What licence applies?</summary>
    <p>Data is CC BY 4.0 &mdash; reuse it freely with attribution to internunion.</p></details>

  <footer>
    <p>Last updated: {TODAY} &middot; Data licensed
    <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> &middot;
    Self-funded, community-driven. Figures marked <em>unverified</em> are provisional until their
    source is confirmed.</p>
  </footer>
</main>
</body>
</html>
"""

robots_txt = """# internunion robots.txt -- open data, allow search and AI answer engines
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: GPTBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: Googlebot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Bingbot
Allow: /
User-agent: *
Allow: /

Sitemap: %s/sitemap.xml
""" % DOMAIN

llms_txt = f"""# internunion

> Open data on internships and traineeships in Brussels and across the EU: which organisations
> host interns, whether the internship is paid, the monthly stipend in EUR, and whether an intern
> can afford to live in Brussels. Self-funded, CC BY 4.0. Last updated {TODAY}.

Key facts: median monthly stipend in the sample ~EUR {median:.0f}; a single room in a shared
Brussels flat ~EUR {ROOM_RENT_EUR}/month ({burden}% of the median stipend); minimum monthly cost
of living ~EUR {LIVABLE_FLOOR_EUR}. Each record has a response-status (unverified / answered /
no reply); missing data is shown, never imputed.

## Data
- [Directory + housing index]({DOMAIN}/): the main page, {len(rows)} organisations with pay and status
- [institutions.csv]({DOMAIN}/institutions.csv): the full dataset (CSV)

## Optional
- [Source & method](https://github.com/Milziade21/internunion): repository, methodology, contributions
"""

sitemap_xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f'  <url><loc>{DOMAIN}/</loc><lastmod>{TODAY}</lastmod></url>\n'
    f'</urlset>\n')

# --- write output ------------------------------------------------------------
OUT.mkdir(exist_ok=True)
(OUT / "index.html").write_text(index_html, encoding="utf-8")
(OUT / "robots.txt").write_text(robots_txt, encoding="utf-8")
(OUT / "llms.txt").write_text(llms_txt, encoding="utf-8")
(OUT / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
shutil.copyfile(ROOT / "data" / "institutions.csv", OUT / "institutions.csv")

# --- one runnable check ------------------------------------------------------
out = (OUT / "index.html").read_text(encoding="utf-8")
assert '"@type": "Dataset"' in out, "Dataset JSON-LD missing"
assert out.count("<tr>") == len(rows) + 1, "table row count != data rows (+header)"
assert f"{burden}%" in out, "headline stat not rendered"
json.loads(out.split('application/ld+json">', 1)[1].split("</script>", 1)[0])  # JSON-LD parses
print(f"built public/  ({len(rows)} rows, median EUR {median:.0f}, rent burden {burden}%)")
print("files: index.html robots.txt llms.txt sitemap.xml institutions.csv")
