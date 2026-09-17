# internunion

**Open data on internships in Brussels — who hosts them, who pays, and whether an intern can actually afford to live here.**

internunion is a self-funded, open-source project mapping the internship and traineeship
ecosystem of Brussels — EU institutions, agencies, NGOs, think tanks, trade associations,
consultancies and law firms — with a housing-affordability index that puts each stipend
against the real cost of living in the city. Brussels first, EU-wide next.

## Why

Interns are one of the beating hearts of Brussels. We arrive with hopes and then fight
battles that look impossible: housing, transport, the cost of simply living here. Interns
are paid, percentage-wise, *below* the Belgian minimum wage. This project collects the data,
gives it a face through personal stories, and builds the case for fair, transparent, and
collectively-bargained internship conditions.

## What's here now

The homepage is a **Europe choropleth** — each country shaded by intern pay ÷ capital-city room
rent, grey hatching where there is no legal pay floor — with city pins for coverage (Brussels live,
other hubs coming soon), and the **accountability ledger**. Projected from a GeoJSON at build time;
no library. The **Brussels city dashboard** (`/city.html`) is a **3D city map**: MapLibre GL
(vendored in `assets/vendor/`) over OpenFreeMap's white-and-grey vector tiles, with OpenStreetMap
buildings extruded. Each precisely-located organisation rises as a **beam** whose height is its
disclosed monthly stipend, capped by a dot coloured by kind of place; organisations that have not
disclosed pay are a short grey stub, never a low beam. The ~3,300 EU Transparency Register orgs sit
behind a toggle as flat dots (postcode-level, approximate). Category chips + pay/status/search
filters drive the map and the directory list together. `/jobs.html` lists **open internships** next to
what each employer pays and whether they answered the questionnaire. `build.py` also generates `submit`, `questionnaire` (the
instrument, published verbatim), `privacy` (GDPR), and `about` pages.

### Before launch, set four things in [`build.py`](build.py)
`DOMAIN` (done: internunion.com), `FORM_ENDPOINT` (your Formspree/Tally URL for the submit form),
`CONTACT_EMAIL` (GDPR/data-request address), and `PATREON_URL`. Placeholders build fine but the form
won't deliver and the contact links won't work until set.

- **[`data/countries.csv`](data/countries.csv)** — EU-27: intern pay, capital room rent, affordability
  ratio, minimum wage, and the **legal status of unpaid internships** per country.
- **[`data/institutions.csv`](data/institutions.csv)** — the Brussels directory: organisation,
  type, city, internship open?, paid?, monthly stipend, **response status**, address, source.
- **[`data/SOURCES.md`](data/SOURCES.md)** — the rent constant, the housing-index method,
  the research method box, and provenance.
- **[`data/check.py`](data/check.py)** — validates the dataset and computes the housing index.
- **[`data/vacancies.py`](data/vacancies.py)** — collects open internships from cleared sources only
  (EPSO's consolidated view, the EU Agencies Network sitemap, employers' own ATS endpoints), files
  each by required experience, and writes `data/vacancies.csv`. Never touches commercial job boards.
- **[`data/geocode_precise.py`](data/geocode_precise.py)** — places each office at its street address:
  an offline exact match against the BeST Address extract (CC BY 4.0), then the keyless UrbIS geocoder
  (CC0) for the residue. 2,973 of 3,345 Brussels organisations are now pinpointed, up from 55.
- **[`data/haveyoursay.py`](data/haveyoursay.py)** — finds which organisations are active on a policy
  file, via the Commission's consultation feedback, joined on Transparency Register number. Discards
  respondents' personal data at ingest.
- **[`data/verify_sources.py`](data/verify_sources.py)** — re-opens each stipend's source page and
  reports whether the figure we publish is still there. A weekly job opens an issue on drift.
- **[`build.py`](build.py)** — zero-dependency generator: turns the CSV into a static,
  search- and AI-discoverable site (`public/`) with schema.org `Dataset` JSON-LD, `robots.txt`,
  `llms.txt`, `sitemap.xml`, and an answer-first page.
