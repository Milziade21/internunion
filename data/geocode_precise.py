#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Pinpoint each organisation's office: postcode centroid -> real street address.

Two stages, no API key, results redistributable under CC BY (see SOURCES_POLICY.md):
  1. OFFLINE  BeST Address (BOSA) Brussels extract, CC BY 4.0. Exact match on accent-folded
     street name + house number, across the FR / NL / DE spellings. No network call.
  2. RESIDUE  the keyless UrbIS geocoder (underlying data CC0), which resolves street-name
     variants exact matching misses ("Rue des 2 Eglises" vs "Rue des Deux Eglises").

Google's Maps ToS forbids storing or redistributing geocodes, and Nominatim's usage policy
forbids systematic queries, so neither is usable for an open dataset. See SOURCES_POLICY.md.

  python3 data/geocode_precise.py --selftest   # no network
  python3 data/geocode_precise.py --dry-run    # report coverage, write nothing
  python3 data/geocode_precise.py              # update institutions.csv (lat/lon/loc)

ponytail: the offline index is a plain dict held in memory (~850k rows, a few hundred MB while
running). Ceiling is one city's address file; for a second country, build the index into a sqlite
file once and query that instead.
"""
import csv, io, re, sys, json, time, zipfile, pathlib, unicodedata
import urllib.request, urllib.error, urllib.parse

HERE = pathlib.Path(__file__).parent
CSVF = HERE / "institutions.csv"
CACHE = HERE.parent / "assets" / "_best_bru.zip"          # gitignored, ~18 MB
BEST_URL = "https://opendata.bosa.be/download/best/openaddress-bebru.zip"
URBIS = "https://geoservices.irisnet.be/localization/Rest/Localize/getaddresses"
UA = "internunion-geocoder/2.0 (+https://github.com/Milziade21/internunion)"
BBOX = (4.20, 50.75, 4.50, 50.95)                          # lon/lat sanity box for Brussels-Capital

# ---------------------------------------------------------------- address normalisation
def fold(s):
    """Accent- and case-fold, collapse punctuation: 'Rue des Deux Églises' -> 'rue des deux eglises'."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()

_NUM = re.compile(r"\b(\d+[a-zA-Z]?)\b")
# A register address usually ends with the municipality; BeST street names never do, so trim it.
CITY_WORDS = ("brussels", "bruxelles", "brussel", "bruessel", "belgium", "belgique", "belgie",
              "etterbeek", "ixelles", "elsene", "schaerbeek", "schaarbeek", "saint gilles",
              "sint gillis", "saint josse", "sint joost", "uccle", "ukkel", "woluwe", "auderghem",
              "oudergem", "anderlecht", "jette", "evere", "forest", "vorst", "koekelberg",
              "watermael", "watermaal", "boitsfort", "bosvoorde", "ganshoren", "molenbeek",
              "berchem", "sainte agathe", "haren", "laeken", "laken", "neder over heembeek")
def _trim_city(folded):
    changed = True
    while changed:
        changed = False
        for w in CITY_WORDS:
            if folded.endswith(" " + w):
                folded = folded[: -len(w) - 1].strip(); changed = True
    return folded
def split_address(addr):
    """('Rond-Point Robert Schuman 2-4', ...) -> ('rond point robert schuman', '2').

    Handles the shapes actually present in the register: glued CamelCase ('Cabinet ARCTURUS
    GROUPBoulevard du Regent, 35'), bilingual slashes ('Rue Ravenstein / Ravensteinstraat, 4'),
    number-first ('10 Square Ambiorix'), ranges ('2-4'), and box/floor suffixes.

    Order matters: the house number is taken from the WHOLE cleaned string before the bilingual
    slash is cut, because 'Rue Ravenstein / Ravensteinstraat, 4' carries its number after the slash.
    """
    a = (addr or "").strip()
    a = re.sub(r"\bc/o\b.*?(?=[A-Z])", " ", a, flags=re.I)          # drop 'c/o ...' prefixes
    a = re.sub(r"([a-z])([A-Z])", r"\1 \2", a)                      # unglue CamelCase joins
    a = re.sub(r"\b(bte|boite|box|bus|floor|etage|verdieping|app|apt)\b\.?\s*\S*$", "", a, flags=re.I)
    a = re.sub(r"(\d+)\s*[-\u2013]\s*\d+", r"\1", a)                # range 2-4 -> 2
    a = re.sub(r"\b(1[0-2]\d\d)\b", " ", a)                        # a postcode is not a house number
    nums = _NUM.findall(a)
    num = ""
    if nums:
        num = (nums[0] if a.strip()[:1].isdigit() else nums[-1]).lower()
    street_src = _NUM.sub(" ", a)                                   # strip numbers, then pick language
    if "/" in street_src:
        parts = [x for x in street_src.split("/") if len(fold(x)) > 3]
        street_src = parts[0] if parts else street_src
    return _trim_city(fold(street_src).strip()), num

