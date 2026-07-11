#!/usr/bin/env python3
"""Generate the internunion static site. Zero dependencies (stdlib only).

Output -> public/. Deploy that folder on any static host (Railway serves it via the
Dockerfile). Run: python3 build.py

Homepage: a Europe choropleth (intern pay vs cost of living, projected from
assets/europe.geojson with no mapping library) + city coverage pins, then the
Brussels directory, then a submit CTA. Discoverability baked in: schema.org
Dataset/Organization/WebSite/FAQPage JSON-LD, robots.txt for AI crawlers,
llms.txt, sitemap.xml.
"""
import csv, shutil, html, json, math, datetime, pathlib

# --- one thing to change: your real domain + TLD -----------------------------
DOMAIN = "https://internunion.com"         # ponytail: single source of truth for all URLs
# -----------------------------------------------------------------------------
ROOM_RENT_EUR = 509                        # market-wide shared room, Brussels (Brukot/Federia 2025)
LIVABLE_FLOOR_EUR = 770                    # rent+utilities+groceries+transport(<25, registered)
SUBMIT_FORM_URL = "#submit"                # ponytail: swap for a Tally/Google Form URL when live

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "public"
TODAY = datetime.date.today().isoformat()

def esc(s): return html.escape(s or "")
def num(s):
    s = (s or "").strip()
    return float(s) if s else None

# ============================================================ data
inst = list(csv.DictReader(open(ROOT / "data" / "institutions.csv")))
paid = [r for r in inst if r["monthly_stipend_eur"].strip()]
stipends = sorted(float(r["monthly_stipend_eur"]) for r in paid)
median = stipends[len(stipends) // 2]
lo, hi = stipends[0], stipends[-1]
burden = round(ROOM_RENT_EUR / median * 100)
low_end = [r for r in paid if float(r["monthly_stipend_eur"]) <= 1100]
brussels = [r for r in inst if r["city"] == "Brussels"]

countries = list(csv.DictReader(open(ROOT / "data" / "countries.csv")))
cmap = {c["iso2"]: c for c in countries}
with_ratio = [c for c in countries if num(c["ratio"]) is not None]
no_floor = [c for c in countries if num(c["ratio"]) is None]          # unregulated / no pay floor
below_one = [c for c in with_ratio if num(c["ratio"]) < 1]            # pay < one room's rent

# ============================================================ map projection
# Mercator, clipped to a European window. Same projection for country paths and city pins,
# so pins land in the right place. No mapping library, no tiles.
LON0, LON1, LAT0, LAT1 = -11.0, 34.0, 34.5, 60.8   # window trimmed to where EU-27 capitals sit
W = 1000.0
def _my(lat): return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
SX0, SX1 = math.radians(LON0), math.radians(LON1)
SY0, SY1 = _my(LAT1), _my(LAT0)           # top, bottom (screen y grows downward)
SCALE = W / (SX1 - SX0)
H = SCALE * (SY0 - SY1)
def project(lon, lat):
    return ((math.radians(lon) - SX0) * SCALE, (SY0 - _my(lat)) * SCALE)

def ratio_color(c):
    r = num(c["ratio"])
    if r is None: return None             # no floor -> hatched grey, handled separately
    if r >= 1.5: return "#1a7a3a"
    if r >= 1.0: return "#6bbf59"
    if r >= 0.75: return "#f0a33a"
    return "#d1495b"

geo = json.load(open(ROOT / "assets" / "europe.geojson"))
paths = []
bb = [1e9, 1e9, -1e9, -1e9]               # content bounds [minx,miny,maxx,maxy] over EU shapes + pins
def grow(x, y):
    bb[0] = min(bb[0], x); bb[1] = min(bb[1], y); bb[2] = max(bb[2], x); bb[3] = max(bb[3], y)
for f in geo["features"]:
    iso = f["properties"].get("ISO2")
    lon_c, lat_c = f["properties"].get("LON", 0), f["properties"].get("LAT", 0)
    if not (-30 < lon_c < 45 and 32 < lat_c < 75):   # skip features outside the window
        continue
    polys = f["geometry"]["coordinates"]
    if f["geometry"]["type"] == "Polygon": polys = [polys]
    d = []
    for poly in polys:
        for ring in poly:
            pts, last = [], None
            for lon, lat in ring:
                x, y = project(lon, lat)
                p = (round(x), round(y))
                if p != last: pts.append(p); last = p
            if len(pts) < 3: continue
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if (max(xs) - min(xs)) * (max(ys) - min(ys)) < 6: continue   # drop tiny islands
            d.append("M" + " ".join(f"{x},{y}" for x, y in pts) + "Z")
    if not d: continue
    c = cmap.get(iso)
    if c:                                  # an EU-27 country we have data for
        for poly in polys:                 # grow content bounds over this country's in-window points
            for ring in poly:
                for lon, lat in ring:
                    if LON0 <= lon <= LON1 and LAT0 <= lat <= LAT1:
                        grow(*project(lon, lat))
        col = ratio_color(c)
        fill = col if col else "url(#nofloor)"
        r = num(c["ratio"])
        tip = (f'{c["country"]} - {c["capital"]}. '
               + (f'Intern pay EUR {num(c["intern_pay_eur"]):.0f}/mo vs room rent EUR '
                  f'{num(c["room_rent_eur"]):.0f} (ratio {r:.2f}). ' if r is not None
                  else f'No legal pay floor; room rent EUR {num(c["room_rent_eur"]):.0f}/mo. ')
               + ("Unpaid internships are legal here." if c["unpaid_legal"] == "yes"
                  else "Interns must be paid." if c["unpaid_legal"] == "no"
                  else "Regulated schemes are paid."))
        paths.append(f'<path d="{"".join(d)}" fill="{fill}" stroke="#fff" stroke-width="0.7" '
                     f'data-tip="{esc(tip)}" tabindex="0"><title>{esc(tip)}</title></path>')
    else:                                  # non-EU context country
        paths.append(f'<path d="{"".join(d)}" fill="#eaeaea" stroke="#fff" stroke-width="0.6"/>')

CITIES = [("Brussels", 50.85, 4.35, "live"), ("Luxembourg", 49.61, 6.13, "soon"),
          ("Strasbourg", 48.58, 7.75, "soon"), ("Paris", 48.85, 2.35, "soon"),
          ("Amsterdam", 52.37, 4.90, "soon"), ("Frankfurt", 50.11, 8.68, "soon"),
          ("Vienna", 48.21, 16.37, "soon"), ("Madrid", 40.42, -3.70, "soon")]
pins = []
for name, lat, lon, status in CITIES:
    x, y = project(lon, lat)
    grow(x, y)
    if status == "live":
        pins.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#0b5" stroke="#fff" stroke-width="2"/>'
                    f'<circle cx="{x:.0f}" cy="{y:.0f}" r="13" fill="none" stroke="#0b5" stroke-width="1.5" opacity=".5"/>'
                    f'<text x="{x+16:.0f}" y="{y+4:.0f}" class="pin-live">{esc(name)} - live</text>')
    else:
        pins.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="#fff" stroke="#888" stroke-width="1.6"/>'
                    f'<text x="{x+10:.0f}" y="{y+4:.0f}" class="pin-soon">{esc(name)}</text>')

