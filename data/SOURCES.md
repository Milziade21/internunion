# internunion — data sources & method

## What this is
`institutions.csv` is the seed dataset for the Brussels internship directory + housing index.
Every row is currently `response_status = classified`: compiled from AI deep-research over public
sources, **not yet verified by clicking the source or by a reply from the institution**. That is
deliberate and honest — the status column upgrades to `answered` / `not answered` as you send the
questionnaire and check sources.

Provenance of the seed: EU Transparency Register + EU Whoiswho + official traineeship portals,
via Gemini Deep Research (July 2026). Treat every stipend as provisional until the `source_url` is
opened. Known conflict already flagged in-row: EESC (1370 vs 1538.88).

## Column meaning
`response_status`: **classified** = from research, unverified · **pending** = questionnaire sent, in
window · **verified** = replied, compliant · **disclosed** = replied, sub-standard · **refused** = no
reply after contact. This column is the lever — a public "refused to disclose" is defensible.
`loc`: **exact** = precisely geocoded from a street address · **approx** = postcode-level only.

## Comprehensive layer: the EU Transparency Register
Beyond the ~69 curated Brussels orgs, `institutions.csv` now includes ~3,300 organisations with a
Brussels office pulled from the **EU Transparency Register** (daily open-data XML, 17k+ registrants,
filtered to postcodes 1000-1210). These are **candidate** internship hosts: `internship_open=unknown`,
`paid=unknown`, `response_status=classified`, `loc=approx` (placed at their postcode centroid with a
deterministic jitter, not a verified street location). Regenerate with `python3 data/ingest_register.py`.
Source: <https://transparency-register.europa.eu> (odplastorganisationxml_en).

## The rent constant (housing index)
Single number, updateable in one place. Source: Brukot / Federia Rental Barometer 2025 (pub. Feb 2026).

    ROOM_RENT_EUR = 509        # market-wide shared room (colocation), monthly
    # alternatives: 660 furnished private room · 700-950 corporate coliving (utilities bundled)

## The livable floor (the real headline)
Minimum monthly cost for an intern in a shared room (Statbel / Sibelga / STIB 2025-26):

    rent 509 + utilities 60 (small client) + groceries 200 + transport 1 (<25, registered) = ~770/month
    (transport 56/month if 25+ or unregistered -> ~825/month)

Headline the page should lead with, straight from the data:
- Median institutional stipend ~1538 -> rent burden 33%, livable.
- Lowest stipends in the sample (EPC 950, FleishmanHillard/BusinessEurope 1000, Political Intelligence 1095)
  leave **180-325 EUR/month** after the minimum floor — for people handling sensitive EU policy work.

## Method box (publish verbatim on the page — this is the academic-credibility layer)
1. Universe: Brussels EU-affairs organisations (institutions, agencies, NGOs, think tanks, trade
   associations, consultancies, law firms) + pan-EU institutional traineeship programmes.
2. Instrument: a standardised questionnaire (publish the exact text).
3. Collection: public sources first (register, official portals); then direct questionnaire.
4. Missingness shown, never imputed: unknown pay = blank + `unknown`; no reply = `not answered`.
5. Every figure traceable to `source_url` with `last_checked` date.

## Deferred (research already gathered, not in the CSV yet)
- EU-27 affordability comparison -> the season-two map (EU Internship Affordability Dataset.docx)
- Brussels budget food/drink map (Brussels Budget Food Guide.docx)
- Legal/rhetorical ammunition: Belgian CIP, Ombudsman 2017 unpaid-internship ruling, proposed
  Traineeships Directive (Belgian and EU Internship Pay.docx) -> manifesto / about page
