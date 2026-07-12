#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Local, one-off pipeline: ingest Brussels organisations from the EU Transparency Register
into institutions.csv as candidate internship hosts. Run on your machine; commit the CSV.
The deploy never runs this. Run: python3 ingest_register.py

Steps: download the daily register XML -> clean invalid XML-1.1 char refs -> keep orgs with a
Brussels office (postcode 1000-1210) -> map category to our sector -> dedup vs existing ->
geocode by POSTCODE centroid (not per-org, to respect Nominatim) + deterministic jitter so
markers spread within the correct postcode -> append with loc=approx, pay unknown, status
classified. ponytail: postcode-level is deliberately approximate; upgrade to per-address
geocoding (or a local Nominatim) if you need street precision at this scale.
"""
import xml.etree.ElementTree as ET, csv, json, re, math, hashlib, time, pathlib
import urllib.parse, urllib.request

UA = "internunion-geocoder/1.0 (contact@internunion.com)"
SRC = "https://transparency-register.europa.eu/odplastorganisationxml_en"
HERE = pathlib.Path(__file__).parent
CSV = HERE / "institutions.csv"
XML = HERE.parent / "assets" / "_register.xml"   # gitignored cache (~113MB)
TYPE = {"Non-governmental organisations, platforms and networks and similar": "NGO",
        "Trade and business associations": "trade association", "Companies & groups": "company",
        "Professional consultancies": "consultancy", "Trade unions and professional associations": "trade union",
        "Think tanks and research institutions": "think tank", "Other organisations, public or mixed entities": "public/mixed",
        "Associations and networks of public authorities": "public authority", "Law firms": "law firm",
        "Organisations representing churches and religious communities": "religious",
        "Academic institutions": "academic", "Entities, offices or networks established by third countries": "other"}

def norm(s):
    s = re.sub(r"\(.*?\)", "", s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"\b(the|asbl|aisbl|vzw|ivzw|eu|europe|european|international)\b", "", s).strip()

def in_brussels(pc, city, country):
    city, country = (city or "").lower(), (country or "").lower()
    if country and "belg" not in country: return False
    try: n = int((pc or "").strip())
    except ValueError: n = None
    return (n is not None and 1000 <= n <= 1210) or "brux" in city or "bruss" in city

def load_clean_xml():
    if not XML.exists():
        print("downloading register (~113MB)...")
        req = urllib.request.Request(SRC, headers={"User-Agent": UA})
        XML.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    raw = XML.read_bytes().decode("utf-8", "ignore").replace("version='1.1'", "version='1.0'", 1)
    ok = lambda cp: cp in (9, 10, 13) or 0x20 <= cp <= 0xD7FF or 0xE000 <= cp <= 0xFFFD or 0x10000 <= cp <= 0x10FFFF
    raw = re.sub(r"&#(x?[0-9a-fA-F]+);",
                 lambda m: m.group(0) if ok(int(m.group(1)[1:], 16) if m.group(1)[0] in "xX" else int(m.group(1))) else "", raw)
    return "".join(c for c in raw if ok(ord(c)))

def geocode_postcode(pc):
    for params in ({"postalcode": pc, "countrycodes": "be"}, {"q": f"{pc} Bruxelles", "countrycodes": "be"}):
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"format": "json", "limit": 1, **params})
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20))
        if d:
            lat, lon = round(float(d[0]["lat"]), 6), round(float(d[0]["lon"]), 6)
            if 50.76 <= lat <= 50.92 and 4.23 <= lon <= 4.49: return lat, lon
        time.sleep(1.1)
    return None, None

def jitter(name, lat, lon):
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    ang, rad = (h % 360) * math.pi / 180, 0.0015 + ((h >> 9) % 100) / 100 * 0.0045
    return round(lat + rad * math.sin(ang), 6), round(lon + rad * math.cos(ang) / math.cos(math.radians(lat)), 6)

def main():
    rows = list(csv.DictReader(open(CSV)))
    fields = list(rows[0].keys()) + (["loc"] if "loc" not in rows[0] else [])
    for r in rows: r.setdefault("loc", "exact")
    seen = {norm(r["name"]) for r in rows}

    import xml.etree.ElementTree as ET
    src = pathlib.Path("/tmp/_reg_clean.xml"); src.write_text(load_clean_xml(), encoding="utf-8")
    orgs = []
    for _, el in ET.iterparse(src, events=("end",)):
        if el.tag.rsplit("}", 1)[-1] != "interestRepresentative": continue
        cat = el.findtext(".//{*}registrationCategory") or ""
        if cat in TYPE:
            name = (el.findtext(".//{*}originalName") or "").strip()
            web = (el.findtext(".//{*}webSiteURL") or "").strip()
            pc = ""
            for off in ("EUOffice", "headOffice"):
                o = el.find(".//{*}" + off)
                if o is not None and in_brussels(o.findtext("{*}postCode"), o.findtext("{*}city"), o.findtext("{*}country")):
                    pc = (o.findtext("{*}postCode") or "").strip(); break
            k = norm(name)
            if pc and k and k not in seen:
                seen.add(k); orgs.append({"name": name, "type": TYPE[cat], "pc": pc, "web": web})
        el.clear()

    cent = {}
    for pc in sorted({o["pc"] for o in orgs}):
        cent[pc] = geocode_postcode(pc)
    added = 0
    for o in orgs:
        lat, lon = cent.get(o["pc"], (None, None))
        if lat: lat, lon = jitter(o["name"], lat, lon)
        src_url = o["web"] if o["web"].startswith("http") else "https://transparency-register.europa.eu"
        rows.append({k: "" for k in fields} | {
            "name": o["name"], "type": o["type"], "city": "Brussels", "internship_open": "unknown",
            "paid": "unknown", "response_status": "classified", "address": f'{o["pc"]} Brussels',
            "source_url": src_url, "last_checked": "2026-07",
            "notes": "EU Transparency Register; location approximate (postcode-level).",
            "lat": lat or "", "lon": lon or "", "loc": "approx"})
        added += 1
    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"appended {added} register orgs; total rows {len(rows)}")

if __name__ == "__main__":
    main()