# crop viewBox to content: pad left/top/bottom, extra on the right for city labels
vx, vy = bb[0] - 12, bb[1] - 12
vw, vh = (bb[2] - bb[0]) + 100, (bb[3] - bb[1]) + 24
svg_map = f'''<svg viewBox="{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}" class="map" role="img"
  aria-label="Map of Europe shaded by internship pay relative to the cost of a room in the capital.">
  <defs><pattern id="nofloor" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="6" height="6" fill="#cfcfcf"/><line x1="0" y1="0" x2="0" y2="6" stroke="#a9a9a9" stroke-width="2"/>
  </pattern></defs>
  {"".join(paths)}
  {"".join(pins)}
</svg>'''

# ============================================================ tables
def country_rows():
    ordered = sorted(with_ratio, key=lambda c: -num(c["ratio"])) + \
              sorted(no_floor, key=lambda c: num(c["room_rent_eur"]) or 0)
    out = []
    for c in ordered:
        r = num(c["ratio"])
        if r is not None:
            col = ratio_color(c)
            pay = f'&euro;{num(c["intern_pay_eur"]):.0f}'
            ratio_cell = f'<b style="color:{col}">{r:.2f}</b>'
        else:
            pay = '<span class="nf">no floor</span>'
            ratio_cell = '<span class="nf">&mdash;</span>'
        legal = {"yes": "unpaid legal", "no": "must pay", "partial": "regulated pay"}[c["unpaid_legal"]]
        out.append(f'<tr><td>{esc(c["country"])}</td><td>{esc(c["capital"])}</td>'
                   f'<td class="num">{pay}</td><td class="num">&euro;{num(c["room_rent_eur"]):.0f}</td>'
                   f'<td class="num">{ratio_cell}</td><td>{legal}</td>'
                   f'<td class="ln">{esc(c["legal_note"])}</td></tr>')
    return "\n".join(out)