# ---------------------------------------------------------------- stage 1: offline BeST
def load_best(verbose=True):
    if not CACHE.exists():
        if verbose: print(f"downloading BeST Brussels ({BEST_URL}) ...")
        CACHE.parent.mkdir(exist_ok=True)
        req = urllib.request.Request(BEST_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r, open(CACHE, "wb") as f:
            f.write(r.read())
    idx = {}
    with zipfile.ZipFile(CACHE) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as fh:
            rd = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"))
            latk = next((c for c in (rd.fieldnames or []) if "4326" in c and "lat" in c.lower()), None)
            lonk = next((c for c in (rd.fieldnames or []) if "4326" in c and "lon" in c.lower()), None)
            if not latk or not lonk:
                raise SystemExit(f"BeST: no EPSG:4326 columns in {rd.fieldnames}")
            streets = [c for c in rd.fieldnames if "streetname" in c.lower().replace("_", "")]
            numk = next(c for c in rd.fieldnames if "houseNumber" in c or "house_number" in c.lower())
            for row in rd:
                try: lat, lon = float(row[latk]), float(row[lonk])
                except (TypeError, ValueError): continue
                num = (row.get(numk) or "").strip().lower()
                for sc in streets:                       # index every language spelling
                    st = fold(row.get(sc))
                    if st: idx.setdefault((st, num), (lat, lon))
    if verbose: print(f"BeST index: {len(idx):,} street+number keys")
    return idx

# ---------------------------------------------------------------- stage 2: UrbIS residue
def urbis(addr, postcode, city="Bruxelles"):
    street, num = split_address(addr)
    if not street: return None
    q = " ".join(x for x in (street, num, postcode, city) if x)     # space-separated, NOT comma
    url = f"{URBIS}?{urllib.parse.urlencode({'spatialReference': '4326', 'language': 'fr', 'address': q})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, OSError, ValueError):
        return None
    for res in (d.get("result") or []):
        q_ = res.get("qualificationText") or {}
        if q_.get("policeNumber") != "Found":            # street-level only is not a pinpoint
            continue
        p = res.get("point") or {}
        lat, lon = p.get("y"), p.get("x")
        if lat and lon and BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]:
            return float(lat), float(lon)
    return None

# ---------------------------------------------------------------- driver
def main(dry=False, limit=None):
    rows = list(csv.DictReader(open(CSVF, encoding="utf-8")))
    todo = [r for r in rows if r["city"] == "Brussels" and r.get("loc") != "exact" and r["address"].strip()]
    if limit: todo = todo[:limit]
    print(f"{len(todo)} organisations to pinpoint (of {len(rows)} rows)")
    idx = load_best()
    hit_off = hit_net = 0
    residue = []
    for r in todo:
        st, num = split_address(r["address"])
        pt = idx.get((st, num)) if num else None
        if pt:
            r["lat"], r["lon"], r["loc"] = f"{pt[0]:.6f}", f"{pt[1]:.6f}", "exact"; hit_off += 1
        else:
            residue.append(r)
    print(f"stage 1 (offline BeST): {hit_off}/{len(todo)} = {hit_off/max(1,len(todo))*100:.1f}%")
    print(f"stage 2 (UrbIS): {len(residue)} to query, ~{len(residue)*0.45/60:.1f} min ...")
    for i, r in enumerate(residue):
        pt = urbis(r["address"], (r.get("address") or "").strip() and _postcode(r["address"]))
        if pt:
            r["lat"], r["lon"], r["loc"] = f"{pt[0]:.6f}", f"{pt[1]:.6f}", "exact"; hit_net += 1
        if i % 200 == 199: print(f"  {i+1}/{len(residue)} ({hit_net} resolved)")
        time.sleep(0.12)
    tot = hit_off + hit_net
    print(f"\npinpointed {tot}/{len(todo)} = {tot/max(1,len(todo))*100:.1f}% "
          f"({hit_off} offline, {hit_net} via UrbIS); {len(todo)-tot} left at postcode level")
    if dry:
        print("--dry-run: institutions.csv NOT written"); return 0
    with open(CSVF, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"wrote {CSVF.name}")
    return 0

def _postcode(addr):
    m = re.search(r"\b(1[0-2]\d\d)\b", addr or "")
    return m.group(1) if m else ""

def selftest():
    assert fold("Rue des Deux Églises") == "rue des deux eglises"
    assert split_address("Rond-Point Robert Schuman 2-4") == ("rond point robert schuman", "2")
    assert split_address("10 Square Ambiorix") == ("square ambiorix", "10")
    st, n = split_address("Rue de la Loi 200, 1040 Brussels")
    assert st == "rue de la loi" and n == "200", (st, n)          # postcode must not win over house no.
    st, n = split_address("Cabinet ARCTURUS GROUPBoulevard du Regent, 35")
    assert "boulevard du regent" in st and n == "35", (st, n)
    st, n = split_address("Rue Ravenstein / Ravensteinstraat, 4")
    assert st == "rue ravenstein" and n == "4", (st, n)
    st, n = split_address("Avenue de Cortenbergh 100, bte 3")
    assert st == "avenue de cortenbergh" and n == "100", (st, n)
    assert _postcode("Rue de la Loi 200, 1040 Brussels") == "1040"
    assert split_address("Silversquare Central")[1] == ""      # not an address: no number, no pin
    assert split_address("Avenue des Arts 56, 1000 Bruxelles")[0] == "avenue des arts"
    assert split_address("Rue Belliard 40, 1040 Etterbeek, Belgium")[0] == "rue belliard"
    print("selftest OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit(0)
    sys.exit(main(dry="--dry-run" in sys.argv,
                  limit=int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None))
