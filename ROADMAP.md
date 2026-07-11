# internunion — roadmap

## The thesis (one line)
Commercial job boards are paid by employers, so they will never tell an intern whether a role is
*paid enough to live on* or *legally compliant*. internunion is the independent transparency layer
that does — and holds employers to account for answering.

## The wedge (what we own, nobody else can)
**The Employer Response Status ledger.** For each organisation we publicly show one of four states:

- **Verified compliant** — replied to the standardised questionnaire with proof of paid, compliant terms.
- **Response pending** — questionnaire delivered, inside the 14-day window.
- **Disclosed unpaid / sub-standard** — replied, confirming unpaid or below the local cost-of-living floor.
- **Refused to disclose** — declined or ignored the window.

This is FOI-style accountability. Incumbents *structurally cannot* copy it: labelling a paying client
"sub-standard" cannibalises their revenue. Under the 2026 EU Pay Transparency Directive, refusing to
disclose is itself a red flag. This is the moat — everything else supports it.

## Principles / what we will NOT build (the guardrails)
- **No web crawlers over hundreds of bespoke sites.** Coverage-first: registers, RSS, ATS JSON APIs. (see `EU Job Tracker Architecture.docx`)
- **No dedicated machine.** The whole thing is a weekly cron job. Compute is never the bottleneck.
- **No scraping LinkedIn / job boards.** ToS + bot-blocking + GDPR. Link out and integrate instead.
- **No login until it's justified.** Submissions are anonymous by default; add LinkedIn OIDC only for *verification*, storing nothing.
- **Never invent data.** `classified` (unverified) / `answered` / `not answered` is shown, always.

---

## Phase 0 — Foundation ✅ DONE
- Public repo (MIT code, CC BY 4.0 data); Railway deploy via `Dockerfile`.
- `data/institutions.csv` (31 Brussels orgs) + `data/countries.csv` (EU-27 pay/rent/ratio/legality).
- Static site: EU affordability map + Brussels directory + submit CTA.
- Discoverability: schema.org JSON-LD, `robots.txt` (AI crawlers), `llms.txt`, `sitemap.xml`.

## Phase 1 — Launch & be found (next ~2 weeks)
1. **Deploy to internunion.com** on Railway; DNS `CNAME`+`TXT`, TLS.
2. **Google Search Console** → submit `sitemap.xml`; confirm the `Dataset` markup lands in Google Dataset Search.
3. **Verify launch-critical figures.** Click the `source_url` on the paid Brussels rows and the EU-27
   stipends; flip confirmed rows to `answered`. Launch credibility > row count. (These are AI-research numbers.)
4. **Wire the submission form.** Set `SUBMIT_FORM_URL` in `build.py` to a Tally/Google Form (no login).
5. **Add a privacy page** (GDPR): what we collect, lawful basis = consent, retention, removal. Required before collecting.
6. **Add the Patreon link** in the footer/CTA.

## Phase 2 — Ship the wedge: the Response Status engine
*Do this lazily first — a spreadsheet + mail-merge, not an app.*
1. **Write the questionnaire** (the instrument) and publish it verbatim (the method-box promise).
2. **Send it** to the 31 Brussels orgs using their EU Transparency Register contact point.
3. **Track the 4 states** in `institutions.csv` (the `response_status` column already exists — extend the vocabulary).
4. **Show it on the site** — the directory already renders status badges. Every reply visibly improves the page.
5. This is the launch's ongoing engine: each flip from `not answered` → `answered`/`refused` is a story.

## Phase 3 — Complementarity integrations (as capacity allows)
- **LobbyFacts cross-ref** (highest bang-for-buck, pure open data): show an org's EU lobbying spend next
  to what it pays its trainees. "Spends €Xm lobbying, pays interns €0." That table writes its own headlines.
- **Link out, don't rebuild:** deep-link to EuroBrussels / LinkedIn job IDs as the "apply here"; frame
  internunion as the pre-application health check.
- **Vacancy feed (small):** one script hitting the ATS JSON endpoints (Greenhouse/Lever/etc.) of orgs
  already listed + aggregator RSS. GitHub Actions cron, weekly. Coverage-first, no bespoke scrapers.
- **LinkedIn OIDC** for *verified* submissions once volume justifies — `/v2/userinfo` only, store nothing.

## Phase 4 — Expand coverage
- **Full Brussels directory by sector** from the EU Transparency Register + Belgian KBO/BCE (NACE codes to
  exclude retail/food) + OSM geocoding. This is "all the places, by sector." (see `Brussels GIS Directory Design.docx`)
- **Turn on the "soon" city pins** — Luxembourg first (institutional data already in `countries.csv`), then the rest.

## Phase 5 — Distribution & alliances (start at launch, run forever)
- **Transparency Scorecards** as LinkedIn-native PDFs (the feed favours native docs over links).
- **Quarterly "EU Internship Transparency Index"** — pitch to Euractiv / POLITICO / investigative journalists.
- **Partners:** ETUC Youth Committee, European Youth Forum, Fair Internship Initiative, VUB/ULB career &
  social services. Give them white-labelled dashboards; they crowdsource data and amplify campaigns.

---

## Right now — the next 3 actions
1. Deploy to internunion.com + Search Console (Phase 1.1–1.2).
2. Verify ~10 stipend sources so the launch data is defensible (Phase 1.3).
3. Draft the questionnaire + privacy page — the two things that unlock the wedge and let you collect data (Phase 2.1, 1.5).

*Reference research lives in the project root (`.docx`): affordability, legal frameworks, cost of living,
SEO/GEO, job-tracker architecture, GIS directory, and competitor strategy.*