- **`content/blog/*.md`** — blog articles. Add a markdown file with `title`, `date`, `summary`
  frontmatter and it builds into `/blog/<slug>.html` (newest first on `/blog.html`). Supported
  markdown: headings, bold/italic/code, links, lists, blockquotes, `---` rules.

## Run & deploy

```sh
python3 build.py            # generates public/
cd public && python3 -m http.server 8000   # preview at localhost:8000
```

### Railway

The repo is Railway-ready via the [`Dockerfile`](Dockerfile): it runs `python3 build.py` at build
time and serves `public/` on `$PORT`. Just create a Railway project from this GitHub repo — Railway
detects the Dockerfile and deploys, no extra config. Then add `internunion.com` as a custom domain
in Railway (Settings → Networking) and point your DNS `CNAME` + `TXT` records at it.

The canonical domain is set via `DOMAIN` at the top of [`build.py`](build.py)
(`https://internunion.com`); it drives every canonical URL, the sitemap, and the JSON-LD IDs.

### The response-status column
Every row starts as `classified` (compiled from public research, not yet verified). It becomes
`answered` when an institution replies to our standardised questionnaire, or `not answered` when
it doesn't. Missing data is shown, never invented. A public record of who declined to answer is
itself the point.

### The number
Median internship stipend in the sample: ~€1400/month. A single room in a Brussels shared flat:
~€509/month — **36% of a median stipend, before food, transport, and utilities.** At the low end
(€950–€1095) interns are left with €180–€325/month after the minimum cost-of-living floor.

## Roadmap

- [ ] Static site rendering the directory + housing index (discoverable, crawlable, agent-readable)
- [ ] Standardised questionnaire sent to every listed organisation
- [ ] Personal stories — faces behind the data
- [ ] EU-27 affordability map (stipend vs. rent, country by country)
- [ ] Brussels budget food & drink map

## Contributing

**Roles are open and small** — about two hours a month, and you do not need to be a developer for
most of them. See [`MAINTAINERS.md`](MAINTAINERS.md) for what is vacant and
[claim one here](../../issues/new?template=join.yml). The most useful thing anyone can do right now
is be a **backup** for an existing role.

| Document | What it settles |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Evidence classes A–D, the response ledger, the checks on every PR |
| [`GOVERNANCE.md`](GOVERNANCE.md) | How someone joins and earns responsibility, the RFC process, and why this is not a blockchain DAO |
| [`MAINTAINERS.md`](MAINTAINERS.md) | Who holds which role, and which are vacant |
| [`AGENTS.md`](AGENTS.md) | Deterministic fetchers do the work; agents only review; no model ever touches the data path |
| [`SOURCES_POLICY.md`](SOURCES_POLICY.md) | What we may and may not fetch, checked against each operator's terms |
| [`ACCOUNTS.md`](ACCOUNTS.md) | Which API keys and accounts are actually needed, and the ones we designed away |
| [`STRATEGY.md`](STRATEGY.md) | The organising plan, allies, language and the 30-minutes-a-day rhythm |
| [`outreach/employer-emails.md`](outreach/employer-emails.md) | The four-email employer series, published verbatim |
| [`RESEARCH_PROMPTS.md`](RESEARCH_PROMPTS.md) | Ten deep-research prompts to source the argument |

Corrections and additions welcome — especially first-hand stipend figures and internship
experiences. Open an issue or a pull request against `data/institutions.csv`. If you're an
intern in Brussels, your data point moves this forward.

Support the project: *(Patreon link to be added)*

## Licence

This project is licensed under the **MIT License** — Copyright (c) 2026 Gábriel Rossi. See the
[`LICENSE`](LICENSE) file for the full text.

- **Code**: MIT (see [`LICENSE`](LICENSE)).
- **Data** (`data/*.csv`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — reuse
  freely with attribution to internunion.

Data is compiled from public sources (EU Transparency Register, EU Whoiswho, official
traineeship portals) and community submissions. Figures marked `classified` are unverified;
treat them as provisional until the linked source is confirmed.
