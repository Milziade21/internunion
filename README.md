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

- **[`data/institutions.csv`](data/institutions.csv)** — the seed directory: organisation,
  type, city, internship open?, paid?, monthly stipend, **response status**, address, source.
- **[`data/SOURCES.md`](data/SOURCES.md)** — the rent constant, the housing-index method,
  the research method box, and provenance.
- **[`data/check.py`](data/check.py)** — validates the dataset and computes the housing index.
- **[`build.py`](build.py)** — zero-dependency generator: turns the CSV into a static,
  search- and AI-discoverable site (`public/`) with schema.org `Dataset` JSON-LD, `robots.txt`,
  `llms.txt`, `sitemap.xml`, and an answer-first page.

## Run & deploy

```sh
python3 build.py            # generates public/
cd public && python3 -m http.server 8000   # preview at localhost:8000
```

Deploy the `public/` folder on any static host. On **Railway** or **Cloudflare Pages**: build
command `python3 build.py`, output/publish directory `public`. **Before deploying**, set `DOMAIN`
at the top of [`build.py`](build.py) to your real domain — it drives every canonical URL, the
sitemap, and the JSON-LD IDs.

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

Corrections and additions welcome — especially first-hand stipend figures and internship
experiences. Open an issue or a pull request against `data/institutions.csv`. If you're an
intern in Brussels, your data point moves this forward.

Support the project: *(Patreon link to be added)*

## Licence

- **Code**: MIT (see [`LICENSE`](LICENSE)).
- **Data** (`data/*.csv`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — reuse
  freely with attribution to internunion.

Data is compiled from public sources (EU Transparency Register, EU Whoiswho, official
traineeship portals) and community submissions. Figures marked `classified` are unverified;
treat them as provisional until the linked source is confirmed.
