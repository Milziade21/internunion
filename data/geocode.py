#!/usr/bin/env python3
# Copyright (c) 2026 Gábriel Rossi. Licensed under the MIT License.
"""Local, one-off geocoder: fill lat/lon on institutions.csv from each row's address
via OpenStreetMap Nominatim. Run on your machine, commit the result; the deploy never
geocodes. Idempotent — rows that already have lat are skipped. Run: python3 geocode.py

ponytail: naive 1-req/sec loop over ~30 rows. If the directory grows to thousands,
switch to a batch geocoder or a local Nominatim instance.
"""
import csv, json, time, re, urllib.parse, urllib.request, pathlib

CSV = pathlib.Path(__file__).parent / "institutions.csv"
UA = "internunion-geocoder/1.0 (contact@internunion.com)"   # Nominatim requires a real UA

def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"format": "json", "limit": 1, "q": q})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    return (round(float(d[0]["lat"]), 6), round(float(d[0]["lon"]), 6)) if d else (None, None)

rows = list(csv.DictReader(open(CSV)))
fields = list(rows[0].keys())
for c in ("lat", "lon"):
    if c not in fields: fields.append(c)

for r in rows:
    if r.get("lat"):                                # already geocoded -> skip
        continue
    addr = re.sub(r"\s*\([^)]*\)", "", r["address"]).strip()   # drop "(address unverified)" etc.
    q = addr or f'{r["name"]}, {r["city"]}'
    try:
        lat, lon = geocode(q)
    except Exception as e:
        lat, lon = None, None
        print(f"  ! {r['name']}: {e}")
    r["lat"], r["lon"] = (lat or ""), (lon or "")
    print(f'{"ok " if lat else "MISS"} {r["name"]:<34} {r["lat"]},{r["lon"]}  <- {q[:45]}')
    time.sleep(1.1)                                 # be polite to Nominatim

with open(CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(rows)
got = sum(1 for r in rows if r["lat"])
print(f"\nwrote {CSV.name}: {got}/{len(rows)} geocoded")
