#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Generate the internunion static site. Zero dependencies (stdlib only).

Output -> public/. Deploy that folder on any static host (Railway serves it via the
Dockerfile). Run: python3 build.py

Pages: index (Europe affordability map + Brussels directory + response-status ledger),
submit, questionnaire (the instrument, published verbatim), privacy (GDPR), about.
Discoverability baked in: schema.org JSON-LD, robots.txt for AI crawlers, llms.txt, sitemap.xml.
"""
import csv, shutil, html, json, math, datetime, pathlib, re

# --- one thing to change: your real domain + TLD -----------------------------
DOMAIN = "https://internunion.com"         # ponytail: single source of truth for all URLs
# -----------------------------------------------------------------------------
ROOM_RENT_EUR = 509                        # market-wide shared room, Brussels (Brukot/Federia 2025)
LIVABLE_FLOOR_EUR = 770                    # rent+utilities+groceries+transport(<25, registered)
CIP_MIN_EUR = 1095                         # Belgian CIP indexed minimum, full-time gross (Apr 2026)
# --- set these three before launch -------------------------------------------
FORM_ENDPOINT = "https://formspree.io/f/YOUR_FORM_ID"   # Formspree/Tally endpoint for the submit form
CONTACT_EMAIL = "contact@internunion.com"               # GDPR/data-request contact
PATREON_URL   = "https://www.patreon.com/internunion"   # support link
# -----------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "public"
TODAY = datetime.date.today().isoformat()
GH = "https://github.com/Milziade21/internunion"

def esc(s): return html.escape(s or "")
def num(s):
    s = (s or "").strip()
    return float(s) if s else None

# ponytail: tiny markdown SUBSET for blog posts (headings, para, bold/italic/code, links, lists,
# blockquote, hr). Author controls the input, so a subset is safe. Upgrade to python-markdown if
# posts ever need tables/footnotes/nested lists.
def md_inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md_to_html(text):
    out, lines, i, n = [], text.split("\n"), 0, len(text.split("\n"))
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1; continue
        h = re.match(r"^(#{1,3})\s+(.*)", line)
        if h:
            lvl = len(h.group(1)) + 1
            out.append(f"<h{lvl}>{md_inline(h.group(2))}</h{lvl}>"); i += 1; continue
        if re.match(r"^---+\s*$", line):
            out.append("<hr>"); i += 1; continue
        if re.match(r"^>\s", line):
            buf = []
            while i < n and re.match(r"^>\s?", lines[i]):
                buf.append(re.sub(r"^>\s?", "", lines[i])); i += 1
            out.append("<blockquote>" + " ".join(md_inline(b) for b in buf) + "</blockquote>"); continue
        for pat, tag in ((r"^[-*]\s+", "ul"), (r"^\d+\.\s+", "ol")):
            if re.match(pat, line):
                items = []
                while i < n and re.match(pat, lines[i]):
                    items.append(re.sub(pat, "", lines[i])); i += 1
                out.append(f"<{tag}>" + "".join(f"<li>{md_inline(x)}</li>" for x in items) + f"</{tag}>")
                break
        else:
            buf = []
            while i < n and lines[i].strip() and not re.match(r"^(#{1,3}\s|>\s|[-*]\s|\d+\.\s|---+\s*$)", lines[i]):
                buf.append(lines[i]); i += 1
            out.append("<p>" + md_inline(" ".join(buf)) + "</p>")
    return "\n".join(out)

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

vx, vy = bb[0] - 12, bb[1] - 12            # crop viewBox to content (extra right pad for city labels)
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
            pay = f'&euro;{num(c["intern_pay_eur"]):.0f}'
            ratio_cell = f'<b style="color:{ratio_color(c)}">{r:.2f}</b>'
        else:
            pay = '<span class="nf">no floor</span>'
            ratio_cell = '<span class="nf">&mdash;</span>'
        legal = {"yes": "unpaid legal", "no": "must pay", "partial": "regulated pay"}[c["unpaid_legal"]]
        out.append(f'<tr><td>{esc(c["country"])}</td><td>{esc(c["capital"])}</td>'
                   f'<td class="num">{pay}</td><td class="num">&euro;{num(c["room_rent_eur"]):.0f}</td>'
                   f'<td class="num">{ratio_cell}</td><td>{legal}</td>'
                   f'<td class="ln">{esc(c["legal_note"])}</td></tr>')
    return "\n".join(out)

# Response-status ledger vocabulary (label, css class). classified = not yet contacted.
STATUS = {
    "classified": ("unverified", "st-classified"),
    "pending":    ("response pending", "st-pending"),
    "verified":   ("verified compliant", "st-verified"),
    "disclosed":  ("disclosed sub-standard", "st-disclosed"),
    "refused":    ("did not disclose", "st-refused"),
    "answered": ("verified compliant", "st-verified"),          # legacy aliases
    "not answered": ("did not disclose", "st-refused"),
}
def inst_rows():
    def stipend(r):
        s = r["monthly_stipend_eur"].strip()
        return f"&euro;{float(s):.0f}" if s else "&mdash;"
    out = []
    for r in sorted(inst, key=lambda r: (r["city"] != "Brussels", r["name"])):
        label, cls = STATUS[r["response_status"]]
        out.append(
            f'<tr><td>{esc(r["name"])}</td><td>{esc(r["type"])}</td><td>{esc(r["city"])}</td>'
            f'<td>{esc(r["paid"])}</td><td class="num">{stipend(r)}</td>'
            f'<td><span class="st {cls}">{label}</span></td>'
            f'<td><a href="{esc(r["source_url"])}" rel="nofollow">source</a></td></tr>')
    return "\n".join(out)

# ============================================================ Brussels city data (Leaflet)
# The city map is Leaflet + OpenStreetMap tiles (real roads). Markers and filtering are client-side
# (see CITY_JS) -- no database on the server. Curated orgs are precisely geocoded pins; register
# orgs are postcode-level (loc=approx), shown behind a toggle and never as false street pins.
# category -> colour (EU institutions blue), shared by the map and the legend
CATCOLOR = {"EU institution": "#1d6fb8", "EU agency": "#1d6fb8", "NGO": "#2e9e5b",
    "think tank": "#7e57c2", "consultancy": "#ef8a34", "trade association": "#159a9a",
    "trade union": "#159a9a", "law firm": "#8d6e63", "company": "#64748b", "academic": "#d6559b",
    "public/mixed": "#546e7a", "public authority": "#546e7a", "foundation": "#5c6bc0",
    "media": "#e05252", "religious": "#9e9e9e", "other": "#9e9e9e"}
blist = sorted(brussels, key=lambda r: r["name"])
orgs_json = []
for i, r in enumerate(blist):
    s = r["monthly_stipend_eur"].strip()
    orgs_json.append({"i": i, "name": r["name"], "type": r["type"], "paid": r["paid"],
                      "status": r["response_status"], "loc": r.get("loc", "exact"),
                      "url": r["source_url"], "pay": (f"{float(s):.0f}" if s else ""),
                      "lat": (float(r["lat"]) if r["lat"] else None),
                      "lon": (float(r["lon"]) if r["lon"] else None)})
n_mapped = sum(1 for o in orgs_json if o["lat"] is not None)
n_precise = sum(1 for o in orgs_json if o["lat"] is not None and o["loc"] != "approx")

def city_list_rows():
    out = []
    for i, r in enumerate(blist):
        label, cls = STATUS[r["response_status"]]
        s = r["monthly_stipend_eur"].strip()
        pay = f'&euro;{float(s):.0f}' if s else '&mdash;'
        out.append(f'<tr data-i="{i}"><td>{esc(r["name"])}</td><td>{esc(r["type"])}</td>'
                   f'<td>{esc(r["paid"])}</td><td class="num">{pay}</td>'
                   f'<td><span class="st {cls}">{label}</span></td>'
                   f'<td><a href="{esc(r["source_url"])}" rel="nofollow">source</a></td></tr>')
    return "\n".join(out)

SECTORS = sorted(set(r["type"] for r in blist))
CAT_LEGEND = "".join(
    f'<span><i class="sw" style="background:{CATCOLOR.get(s, "#9e9e9e")};border-radius:50%"></i>{esc(s)}</span>'
    for s in SECTORS)

# ============================================================ structured data (index only)
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
     "url": DOMAIN + "/city.html", "license": "https://creativecommons.org/licenses/by/4.0/",
     "isAccessibleForFree": True, "creator": {"@id": f"{DOMAIN}/#org"}, "dateModified": TODAY,
     "spatialCoverage": {"@type": "Place", "name": "Brussels-Capital Region, Belgium"},
     "distribution": [{"@type": "DataDownload", "name": "institutions.csv",
                       "contentUrl": f"{DOMAIN}/institutions.csv", "encodingFormat": "text/csv"}]},
    {"@type": "Organization", "@id": f"{DOMAIN}/#org", "name": "internunion", "url": DOMAIN + "/",
     "description": "Open data on internships in Brussels and across the EU.", "sameAs": [GH]},
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

# ============================================================ shared shell
CSS = """
  :root { --ink:#1a1a1a; --mut:#666; --line:#e2e2e2; --bg:#fff; }
  * { box-sizing:border-box; }
  body { font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; color:var(--ink); background:var(--bg); margin:0; }
  .nav { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:.4rem 1rem;
         max-width:1000px; margin:0 auto; padding:1rem 1.1rem .4rem; }
  .brand { font-weight:700; font-size:1.15rem; color:var(--ink); text-decoration:none; }
  .nav nav { display:flex; flex-wrap:wrap; gap:.2rem 1rem; font-size:.92rem; }
  .nav nav a { color:#06c; text-decoration:none; }
  main { max-width:1000px; margin:0 auto; padding:1rem 1.1rem 2rem; }
  h1 { font-size:2rem; line-height:1.15; margin:.4rem 0 1rem; }
  h2 { font-size:1.35rem; margin:2.4rem 0 .6rem; }
  h3 { font-size:1.05rem; margin:1.4rem 0 .3rem; }
  .tldr { font-size:1.08rem; color:#333; max-width:70ch; }
  p, li { max-width:72ch; }
  .mapwrap { position:relative; margin:1.4rem 0 .5rem; }
  .map { width:100%; height:auto; max-height:600px; background:#f7fbff; border:1px solid var(--line); border-radius:12px; display:block; margin:0 auto; }
  .map path[data-tip] { cursor:pointer; transition:opacity .1s; }
  .map path[data-tip]:hover, .map path[data-tip]:focus { opacity:.8; outline:none; }
  .pin-live { font:600 13px system-ui; fill:#083; }
  .pin-soon { font:12px system-ui; fill:#555; }
  #tip { position:fixed; z-index:9; max-width:280px; background:#111; color:#fff; font-size:.82rem;
         padding:.5rem .7rem; border-radius:7px; pointer-events:none; opacity:0; transition:opacity .1s; }
  .legend { display:flex; flex-wrap:wrap; gap:.4rem 1.1rem; font-size:.82rem; color:var(--mut); margin:.4rem 0 0; }
  .legend span { display:inline-flex; align-items:center; gap:.35rem; }
  .sw { width:14px; height:14px; border-radius:3px; display:inline-block; }
  .stat { display:flex; flex-wrap:wrap; gap:1.1rem; margin:1.4rem 0; }
  .stat div { flex:1 1 210px; border:1px solid var(--line); border-radius:10px; padding:1rem 1.1rem; }
  .stat b { display:block; font-size:2rem; line-height:1.1; }
  .stat span { color:var(--mut); font-size:.9rem; }
  .scroll { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:.9rem; }
  th,td { text-align:left; padding:.5rem .6rem; border-bottom:1px solid var(--line); vertical-align:top; }
  td.num, th.num { text-align:right; white-space:nowrap; }
  th { background:var(--bg); border-bottom:2px solid var(--ink); white-space:nowrap; }
  .ln { color:var(--mut); font-size:.82rem; min-width:240px; }
  .nf { color:#a33; }
  .st { font-size:.78rem; padding:.1rem .45rem; border-radius:20px; white-space:nowrap; }
  .st-classified { background:#eee; color:#555; }
  .st-pending { background:#fff4d6; color:#8a6d00; }
  .st-verified { background:#dff3e6; color:#0a7a45; }
  .st-disclosed { background:#fde6cf; color:#a5651a; }
  .st-refused { background:#fbdcdc; color:#b11; }
  .chipbar { display:flex; flex-wrap:wrap; gap:.4rem; align-items:center; margin:1.2rem 0 .6rem; }
  .chiplabel { font-weight:700; margin-right:.4rem; }
  .chip { border:1px solid var(--line); background:#fff; color:var(--ink); padding:.35rem .85rem;
          border-radius:20px; cursor:pointer; font:inherit; font-size:.9rem; }
  .chip:hover { border-color:#0b5; }
  .chip.active { background:#0b5; color:#fff; border-color:#0b5; }
  #map { height:520px; border:1px solid var(--line); border-radius:12px; z-index:0; }
  .leaflet-popup-content { font:14px/1.4 system-ui; }
  .filters { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; margin:1rem 0; }
  .filters select, .filters input { width:auto; max-width:none; margin:0; }
  .citymap .commune { fill:#eef4ee; stroke:#c2d4c2; stroke-width:0.8; }
  .citymap .commune:hover { fill:#e3efe3; }
  .citymap .cl { font:9px system-ui; fill:#93a393; pointer-events:none; text-anchor:middle; }
  .citymap .mk { cursor:pointer; }
  .citymap .mk.ap { opacity:.5; }
  .citymap .mk.ap:hover { opacity:.95; }
  .citymap .mk:hover, .citymap .mk:focus { stroke:#111; outline:none; }
  .box { background:#fafafa; border:1px solid var(--line); border-radius:10px; padding:1rem 1.2rem; }
  .cta { background:#f2f8f4; border:1px solid #cfe8d8; border-radius:12px; padding:1.4rem; margin:1rem 0; }
  .btn { display:inline-block; background:#0b5; color:#fff; text-decoration:none; padding:.6rem 1.1rem; border-radius:8px; font-weight:600; margin-top:.6rem; border:0; cursor:pointer; font-size:1rem; }
  a { color:#06c; }
  label { display:block; font-weight:600; margin:1rem 0 .25rem; font-size:.92rem; }
  input, select, textarea { width:100%; max-width:520px; padding:.5rem .6rem; border:1px solid var(--line); border-radius:7px; font:inherit; }
  textarea { min-height:120px; }
  .req { color:#c33; }
  .consent { display:flex; gap:.5rem; align-items:flex-start; max-width:560px; margin:1.2rem 0; }
  .consent input { width:auto; margin-top:.3rem; }
  .foot { max-width:1000px; margin:3rem auto 0; padding:1rem 1.1rem 3rem; border-top:1px solid var(--line); color:var(--mut); font-size:.85rem; }
  .foot a { color:#06c; }
  details { margin:.5rem 0; } summary { cursor:pointer; font-weight:600; }
  article h2, article h3 { margin-top:1.6rem; }
  article ul, article ol { padding-left:1.3rem; }
  article blockquote, blockquote { border-left:3px solid #cfe8d8; margin:1rem 0; padding:.2rem 0 .2rem 1rem; color:#444; }
  code { background:#f2f2f2; padding:.05rem .3rem; border-radius:4px; font-size:.92em; }
"""

TIP_JS = """
  var tip = document.getElementById('tip');
  document.querySelectorAll('[data-tip]').forEach(function(p){
    p.addEventListener('mousemove', function(e){
      tip.textContent = p.getAttribute('data-tip');
      tip.style.left = Math.min(e.clientX+14, innerWidth-290)+'px';
      tip.style.top = (e.clientY+14)+'px'; tip.style.opacity = 1;
    });
    p.addEventListener('mouseleave', function(){ tip.style.opacity = 0; });
  });
"""

NAV = ('<header class="nav"><a href="/" class="brand">internunion</a><nav>'
       '<a href="/">Map</a> <a href="/city.html">Cities</a> <a href="/rights.html">Rights</a> '
       '<a href="/blog.html">Blog</a> <a href="/submit.html">Submit</a> <a href="/about.html">About</a> '
       f'<a href="{GH}">GitHub</a></nav></header>')

FOOTER = (f'<footer class="foot"><div><a href="/">Map</a> &middot; <a href="/city.html">Cities</a> '
          f'&middot; <a href="/rights.html">Rights</a> &middot; <a href="/blog.html">Blog</a> '
          f'&middot; <a href="/submit.html">Submit</a> '
          f'&middot; <a href="/questionnaire.html">Questionnaire</a> &middot; <a href="/about.html">About</a> '
          f'&middot; <a href="/privacy.html">Privacy</a> &middot; <a href="{PATREON_URL}">Support on Patreon</a> '
          f'&middot; <a href="{GH}">GitHub</a></div>'
          f'<p>Last updated {TODAY} &middot; Data licensed '
          f'<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> &middot; Self-funded, '
          f'community-driven. Figures marked <em>unverified</em> or <em>no floor</em> are provisional '
          f'until confirmed at source.</p></footer>')

def shell(title, desc, body, path, head_extra="", tail=""):
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{esc(title)}</title>\n<meta name="description" content="{esc(desc)}">\n'
            f'<link rel="canonical" href="{DOMAIN}{path}">\n'
            f'<meta property="og:type" content="website">\n'
            f'<meta property="og:title" content="{esc(title)}">\n'
            f'<meta property="og:url" content="{DOMAIN}{path}">\n{head_extra}'
            f'<style>{CSS}</style>\n</head>\n<body>\n{NAV}\n<main>\n{body}\n</main>\n{FOOTER}\n{tail}\n</body>\n</html>\n')

# ============================================================ page bodies
index_body = f"""
  <h1>Can an intern afford to live in Europe?</h1>
  <p class="tldr"><strong>internunion</strong> maps what interns are paid against what it costs to live,
  starting with Brussels and expanding across the EU. Internship pay is set country by country, not by the
  Union &mdash; so the gap is enormous. <strong>{len(no_floor)} of 27 EU countries have no legal pay floor
  for interns at all.</strong> Where pay is regulated, it ranges from covering 2.6&times; a room in Riga to
  just 40% of one in Amsterdam.</p>

  <div class="mapwrap">{svg_map}</div>
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
  <div class="scroll"><table>
    <thead><tr><th>Country</th><th>Capital</th><th class="num">Intern pay/mo</th>
    <th class="num">Room rent/mo</th><th class="num">Ratio</th><th>Unpaid?</th><th>How it's regulated</th></tr></thead>
    <tbody>{country_rows()}</tbody>
  </table></div>
  <p><a href="/countries.csv">Download the EU-27 dataset (CSV, CC BY 4.0)</a></p>

  <h2 id="brussels">Brussels &mdash; our first city</h2>
  <p class="tldr">Brussels is where internunion starts. Belgium sets no central pay floor, so the market is
  fragmented: the median stipend here is ~<strong>&euro;{median:.0f}/month</strong> and a single room is
  ~<strong>{burden}% of it</strong>. At the low end (&euro;{lo:.0f}&ndash;1100 &mdash;
  {", ".join(esc(r["name"]) for r in low_end[:3])} and others) little is left after the ~&euro;{LIVABLE_FLOOR_EUR}
  minimum cost of living. Explore all {len(brussels)} organisations on a filterable city map.</p>
  <p><a class="btn" href="/city.html">Open the Brussels dashboard</a></p>

  <h2>The accountability ledger</h2>
  <div class="box">
    <p>Job boards are paid by employers, so they never say whether a role is <em>livable</em> or
    <em>legal</em>. We do. The <strong>Status</strong> column on the <a href="/city.html">Brussels
    dashboard</a> is a public record of how each organisation answers our
    <a href="/questionnaire.html">standardised questionnaire</a>:</p>
    <p><span class="st st-classified">unverified</span> compiled from public research, not yet contacted &middot;
    <span class="st st-pending">response pending</span> questionnaire sent, within the 30-day window &middot;
    <span class="st st-verified">verified compliant</span> replied with proof of paid, compliant terms &middot;
    <span class="st st-disclosed">disclosed sub-standard</span> replied, confirming unpaid or below the cost-of-living floor &middot;
    <span class="st st-refused">did not disclose</span> declined or ignored the window.</p>
    <p style="margin-bottom:0"><strong>Missing data is shown, never invented.</strong> EU-27 figures come from the
    European Commission (DG EMPL) traineeship study, Eurostat minimum wages and HousingAnywhere/Numbeo rents (2026);
    Brussels rows from the EU Transparency Register, EU Whoiswho and official traineeship portals.</p>
  </div>

  <div class="cta">
    <p><strong>Interned somewhere, or know a place that hosts interns?</strong> Add it and tell us what the
    pay and conditions really were. Every submission turns an <em>unverified</em> row into a lived one.</p>
    <a class="btn" href="/submit.html">Submit a place / your experience</a>
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
"""

index_head = (f'<meta property="og:description" content="Open map: internship pay vs cost of living across '
              f'the EU, plus the full Brussels directory.">\n'
              f'<script type="application/ld+json">\n{json.dumps(graph, ensure_ascii=False, indent=1)}\n</script>\n')

city_body = f"""
  <h1>City dashboard</h1>
  <div class="filters" style="margin-top:.2rem">
    <label style="margin:0;font-weight:600">City&nbsp;
      <select id="citysel">
        <option value="brussels" selected>Brussels &mdash; live</option>
        <option disabled>Luxembourg &mdash; coming soon</option>
        <option disabled>Paris &mdash; coming soon</option>
        <option disabled>Amsterdam &mdash; coming soon</option>
        <option disabled>Frankfurt &mdash; coming soon</option>
        <option disabled>Vienna &mdash; coming soon</option>
      </select></label>
  </div>
  <p class="tldr">Brussels is our first city. Belgium sets no central pay floor, so the market is fragmented:
  median stipend ~&euro;{median:.0f}/month, a single room ~{burden}% of it. Filter the map and list below;
  more cities arrive as the data does.</p>

  <div class="chipbar">
    <span class="chiplabel">What kind of place?</span>
    <button class="chip active" data-sector="">All places</button>
    {"".join(f'<button class="chip" data-sector="{esc(s)}">{esc(s)}</button>' for s in SECTORS)}
  </div>
  <div class="filters">
    <select id="f-paid"><option value="">Paid: any</option><option value="yes">paid</option><option value="partial">partial</option><option value="no">unpaid</option><option value="unknown">unknown</option></select>
    <select id="f-status"><option value="">Status: any</option><option value="classified">unverified</option><option value="pending">response pending</option><option value="verified">verified compliant</option><option value="disclosed">disclosed sub-standard</option><option value="refused">did not disclose</option></select>
    <input id="f-search" placeholder="Search name&hellip;" style="max-width:190px">
    <span id="count" style="color:var(--mut);font-size:.9rem"></span>
  </div>
  <div class="legend" style="margin:0 0 .5rem">{CAT_LEGEND}</div>
  <label style="display:inline-flex;align-items:center;gap:.4rem;font-weight:400;margin:.2rem 0 .6rem">
    <input type="checkbox" id="reg-toggle" style="width:auto">
    Also show the {len([r for r in blist if r.get("loc") == "approx"])} EU Transparency Register orgs
    (faint dots, <strong>approximate postcode-level</strong> location)</label>
  <div id="map"></div>
  <p style="color:var(--mut);font-size:.82rem;margin:.4rem 0 0">{n_precise} organisations are precisely
  located on the map; the ~{len([r for r in blist if r.get("loc") == "approx"])} from the
  <strong>EU Transparency Register</strong> are postcode-level only (toggle above) and fully searchable in
  the list below. EU institutions are shown in <span style="color:#1d6fb8;font-weight:600">blue</span>.</p>

  <div class="scroll"><table>
    <thead><tr><th>Organisation</th><th>Type</th><th>Paid</th><th class="num">Stipend/mo</th>
    <th>Status</th><th>Source</th></tr></thead>
    <tbody>{city_list_rows()}</tbody>
  </table></div>
  <p><a href="/institutions.csv">Download the Brussels dataset (CSV)</a> &middot;
  <a href="/submit.html">Add a place</a> &middot;
  <a href="/questionnaire.html">How the status ledger works</a></p>
"""

CITY_JS = ("const ORGS=" + json.dumps(orgs_json, ensure_ascii=False) + ";\n"
    + "const CAT=" + json.dumps(CATCOLOR, ensure_ascii=False) + ";\n" + r"""
  var sector='', regOn=false, EL={};
  document.querySelectorAll('[data-i]').forEach(function(e){
    var k=e.getAttribute('data-i'); (EL[k]=EL[k]||[]).push(e); });
  var map=L.map('map',{preferCanvas:true,scrollWheelZoom:false}).setView([50.8425,4.363],12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
  var curatedLayer=L.layerGroup().addTo(map), regLayer=L.layerGroup();
  var CM=[], RM=[];
  ORGS.forEach(function(o){
    if(o.lat==null) return;
    var ap=o.loc==='approx';
    var m=L.circleMarker([o.lat,o.lon],{radius:ap?4:7,color:'#fff',weight:ap?0:1.5,
      fillColor:CAT[o.type]||'#9e9e9e',fillOpacity:ap?0.5:0.95});
    m.bindPopup('<b>'+o.name+'</b><br>'+o.type+(o.pay?(' &middot; €'+o.pay+'/mo'):'')
      +(ap?'<br><em>approx. location (postcode-level)</em>':'')
      +'<br><a href="'+o.url+'" target="_blank" rel="noopener">website</a>');
    o._m=m; (ap?RM:CM).push(o);
  });
  function pass(o){
    var q=document.getElementById('f-search').value.toLowerCase(),
        p=document.getElementById('f-paid').value, s=document.getElementById('f-status').value;
    return (!sector||o.type===sector)&&(!p||o.paid===p)&&(!s||o.status===s)&&(!q||o.name.toLowerCase().indexOf(q)>=0);
  }
  function drawMap(){
    curatedLayer.clearLayers(); regLayer.clearLayers();
    CM.forEach(function(o){ if(pass(o)) curatedLayer.addLayer(o._m); });
    if(regOn){ RM.forEach(function(o){ if(pass(o)) regLayer.addLayer(o._m); }); }
  }
  function apply(){
    var n=0;
    ORGS.forEach(function(o){ var show=pass(o), els=EL[o.i];
      if(els){ for(var j=0;j<els.length;j++) els[j].style.display=show?'':'none'; }
      if(show) n++; });
    document.getElementById('count').textContent=n+' of '+ORGS.length+' shown';
    drawMap();
  }
  document.querySelectorAll('.chip').forEach(function(c){ c.addEventListener('click',function(){
    document.querySelectorAll('.chip').forEach(function(x){ x.classList.remove('active'); });
    c.classList.add('active'); sector=c.getAttribute('data-sector'); apply(); }); });
  ['f-paid','f-status','f-search'].forEach(function(id){
    document.getElementById(id).addEventListener('input',apply); });
  document.getElementById('reg-toggle').addEventListener('change',function(e){
    regOn=e.target.checked; if(regOn){ regLayer.addTo(map); } else { map.removeLayer(regLayer); } drawMap(); });
  apply();
""")

submit_body = f"""
  <h1>Add a place, or tell us your conditions</h1>
  <p class="tldr">Every data point moves this beyond Brussels. Tell us about a workplace that hosts interns
  &mdash; ideally one you know first-hand. <strong>No account or login needed</strong>, and you can stay
  anonymous: we publish workplace-level facts (pay, conditions), never your identity unless you ask.</p>

  <form action="{FORM_ENDPOINT}" method="POST">
    <input type="hidden" name="_subject" value="internunion submission">
    <label>Organisation name <span class="req">*</span>
      <input name="organisation" required placeholder="e.g. Example Policy Group"></label>
    <label>Sector
      <select name="sector">
        <option>EU institution</option><option>EU agency</option><option>NGO</option>
        <option>think tank</option><option>trade association</option><option>consultancy</option>
        <option>law firm</option><option>foundation</option><option>other</option></select></label>
    <label>City <input name="city" value="Brussels"></label>
    <label>Role title <input name="role" placeholder="e.g. Policy trainee"></label>
    <label>Level
      <select name="level"><option>internship</option><option>junior</option><option>mid-level</option>
        <option>other</option></select></label>
    <label>Was it paid?
      <select name="paid"><option>yes</option><option>no</option><option>partial</option>
        <option>unknown</option></select></label>
    <label>Monthly stipend, gross EUR (leave blank if unpaid/unknown)
      <input name="stipend_eur" inputmode="numeric" placeholder="e.g. 1200"></label>
    <label>Contract type
      <select name="contract">
        <option>Professional Immersion Agreement (CIP)</option>
        <option>academic internship convention</option>
        <option>employment contract</option><option>other / unknown</option></select></label>
    <label>What were the conditions really like? (hours, workload, whether pay covered your costs)
      <textarea name="experience"></textarea></label>
    <label>Your email (optional &mdash; only if you want us to follow up; never published)
      <input type="email" name="email" placeholder="you@example.com"></label>
    <div class="consent">
      <input type="checkbox" id="consent" name="consent" value="yes" required>
      <label for="consent" style="font-weight:400;margin:0">I consent to internunion publishing these
        workplace-level facts as open data (CC BY 4.0). I understand my identity will not be published
        unless I ask, and I can request removal at any time. <span class="req">*</span></label>
    </div>
    <button class="btn" type="submit">Submit</button>
  </form>

  <p style="margin-top:1.5rem">Prefer email? Write to
  <a href="mailto:{CONTACT_EMAIL}?subject=internunion%20submission">{CONTACT_EMAIL}</a>.
  See how we handle your data in the <a href="/privacy.html">privacy notice</a>, and the exact questions we
  put to employers in the <a href="/questionnaire.html">standardised questionnaire</a>.</p>
"""

questionnaire_body = f"""
  <h1>The standardised questionnaire</h1>
  <p class="tldr">We send this same questionnaire to every organisation we list, and we publish whether
  they answered and what they disclosed. Publishing it in full is the point: the method is transparent,
  reproducible, and identical for everyone.</p>

  <h2>What we ask each employer</h2>
  <div class="box">
    <ol>
      <li>Does your organisation host interns or trainees in Brussels?</li>
      <li>Under which contract type &mdash; Professional Immersion Agreement (CIP), academic internship
        convention, employment contract, or other?</li>
      <li>Are internships paid? If so, the gross monthly stipend for a full-time trainee (EUR).</li>
      <li>Does that meet or exceed the Belgian CIP indexed minimum
        (&euro;{CIP_MIN_EUR} gross/month full-time, April 2026)?</li>
      <li>What non-cash benefits are provided (public transport, meal vouchers, housing support, other)?</li>
      <li>Typical duration and weekly hours.</li>
      <li>Approximate number of trainees hosted per year.</li>
      <li>A contact point we can cite for verification.</li>
    </ol>
    <p style="margin-bottom:0">We ask for consent to publish the answers as open data, and we never publish
    an individual's personal data &mdash; only organisation-level facts.</p>
  </div>

  <h2>The four response states</h2>
  <p>Every listed organisation carries one public status, stated as a dated fact. It puts the burden of
  proof on the employer, in line with the direction of travel set by the EU Pay Transparency Directive
  (2023/970, not yet transposed in Belgium) and the proposed Traineeships Directive.</p>
  <ul>
    <li><span class="st st-verified">verified compliant</span> &mdash; replied and provided verifiable proof
      of paid, compliant terms (matching or exceeding the CIP index).</li>
    <li><span class="st st-pending">response pending</span> &mdash; questionnaire delivered; within the
      standard 30-day window (reminders at day 14 and 28).</li>
    <li><span class="st st-disclosed">disclosed sub-standard</span> &mdash; replied, confirming the role is
      unpaid or falls below the local cost-of-living floor.</li>
    <li><span class="st st-refused">did not disclose</span> &mdash; no reply after two reminders and 30 days. The send date is
      recorded; the organisation can attach a right of reply at any time.</li>
  </ul>
  <p>Organisations not yet contacted are shown as <span class="st st-classified">unverified</span> &mdash;
  compiled from public research and not yet put to the questionnaire.</p>
  <p>Are you an employer who wants to move to <span class="st st-verified">verified compliant</span>? Email
  <a href="mailto:{CONTACT_EMAIL}?subject=Questionnaire%20response">{CONTACT_EMAIL}</a>.</p>
"""

privacy_body = f"""
  <h1>Privacy notice</h1>
  <p class="tldr">internunion is a self-funded, non-commercial project. We collect as little personal data
  as possible and never sell it. This notice explains what we hold and your rights under the GDPR.</p>

  <h3>Who is responsible</h3>
  <p>The data controller is the individual maintainer of internunion. Contact for any data request:
  <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>

  <h3>What we collect</h3>
  <ul>
    <li><strong>Voluntary submissions</strong> about workplaces (pay, contract type, conditions). These are
      <em>organisation-level facts</em>, not personal data about you.</li>
    <li><strong>An optional email address</strong>, only if you choose to give one so we can follow up.</li>
  </ul>
  <p>No account or login is required. Submissions can be fully anonymous. Please do not submit special-category
  data (health, political opinions, etc.) or other people's personal data.</p>

  <h3>Why (lawful basis)</h3>
  <p>We process submissions on the basis of your <strong>consent</strong> (GDPR Art. 6(1)(a)), for the
  public-interest purpose of transparency about internship pay and conditions. Published data is released as
  open data (CC BY 4.0) at organisation level. <strong>We never publish your identity unless you explicitly ask.</strong></p>

  <h3>Retention &amp; sharing</h3>
  <p>Organisation-level facts are kept while relevant to the public dataset. Any email you give is used only to
  contact you and is deleted on request or when no longer needed. The form is processed by our form provider,
  and the site is hosted on Railway; we run no advertising or tracking cookies.</p>

  <h3>Your rights</h3>
  <p>You may request access, correction, or erasure of your data, or withdraw consent, at any time by emailing
  <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. You also have the right to lodge a complaint with the
  Belgian Data Protection Authority (Autorit&eacute; de protection des donn&eacute;es / Gegevensbeschermingsautoriteit).</p>

  <h3>If we add "Sign in with LinkedIn"</h3>
  <p>Should we later offer LinkedIn sign-in to verify contributors, it will be used <em>only</em> to confirm you
  are a real professional. We would read basic profile claims in real time and store nothing beyond a yes/no
  verification flag &mdash; never your profile, password, or connections.</p>
"""

about_body = f"""
  <h1>About internunion</h1>
  <p class="tldr">I'm an intern in Brussels. internunion is my personal, self-funded project &mdash; an attempt
  to turn a problem thousands of us live through into something we can actually see, measure, and change.</p>

  <p>We come to Brussels with hope, and quickly meet battles that at first look impossible: rent, transport,
  the plain cost of living. Interns here are paid, proportionally, <em>below</em> the Belgian minimum wage &mdash;
  and in much of the EU, not paid at all. That quietly decides who gets to start a career in the institutions
  built on the promise of democracy: those whose families can subsidise them.</p>

  <p>internunion exists to make that visible and to build the case for change. It maps what interns are actually
  paid against what it costs to live, country by country and organisation by organisation, and keeps a public
  record of which employers will answer a simple, standardised questionnaire about how they treat trainees.
  Fair pay is not charity: a worker who is recognised and can live with dignity contributes more, and handles
  sensitive work more safely. A wider pool of people who can afford to be here makes the institutions stronger.</p>

  <p>The data is open (CC BY 4.0), the method is <a href="/questionnaire.html">published in full</a>, and every
  figure is traceable to its source. It runs on individual effort. If you want to help it keep going, you can
  <a href="{PATREON_URL}">support it on Patreon</a> &mdash; and if you've interned here,
  <a href="/submit.html">tell us your conditions</a>. The point was never to complain alone; pressure in Brussels
  has always worked at the level of the group, never the single person.</p>
"""

rights_body = f"""
  <h1>Know your rights as an intern in Brussels</h1>
  <p class="tldr">Belgium has no single "intern" status &mdash; your rights depend on which contract you are
  on. This is plain-language information, not legal advice. When in doubt, talk to a trade union or Bruxelles
  Formation.</p>

  <h2>The two contracts that matter</h2>
  <div class="box">
    <h3>Academic internship (convention de stage / stageovereenkomst)</h3>
    <p>A three-way agreement between you, your university and the employer, tied to your studies. It is
    generally <strong>unpaid</strong> &mdash; legally only the reimbursement of real, documented expenses is
    required &mdash; and is meant as a learning experience, not a job. This is legal when it is genuinely part
    of your curriculum.</p>
    <h3>Professional Immersion Agreement (CIP / BIO)</h3>
    <p>The <em>Convention d'Immersion Professionnelle</em> (FR) / <em>Beroepsinlevingsovereenkomst</em> (NL) is
    for graduates and jobseekers no longer enrolled in a programme. It requires a written training plan and a
    <strong>legally indexed minimum stipend &mdash; about &euro;{CIP_MIN_EUR} gross/month for a full-time
    placement (2026)</strong>. It is overseen by Bruxelles Formation (FR) or VDAB (NL).</p>
  </div>

  <h2>The "bogus internship" trap</h2>
  <p>Some employers hire recent graduates under a <em>student</em>-style agreement to avoid paying the CIP
  minimum. If you have finished your studies and are doing real, productive work, you should normally be on a
  CIP (or an employment contract) &mdash; not an unpaid academic convention. The European Committee of Social
  Rights has found that Belgium's gaps here fail to protect interns from being used as cheap or free labour.
  If your "internship" looks like a job, it probably should be paid like one.</p>

  <h2>What you are entitled to</h2>
  <ul>
    <li><strong>A written agreement</strong> and a real training plan &mdash; not just tasks.</li>
    <li><strong>Insurance</strong> against workplace accidents.</li>
    <li><strong>Reasonable working time</strong> and rest, like any worker.</li>
    <li><strong>The CIP stipend</strong> if you are a graduate/jobseeker on a professional-immersion placement.</li>
    <li><strong>To be treated as staff, not free labour</strong> &mdash; the placement must teach you something.</li>
  </ul>

  <h2>Living here: the practical rights</h2>
  <ul>
    <li><strong>Register with your commune</strong> when you settle; you usually need a lease and proof of means.</li>
    <li><strong>Rental deposit</strong> is capped (max two months' rent) and must sit in a blocked account.</li>
    <li><strong>Public transport</strong>: under 25 and registered in Brussels, the STIB annual pass is about
    &euro;12/year (&euro;1/month).</li>
    <li><strong>Abusive rent</strong>: since 2025 a rent more than 20% above the regional reference can be
    challenged (loyers.brussels).</li>
  </ul>

  <h2>Where to get help</h2>
  <ul>
    <li><strong>Bruxelles Formation</strong> (FR) / <strong>VDAB</strong> (NL) &mdash; the CIP framework.</li>
    <li><strong>Trade unions</strong> (CSC/ACV, FGTB/ABVV, CGSLB/ACLVB) &mdash; free advice for members.</li>
    <li><strong>The regional labour inspectorate</strong> &mdash; for suspected abuse.</li>
    <li><strong>European Youth Forum</strong> and the <strong>Fair Internship Initiative</strong> &mdash; advocacy and community.</li>
  </ul>

  <div class="cta">
    <p>Interned somewhere in Brussels? Your experience helps everyone. <a href="/submit.html">Add your
    conditions</a>, or read what others are asking on the <a href="/blog.html">blog</a>.</p>
  </div>

  <p style="color:var(--mut);font-size:.85rem">General information compiled from public sources (Belgian labour
  rules, Bruxelles Formation, the European Committee of Social Rights, and the affordability research behind
  this site). Not legal advice. Rules change &mdash; verify with an official source or a union before acting.</p>
"""

# ---- blog: posts are markdown files in content/blog/, rendered at build time ----
POSTDIR = ROOT / "content" / "blog"
def parse_post(p):
    raw = p.read_text(encoding="utf-8"); meta = {}; body = raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for ln in fm.strip().splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1); meta[k.strip()] = v.strip()
    return {"slug": p.stem, "meta": meta, "body": body.strip()}
posts = sorted([parse_post(p) for p in POSTDIR.glob("*.md")],
               key=lambda x: x["meta"].get("date", ""), reverse=True)

def post_page(post):
    m = post["meta"]
    body = (f'<article><h1>{esc(m.get("title", "Untitled"))}</h1>'
            f'<p style="color:var(--mut);font-size:.9rem">{esc(m.get("date", ""))}</p>'
            f'{md_to_html(post["body"])}'
            f'<p style="margin-top:2.5rem"><a href="/blog.html">&larr; All articles</a> &middot; '
            f'<a href="/rights.html">Know your rights</a></p></article>')
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": m.get("title", ""),
          "datePublished": m.get("date", ""), "author": {"@type": "Organization", "name": "internunion"},
          "publisher": {"@id": f"{DOMAIN}/#org"}, "mainEntityOfPage": f"{DOMAIN}/blog/{post['slug']}.html"}
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
    return shell(f'{m.get("title", "Article")} | internunion', m.get("summary", ""), body,
                 f"/blog/{post['slug']}.html", head_extra=head)

blog_index_body = ('<h1>Blog &mdash; intern questions &amp; doubts</h1>'
    '<p class="tldr">Short articles on the real questions of interning in Brussels: contracts, pay, housing, '
    'rights. Have a question you want answered? <a href="/submit.html">Tell us</a>.</p>'
    + ("<p>No articles yet &mdash; check back soon.</p>" if not posts else "".join(
        f'<h2 style="margin-bottom:.1rem"><a href="/blog/{p["slug"]}.html">{esc(p["meta"].get("title", "Untitled"))}</a></h2>'
        f'<p style="color:var(--mut);font-size:.85rem;margin:.1rem 0">{esc(p["meta"].get("date", ""))}</p>'
        f'<p>{esc(p["meta"].get("summary", ""))}</p>' for p in posts)))

# ============================================================ non-HTML files
robots_txt = "".join(f"User-agent: {b}\nAllow: /\n" for b in
    ["OAI-SearchBot","ChatGPT-User","GPTBot","PerplexityBot","Perplexity-User","ClaudeBot",
     "anthropic-ai","Googlebot","Google-Extended","Bingbot","*"]) + f"\nSitemap: {DOMAIN}/sitemap.xml\n"

llms_txt = f"""# internunion

> Open data on internships across the EU: what interns are paid vs what it costs to live, country by
> country, plus the full Brussels directory and a public employer accountability ledger. Self-funded,
> CC BY 4.0. Last updated {TODAY}.

Key facts: {len(no_floor)} of 27 EU countries have no legal pay floor for open-market interns. Where pay
is regulated it ranges from covering 2.6x a room (Latvia) to 0.4x (Netherlands). Brussels median stipend
~EUR {median:.0f}/month; a shared room ~EUR {ROOM_RENT_EUR} ({burden}% of the median).

## Data
- [EU-27 pay vs cost of living]({DOMAIN}/): the map and the country table
- [countries.csv]({DOMAIN}/countries.csv): pay, rent, ratio, minimum wage and unpaid-internship legality per country
- [Brussels directory]({DOMAIN}/#brussels): organisations, pay and response status
- [institutions.csv]({DOMAIN}/institutions.csv): the Brussels dataset
- [Standardised questionnaire]({DOMAIN}/questionnaire.html): the instrument and the four response states

## Optional
- [Submit a place or your conditions]({DOMAIN}/submit.html)
- [About]({DOMAIN}/about.html) and [privacy]({DOMAIN}/privacy.html)
- [Source & method]({GH}): repository, methodology, contributions
"""

PAGES = {
    "index.html": shell("Can interns afford Europe? Pay vs cost of living, EU-wide | internunion",
        f"An open map of internship pay against the cost of living across the EU-27, plus the Brussels "
        f"directory and an employer accountability ledger. {len(no_floor)} of 27 EU countries have no legal "
        f"pay floor for interns.", index_body, "/", head_extra=index_head,
        tail='<div id="tip"></div>\n<script>' + TIP_JS + '</script>'),
    "city.html": shell("Brussels internship dashboard &mdash; filterable map | internunion",
        f"A road map of {len(blist)} organisations in Brussels that host interns, by category: EU "
        "institutions, NGOs, consultancies, think tanks, law firms and more.", city_body, "/city.html",
        head_extra='<link rel="stylesheet" href="/vendor/leaflet.css">\n',
        tail='<script src="/vendor/leaflet.js"></script>\n<script>' + CITY_JS + '</script>'),
    "submit.html": shell("Submit a place or your internship conditions | internunion",
        "Add a Brussels/EU workplace that hosts interns and tell us the real pay and conditions. No login, "
        "anonymous by default, GDPR-compliant.", submit_body, "/submit.html"),
    "questionnaire.html": shell("The standardised questionnaire & response states | internunion",
        "The exact transparency questionnaire internunion sends every employer, and the four public response "
        "states that make up the accountability ledger.", questionnaire_body, "/questionnaire.html"),
    "privacy.html": shell("Privacy notice | internunion",
        "How internunion collects and handles data under the GDPR: consent-based, minimal, no login, "
        "anonymous submissions, and your rights.", privacy_body, "/privacy.html"),
    "about.html": shell("About | internunion",
        "internunion is a self-funded project by an intern in Brussels, mapping internship pay against the "
        "cost of living to build the case for fair, transparent internships.", about_body, "/about.html"),
    "rights.html": shell("Know your rights as an intern in Brussels | internunion",
        "A plain-language guide to intern rights in Brussels: academic vs CIP contracts, the legally indexed "
        "minimum stipend, bogus internships, housing, and where to get help.", rights_body, "/rights.html"),
    "blog.html": shell("Blog: intern questions & doubts in Brussels | internunion",
        "Articles on the real questions of interning in Brussels: contracts, pay, housing, and rights.",
        blog_index_body, "/blog.html"),
}
for _p in posts:                           # one page per markdown article
    PAGES[f"blog/{_p['slug']}.html"] = post_page(_p)

sitemap_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f'  <url><loc>{DOMAIN}/{p.replace("index.html","")}</loc><lastmod>{TODAY}</lastmod></url>\n'
              for p in PAGES) + '</urlset>\n')

# ============================================================ write + check
OUT.mkdir(exist_ok=True)
for name, content in PAGES.items():
    (OUT / name).parent.mkdir(parents=True, exist_ok=True)   # blog/ subdir
    (OUT / name).write_text(content, encoding="utf-8")
(OUT / "robots.txt").write_text(robots_txt, encoding="utf-8")
(OUT / "llms.txt").write_text(llms_txt, encoding="utf-8")
(OUT / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
shutil.copyfile(ROOT / "data" / "institutions.csv", OUT / "institutions.csv")
shutil.copyfile(ROOT / "data" / "countries.csv", OUT / "countries.csv")
(OUT / "vendor").mkdir(exist_ok=True)                       # vendored Leaflet (roads map)
for v in ("leaflet.js", "leaflet.css"):
    shutil.copyfile(ROOT / "assets" / "vendor" / v, OUT / "vendor" / v)

idx = (OUT / "index.html").read_text(encoding="utf-8")
city = (OUT / "city.html").read_text(encoding="utf-8")
assert len(countries) == 27, f"expected 27 EU countries, got {len(countries)}"
assert '<svg' in idx and idx.count("<path") >= 27, "Europe map paths missing"
assert '"@type": "Dataset"' in idx, "Dataset JSON-LD missing"
assert idx.count("<tr>") == len(countries) + 1, "index should hold only the country table"
assert 'id="map"' in city and "leaflet.js" in city, "city Leaflet map missing"
assert city.count("<tr") == len(blist) + 1, "city list rows != all Brussels orgs"
assert (OUT / "vendor" / "leaflet.js").exists(), "vendored leaflet missing"
json.loads(idx.split('application/ld+json">', 1)[1].split("</script>", 1)[0])  # JSON-LD parses
for p in PAGES:                            # every page has nav, main and footer
    h = (OUT / p).read_text(encoding="utf-8")
    assert 'class="nav"' in h and "<main>" in h and 'class="foot"' in h, f"{p} missing shell"
assert FORM_ENDPOINT in (OUT / "submit.html").read_text(encoding="utf-8"), "form endpoint missing"
assert "Professional Immersion" in (OUT / "rights.html").read_text(encoding="utf-8"), "rights page missing"
assert all((OUT / f"blog/{p['slug']}.html").exists() for p in posts), "a blog post failed to render"
print(f"built public/  ({len(PAGES)} pages, {len(countries)} countries, {len(no_floor)} no-floor, "
      f"{len(blist)} Brussels orgs ({n_mapped} mapped), median EUR {median:.0f})")
