#!/usr/bin/env python3
"""Sanity check for institutions.csv + the housing-index math. Run: python3 check.py"""
import csv, pathlib

ROOM_RENT_EUR = 509           # market-wide shared room, Brussels (Brukot/Federia 2025)
LIVABLE_FLOOR_EUR = 770       # rent 509 + utilities 60 + groceries 200 + transport 1 (<25, registered)

rows = list(csv.DictReader(open(pathlib.Path(__file__).parent / "institutions.csv")))

# schema + value integrity
allowed_status = {"classified", "answered", "not answered"}
allowed_paid = {"yes", "no", "partial", "unknown"}
for r in rows:
    assert r["name"], "row missing name"
    assert r["response_status"] in allowed_status, f'bad status: {r["response_status"]!r} ({r["name"]})'
    assert r["paid"] in allowed_paid, f'bad paid: {r["paid"]!r} ({r["name"]})'
    s = r["monthly_stipend_eur"].strip()
    assert s == "" or float(s) > 0, f"bad stipend: {s!r} ({r['name']})"

# housing-index math: rent burden = rent / stipend; below-floor = stipend under livable floor
paid = [r for r in rows if r["monthly_stipend_eur"].strip()]
def burden(r): return ROOM_RENT_EUR / float(r["monthly_stipend_eur"])
below_floor = [r for r in paid if float(r["monthly_stipend_eur"]) < LIVABLE_FLOOR_EUR]
stipends = sorted(float(r["monthly_stipend_eur"]) for r in paid)
median = stipends[len(stipends)//2]

assert 0 < burden(min(paid, key=burden)) < 1, "best rent burden should be a sane fraction"
assert all(float(r["monthly_stipend_eur"]) >= ROOM_RENT_EUR for r in paid), \
    "sample: every listed stipend at least covers a shared room"  # if this breaks, someone earns less than rent

print(f"{len(rows)} rows, {len(paid)} with stipend, {len(rows)-len(paid)} unknown/blank")
print(f"median stipend {median:.0f} EUR -> rent burden {ROOM_RENT_EUR/median*100:.0f}%")
print(f"below livable floor ({LIVABLE_FLOOR_EUR} EUR): {[r['name'] for r in below_floor] or 'none'}")
print("OK")