status_label = {"classified": "unverified", "answered": "answered", "not answered": "no reply"}
def inst_rows():
    def stipend(r):
        s = r["monthly_stipend_eur"].strip()
        return f"&euro;{float(s):.0f}" if s else "&mdash;"
    return "\n".join(
        f'<tr><td>{esc(r["name"])}</td><td>{esc(r["type"])}</td><td>{esc(r["city"])}</td>'
        f'<td>{esc(r["paid"])}</td><td class="num">{stipend(r)}</td>'
        f'<td><span class="st st-{r["response_status"].split()[0]}">{status_label[r["response_status"]]}</span></td>'
        f'<td><a href="{esc(r["source_url"])}" rel="nofollow">source</a></td></tr>'
        for r in sorted(inst, key=lambda r: (r["city"] != "Brussels", r["name"])))

# ============================================================ structured data
graph = {"@context": "https://schema.org", "@graph": [
    {"@type": "Dataset", "@id": f"{DOMAIN}/#countries",
     "name": "EU-27 internship pay vs cost of living",
     "description": ("Intern pay, capital-city room rent, affordability ratio, minimum wage and the "
                     "legal status of unpaid internships for all 27 EU member states."),
     "url": DOMAIN + "/", "license": "https://creativecommons.org/licenses/by/4.0/",
     "isAccessibleForFree": True, "creator": {"@id": f"{DOMAIN}/#org"}, "dateModified": TODAY,
     "spatialCoverage": {"@type": "Place", "name": "European Union"},
     "distribution": [{"@type": "DataDownload", "name": "countries.csv",
                       "contentUrl": f"{DOMAIN}/countries.csv", "encodingFormat": "text/csv"}]},
    {"@type": "Dataset", "@id": f"{DOMAIN}/#institutions",
     "name": "Brussels internship providers",
     "description": ("Organisations in Brussels that host interns, with type, whether the internship "
                     "is paid, monthly stipend, a response-status field, address and source."),
     "url": DOMAIN + "/#brussels", "license": "https://creativecommons.org/licenses/by/4.0/",
     "isAccessibleForFree": True, "creator": {"@id": f"{DOMAIN}/#org"}, "dateModified": TODAY,
     "spatialCoverage": {"@type": "Place", "name": "Brussels-Capital Region, Belgium"},
     "distribution": [{"@type": "DataDownload", "name": "institutions.csv",
                       "contentUrl": f"{DOMAIN}/institutions.csv", "encodingFormat": "text/csv"}]},
    {"@type": "Organization", "@id": f"{DOMAIN}/#org", "name": "internunion", "url": DOMAIN + "/",
     "description": "Open data on internships in Brussels and across the EU.",
     "sameAs": ["https://github.com/Milziade21/internunion"]},
    {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": DOMAIN + "/", "name": "internunion",
     "publisher": {"@id": f"{DOMAIN}/#org"}, "inLanguage": "en"},
    {"@type": "FAQPage", "@id": f"{DOMAIN}/#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in [
            ("Which EU countries let interns be unpaid?",
             f"{len(no_floor)} of 27 EU member states have no legal pay floor for open-market interns. "
             "In 5 of the countries that do regulate pay, the stipend still does not cover one room's rent."),
            ("Where are interns best protected in the EU?",
             "Latvia and Czechia protect interns most: they refuse to treat 'traineeship' as a low-wage "
             "status, so any real work triggers the full minimum wage. Latvia's intern pay covers 2.6x a room."),
            ("How much are interns paid in Brussels?",
             f"In our Brussels sample of {len(paid)} paid internships the median stipend is about EUR "
             f"{median:.0f}/month, ranging from EUR {lo:.0f} to EUR {hi:.0f}. A shared room is ~{burden}% of the median."),
            ("What licence applies?",
             "The data is CC BY 4.0; reuse it freely with attribution to internunion."),
        ]]},
]}

