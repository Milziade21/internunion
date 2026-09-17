# Accounts and API bottlenecks

What actually needs a real account, what does not, and what is blocked until it exists. Checked
September 2026.

**The shape of it.** Everything on the *reading* side is keyless by design: the sourcing policy
chose registers and open data precisely so that no account, key or quota stands between a fork and a
working pipeline. Every bottleneck that remains is on the *contact* side — receiving what people
send us, and sending the questionnaire. Those are the ones to solve, and they are cheap.

## Blocking now

| # | What | Why it blocks | Cost | Fixes |
|---|---|---|---|---|
| 1 | **A form endpoint** (Tally or Formspree) | `FORM_ENDPOINT` in `build.py` is still `YOUR_FORM_ID`. The submit page renders, accepts input, and **delivers nowhere**. Everything a visitor sends today is lost. | Free tier is enough | Every submission route except GitHub issues |
| 2 | **A real mailbox on the domain** (`contact@internunion.com`) | The GDPR contact, the right-of-reply route and the questionnaire sender all point at an address that does not receive. Publishing a contact address that bounces is itself a compliance problem. | ~€1–5/month with the domain | The whole employer email series, so the entire ledger |
| 3 | **DNS pointed at Railway** | `DOMAIN` is set to internunion.com but the site answers on the Railway subdomain. Every canonical URL, the sitemap and the JSON-LD identifiers already claim the real domain, so search engines are being told about a domain that does not serve. | Domain only | Discoverability, and every link we hand to a journalist |

Those three are the difference between a built tool and a working one. None takes thirty minutes.

## Needed for the ledger at volume

| # | What | When | Note |
|---|---|---|---|
| 4 | **Transactional sending** (a real mailbox is fine to ~100/day; a service beyond that) | When mailing more than the 69 curated organisations | Send from the project address, never a personal one. Generic mailboxes only, opt-out in every mail, and check the anti-spam rules before any bulk send. |
| 5 | **Patreon** | Before asking for money | `PATREON_URL` is a placeholder; the footer link currently 404s for supporters. |

## Deliberately not needed

This is the useful half of the list, because each one is a bottleneck we already removed.

| Capability | Would normally need | What we use instead |
|---|---|---|
| Geocoding 3,300 addresses | Google Maps API key and billing | BeST Address bulk file (CC BY) plus the keyless UrbIS geocoder (CC0). No key, no quota, and the result is redistributable, which the Google terms forbid. |
| 3D buildings | A tile provider key | UrbIS 3D Constructions (CC0), derived once into a static file. |
| Basemap tiles | MapTiler or Mapbox key | OpenFreeMap. No key, no registration, no rate limit. |
| Vacancy data | A job-board API contract | Official EU views, sitemaps, and employers' own public ATS endpoints. |
| Organisation registry | KBO/BCE account with purpose-bound reuse | EU Transparency Register daily open data. |
| Running the review agents | An `ANTHROPIC_API_KEY` secret in CI | They run in the maintainer's daily Claude Code session instead. No key, no cost, no secret in the repo — and a human sees the judgement at the moment it is made, which is the point. See [AGENTS.md](AGENTS.md). |
| Verified submissions | LinkedIn app registration | Not built. Only worth it if volume ever justifies it, and then only the OIDC userinfo endpoint, storing nothing. |

## Rules for any account we do open

1. **Registered to the project, never to a person.** A founder's personal account is a single point
   of failure and makes handover impossible. This is the same reason city leads have backups.
2. **Credentials in the repository host's secret store, never in the repo.** `data/contacts.local.csv`
   is git-ignored for the same reason and must stay that way.
3. **A free tier we do not outgrow silently.** Anything with a quota gets a note here saying what
   happens when it runs out.
4. **Written down here when opened**, with who holds it, so the next maintainer inherits a list and
   not a mystery.
