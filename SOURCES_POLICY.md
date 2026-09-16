# Data sourcing policy

What internunion is allowed to fetch, and what it is not. Every claim below was checked against the
live endpoint and the operator's own terms in September 2026. This file is the rule, not a preference:
`data/vacancies.py` and `data/verify_sources.py` implement it, and a pull request that widens it
needs a second maintainer.

**The principle.** We take data from the organisation that the data is about, or from an official
public register. We do not take it from an intermediary that sells access to it. That is both the
legal safe harbour and the honest position: we are not competing with job boards, we are auditing
employers.

## Allowed

| Source | Endpoint | Why it is allowed |
|---|---|---|
| **EU Transparency Register** | daily XML export | Official EU open data, reusable under Decision 2011/833/EU with attribution. 17,811 registrants; 3,284 with a Brussels office. Re-exported daily at 20:00 UTC. |
| **EPSO consolidated traineeships** | `eu-careers.europa.eu/en/traineeships-open` | Official EU view, server-rendered, robots.txt permits it. Covers institutions and agencies together. |
| **EU Agencies Network sitemap** | `agencies-network.europa.eu/sitemap.xml` | Published sitemap. The only structured handle to agency vacancy notices since the old EUAN portal was deprecated. |
| **An employer's own ATS** | Personio, Recruitee, Greenhouse, Lever, Ashby, SmartRecruiters, Workday | Public, unauthenticated endpoints the employer publishes to advertise its own vacancies. Personio is the one Brussels think tanks actually use. |
| **An employer's own careers page** | their domain | Checked at most weekly, named user agent, robots.txt respected. |
| **Have Your Say feedback** | Commission better-regulation API | Public consultation responses. We keep only `organization`, `userType`, `country` and the Transparency Register number, and discard respondents' names at ingest. |
| **BeST Address (BOSA)** | `opendata.bosa.be` bulk CSV | CC BY 4.0. The authoritative Belgian address file. |
| **UrbIS (Brussels Region)** | geocoder, WFS, 3D buildings | CC0, public domain, "no limitations to public access". |

## Not allowed

| Source | Why not |
|---|---|
| **jobsin.brussels** | Terms prohibit automated collection verbatim, and assert EU sui generis database rights. Its permissive robots.txt does not override its contract. Permanently out of scope. |
| **Idealist** | Terms prohibit spiders, robots, scrapers and data mining, and prohibit scraping or republishing listings. Out of scope. |
| **Devex** | Blocks all automated access, including robots.txt itself. Cannot be assessed, so not used. |
| **EuroBrussels, EURACTIV Jobs** | No prohibition found, but neither terms page was readable, so they are **permission-unknown, not permitted**. EuroBrussels additionally names AI crawlers in robots.txt, which signals intent about automated reuse. We link out to them; we do not ingest them. |
| **LinkedIn, Indeed, Glassdoor** | Terms prohibit scraping and the operators enforce it. We integrate by linking out only. |
| **Google Maps Geocoding** | Terms §3.2.3(a) names geocodes explicitly as content that may not be extracted, stored, reshared or rehosted, and the caching exception requires deletion within 30 days and isolation per end user. An open dataset cannot satisfy either. Disqualified on licence, not on price. |
| **Nominatim public instance** | The OSM Foundation's usage policy forbids systematic queries and caps use at one request per second. Results are also ODbL share-alike, which would conflict with our CC BY release. |
| **KBO/BCE Belgian company register** | Not an open licence. Requires a registered account, binds reuse to the purpose declared at registration, and makes the licensee a GDPR controller over sole traders' personal data. Needs a deliberate human decision, not a cron job. UrbIS covers the address side under CC0 instead. |

## Geocoding pipeline

Two stages, no API key, fully redistributable, deterministic:

1. **Offline**: the BeST Address Brussels extract (CC BY 4.0), indexed on accent-folded street name plus
   house number, matching French, Dutch and German street names, not filtering on postcode. Resolves
   about three quarters of our addresses with no network call at all.
2. **Residue**: the keyless UrbIS geocoder, which resolves street-name variants that exact matching
   misses (`Rue des 2 Églises` against `Rue des Deux Églises`). Measured end to end on our own 3,284
   Brussels addresses, the two stages together reach **95.4% at house-number precision**.

Normalise before querying: strip `c/o`, split glued words, reduce a range like `9-31` to `9`, drop
box and floor numbers, and send `Street Number Postcode City` space-separated. The remaining few per
cent are coworking brands and bare `c/o` lines, which are fixed by hand once and marked `approx`.

Published coordinates credit BeST/BOSA and UrbIS/Paradigm.

## 3D buildings

OpenFreeMap's vector tiles are excellent for roads, water and labels, but their `building` layer is
**about 1% complete in Brussels**: 46 buildings served against 4,512 present in OpenStreetMap for the
same Schuman tile. Raw OSM height coverage in the EU quarter is only about 3%. So the skyline is
derived instead from **UrbIS 3D Constructions** (CC0, LoD2).

`assets/brussels-buildings.geojson` is that derived layer: **20,807 buildings** across the EU quarter
(longitude 4.3600–4.4050, latitude 50.8300–50.8520), heights from 2.0 m to 118.4 m, median 17.1 m.
Height per building is the maximum roof-surface elevation minus the ground-surface elevation. The
source is six commune-level GeoPackages (203 MB zipped) rather than the 1.85 GiB region file. The
Lambert 72 to WGS84 transform was validated against the Berlaymont footprint in OpenStreetMap: a
centroid offset of 0.77 m and a median vertex distance of 0.07 m. Douglas-Peucker simplification at
about 0.14 m on the ground cut vertices by 28% to fit the file under 6 MB. CC0 means no attribution
string is legally required; we credit Brussels Region anyway because it is the decent thing to do.

To regenerate it for another area, the working scripts are not in this repo; the inputs are the ATOM
feed at `urbisdownload.datastore.brussels` and the rule above. Budget a couple of hours.