# ============================================================ page
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Can interns afford Europe? Pay vs cost of living, EU-wide | internunion</title>
<meta name="description" content="An open map of internship pay against the cost of living across the EU-27, and the full Brussels directory. {len(no_floor)} of 27 EU countries have no legal pay floor for interns.">
<link rel="canonical" href="{DOMAIN}/">
<meta property="og:type" content="website">
<meta property="og:title" content="Can interns afford Europe?">
<meta property="og:description" content="Open map: internship pay vs cost of living across the EU, plus the full Brussels directory.">
<meta property="og:url" content="{DOMAIN}/">
<script type="application/ld+json">
{json.dumps(graph, ensure_ascii=False, indent=1)}
</script>
<style>
  :root {{ --ink:#1a1a1a; --mut:#666; --line:#e2e2e2; --bg:#fff; }}
  * {{ box-sizing:border-box; }}
  body {{ font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; color:var(--ink); background:var(--bg); margin:0; }}
  main {{ max-width:1000px; margin:0 auto; padding:2rem 1.1rem 4rem; }}
  h1 {{ font-size:2rem; line-height:1.15; margin:.2rem 0 1rem; }}
  h2 {{ font-size:1.35rem; margin:2.8rem 0 .6rem; }}
  .tldr {{ font-size:1.08rem; color:#333; max-width:70ch; }}
  .mapwrap {{ position:relative; margin:1.4rem 0 .5rem; }}
  .map {{ width:100%; height:auto; max-height:600px; background:#f7fbff; border:1px solid var(--line); border-radius:12px; display:block; margin:0 auto; }}
  .map path[data-tip] {{ cursor:pointer; transition:opacity .1s; }}
  .map path[data-tip]:hover, .map path[data-tip]:focus {{ opacity:.8; outline:none; }}
  .pin-live {{ font:600 13px system-ui; fill:#083; }}
  .pin-soon {{ font:12px system-ui; fill:#555; }}
  #tip {{ position:fixed; z-index:9; max-width:280px; background:#111; color:#fff; font-size:.82rem;
         padding:.5rem .7rem; border-radius:7px; pointer-events:none; opacity:0; transition:opacity .1s; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:.4rem 1.1rem; font-size:.82rem; color:var(--mut); margin:.4rem 0 0; }}
  .legend span {{ display:inline-flex; align-items:center; gap:.35rem; }}
  .sw {{ width:14px; height:14px; border-radius:3px; display:inline-block; }}
  .stat {{ display:flex; flex-wrap:wrap; gap:1.1rem; margin:1.4rem 0; }}
  .stat div {{ flex:1 1 210px; border:1px solid var(--line); border-radius:10px; padding:1rem 1.1rem; }}
  .stat b {{ display:block; font-size:2rem; line-height:1.1; }}
  .stat span {{ color:var(--mut); font-size:.9rem; }}
  .scroll {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; font-size:.9rem; }}
  th,td {{ text-align:left; padding:.5rem .6rem; border-bottom:1px solid var(--line); vertical-align:top; }}
  td.num, th.num {{ text-align:right; white-space:nowrap; }}
  th {{ background:var(--bg); border-bottom:2px solid var(--ink); white-space:nowrap; }}
  .ln {{ color:var(--mut); font-size:.82rem; min-width:240px; }}
  .nf {{ color:#a33; }}
  .st {{ font-size:.78rem; padding:.1rem .45rem; border-radius:20px; white-space:nowrap; }}
  .st-classified {{ background:#eee; color:#555; }} .st-answered {{ background:#dff3e6; color:#0a5; }}
  .st-not {{ background:#fde8e8; color:#c33; }}
  .box {{ background:#fafafa; border:1px solid var(--line); border-radius:10px; padding:1rem 1.2rem; }}
  .cta {{ background:#f2f8f4; border:1px solid #cfe8d8; border-radius:12px; padding:1.4rem 1.4rem; margin:1rem 0; }}
  .btn {{ display:inline-block; background:#0b5; color:#fff; text-decoration:none; padding:.6rem 1.1rem; border-radius:8px; font-weight:600; margin-top:.6rem; }}
  a {{ color:#06c; }}
  footer {{ color:var(--mut); font-size:.85rem; margin-top:3rem; border-top:1px solid var(--line); padding-top:1rem; }}
  details {{ margin:.5rem 0; }} summary {{ cursor:pointer; font-weight:600; }}
</style>
</head>
<body>
<main>
  <h1>Can an intern afford to live in Europe?</h1>
  <p class="tldr"><strong>internunion</strong> maps what interns are paid against what it costs to live,
  starting with Brussels and expanding across the EU. Internship pay is set country by country, not by the
  Union &mdash; so the gap is enormous. <strong>{len(no_floor)} of 27 EU countries have no legal pay floor
  for interns at all.</strong> Where pay is regulated, it ranges from covering 2.6&times; a room in Riga to
  just 40% of one in Amsterdam.</p>

  <div class="mapwrap">
    {svg_map}
  </div>
  <div class="legend">
    <span><i class="sw" style="background:#1a7a3a"></i> pay &ge; 1.5&times; rent</span>
    <span><i class="sw" style="background:#6bbf59"></i> covers rent (1&ndash;1.5&times;)</span>
    <span><i class="sw" style="background:#f0a33a"></i> tight (0.75&ndash;1&times;)</span>
    <span><i class="sw" style="background:#d1495b"></i> rent &gt; pay</span>
    <span><i class="sw" style="background:repeating-linear-gradient(45deg,#cfcfcf,#cfcfcf 3px,#a9a9a9 3px,#a9a9a9 5px)"></i> no legal pay floor</span>
    <span><i class="sw" style="background:#0b5"></i> internunion live</span>
    <span><i class="sw" style="border:2px solid #888;background:#fff"></i> coming soon</span>
  </div>
  <p style="color:var(--mut);font-size:.85rem;margin-top:.5rem">Ratio = typical/legally-required monthly
  intern pay &divide; median room rent in the capital. Hover a country for detail. Grey hatching means the
  country sets no statutory pay floor for open-market interns.</p>

  <div class="stat">
    <div><b>{len(no_floor)}/27</b><span>EU countries with no legal intern pay floor</span></div>
    <div><b>{len(below_one)}</b><span>regulated countries where pay still can't cover one room</span></div>
    <div><b>2.6&times; &rarr; 0.4&times;</b><span>best (Latvia) to worst (Netherlands) pay-to-rent ratio</span></div>
  </div>

  <h2>Europe, country by country</h2>
  <div class="scroll">
  <table>
    <thead><tr><th>Country</th><th>Capital</th><th class="num">Intern pay/mo</th>
    <th class="num">Room rent/mo</th><th class="num">Ratio</th><th>Unpaid?</th><th>How it's regulated</th></tr></thead>
    <tbody>
    {country_rows()}
    </tbody>
  </table>
  </div>
  <p><a href="/countries.csv">Download the EU-27 dataset (CSV, CC BY 4.0)</a></p>

  <h2 id="brussels">Brussels &mdash; our first city</h2>
  <p class="tldr">Brussels is where internunion starts. Belgium sets no central pay floor, so the market is
  fragmented: the median stipend here is ~<strong>&euro;{median:.0f}/month</strong> and a single room is
  ~<strong>{burden}% of it</strong>. At the low end (&euro;{lo:.0f}&ndash;1100 &mdash;
  {", ".join(esc(r["name"]) for r in low_end[:3])} and others) little is left after the ~&euro;{LIVABLE_FLOOR_EUR}
  minimum cost of living.</p>
  <div class="scroll">
  <table>
    <thead><tr><th>Organisation</th><th>Type</th><th>City</th><th>Paid</th>
    <th class="num">Stipend/mo</th><th>Status</th><th>Source</th></tr></thead>
    <tbody>
    {inst_rows()}
    </tbody>
  </table>
  </div>
  <p><a href="/institutions.csv">Download the Brussels dataset (CSV)</a> &middot;
  <a href="https://github.com/Milziade21/internunion">Source & contributions on GitHub</a></p>

  <h2 id="submit">Add a place, or tell us your conditions</h2>
  <div class="cta">
    <p>Know a workplace that hosts interns, or interned somewhere yourself? Add it, and tell us what the
    pay and conditions really were. Every submission turns an <em>unverified</em> row into a lived one and
    grows the map beyond Brussels.</p>
    <p><a class="btn" href="{esc(SUBMIT_FORM_URL)}">Submit a place / your experience</a></p>
    <p style="font-size:.82rem;color:var(--mut);margin-bottom:0"><strong>Your privacy:</strong> submissions
    are voluntary and can be anonymous &mdash; no account or login required. We only publish workplace-level
    facts (pay, conditions), never your identity unless you ask. You can request removal at any time. Data
    is processed under GDPR on the basis of your consent.</p>
  </div>

  <h2>Method</h2>
  <div class="box">
    <p>EU-27 figures: European Commission (DG EMPL) traineeship-remuneration study, Eurostat minimum wages,
    and HousingAnywhere / Numbeo rent indices (2026). Brussels rows: EU Transparency Register, EU Whoiswho and
    official traineeship portals. Every Brussels row carries a <strong>response status</strong> &mdash;
    <span class="st st-classified">unverified</span> (from research), <span class="st st-answered">answered</span>
    (organisation replied) or <span class="st st-not">no reply</span>. <strong>Missing data is shown, never invented</strong>
    &mdash; countries with no pay floor are marked as such, not estimated.</p>
  </div>

  <h2>Questions</h2>
  <details><summary>Which EU countries let interns be unpaid?</summary>
    <p>{len(no_floor)} of 27 have no legal pay floor for open-market interns. Of the countries that do
    regulate pay, {len(below_one)} still set it below the cost of a single room in the capital.</p></details>
  <details><summary>Where are interns best protected?</summary>
    <p>Latvia and Czechia: they refuse to treat "traineeship" as a low-wage status, so any real work triggers
    the full minimum wage. Latvia's intern pay covers 2.6&times; a room; Amsterdam's covers 0.4&times;.</p></details>
  <details><summary>What licence applies?</summary>
    <p>Data is CC BY 4.0 &mdash; reuse it freely with attribution to internunion.</p></details>

  <footer>
    <p>Last updated: {TODAY} &middot; Data licensed
    <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> &middot; Self-funded, community-driven.
    Figures marked <em>unverified</em> or <em>no floor</em> are provisional until confirmed at source.</p>
  </footer>
</main>
<div id="tip"></div>
<script>
  var tip = document.getElementById('tip');
  document.querySelectorAll('.map path[data-tip]').forEach(function(p){{
    p.addEventListener('mousemove', function(e){{
      tip.textContent = p.getAttribute('data-tip');
      tip.style.left = Math.min(e.clientX+14, innerWidth-290)+'px';
      tip.style.top = (e.clientY+14)+'px'; tip.style.opacity = 1;
    }});
    p.addEventListener('mouseleave', function(){{ tip.style.opacity = 0; }});
  }});
</script>
</body>
</html>
"""

robots_txt = "".join(f"User-agent: {b}\nAllow: /\n" for b in
    ["OAI-SearchBot","ChatGPT-User","GPTBot","PerplexityBot","Perplexity-User","ClaudeBot",
     "anthropic-ai","Googlebot","Google-Extended","Bingbot","*"]) + f"\nSitemap: {DOMAIN}/sitemap.xml\n"

llms_txt = f"""# internunion

> Open data on internships across the EU: what interns are paid vs what it costs to live, country by
> country, plus the full Brussels directory. Self-funded, CC BY 4.0. Last updated {TODAY}.

Key facts: {len(no_floor)} of 27 EU countries have no legal pay floor for open-market interns. Where pay
is regulated it ranges from covering 2.6x a room (Latvia) to 0.4x (Netherlands). Brussels median stipend
~EUR {median:.0f}/month; a shared room ~EUR {ROOM_RENT_EUR} ({burden}% of the median).

## Data
- [EU-27 pay vs cost of living]({DOMAIN}/): the map and the country table
- [countries.csv]({DOMAIN}/countries.csv): pay, rent, ratio, minimum wage and unpaid-internship legality per country
- [Brussels directory]({DOMAIN}/#brussels): organisations, pay and response status
- [institutions.csv]({DOMAIN}/institutions.csv): the Brussels dataset

## Optional
- [Source & method](https://github.com/Milziade21/internunion): repository, methodology, contributions
"""

sitemap_xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f'  <url><loc>{DOMAIN}/</loc><lastmod>{TODAY}</lastmod></url>\n</urlset>\n')

# ============================================================ write + check
OUT.mkdir(exist_ok=True)
(OUT / "index.html").write_text(page, encoding="utf-8")
(OUT / "robots.txt").write_text(robots_txt, encoding="utf-8")
(OUT / "llms.txt").write_text(llms_txt, encoding="utf-8")
(OUT / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
shutil.copyfile(ROOT / "data" / "institutions.csv", OUT / "institutions.csv")
shutil.copyfile(ROOT / "data" / "countries.csv", OUT / "countries.csv")

out = (OUT / "index.html").read_text(encoding="utf-8")
assert len(countries) == 27, f"expected 27 EU countries, got {len(countries)}"
assert '<svg' in out and out.count("<path") >= 27, "map paths missing"
assert '"@type": "Dataset"' in out, "Dataset JSON-LD missing"
assert out.count("<tr>") == len(inst) + len(countries) + 2, "table row count mismatch"
json.loads(out.split('application/ld+json">', 1)[1].split("</script>", 1)[0])  # JSON-LD parses
print(f"built public/  ({len(countries)} countries, {len(no_floor)} no-floor, {len(paths)} map shapes, "
      f"{len(inst)} Brussels rows, median EUR {median:.0f})")
