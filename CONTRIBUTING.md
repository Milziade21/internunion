# Contributing data to internunion

Every figure on the site comes from `data/institutions.csv` and `data/countries.csv`, and every change
to them goes through a pull request. This page is the whole protocol. If it is not written here, it is
not the rule.

## Three doors, one queue

1. **GitHub issue form** (preferred): [report a stipend](../../issues/new?template=stipend-report.yml)
   or [correct a row](../../issues/new?template=correction.yml).
2. **The website form** at `/submit.html`. A maintainer turns each submission into an issue.
3. **Email** to the contact address on the privacy page. Same: it becomes an issue.

A submission is never edited straight into the CSV. Issue first, then PR, then merge.

## Evidence classes

| Class | What it is | What it can change |
|---|---|---|
| **A** | The organisation's own public page stating the figure (traineeship page, vacancy, FAQ) | Everything: `paid`, `monthly_stipend_eur`, `internship_open` |
| **B** | The organisation's written reply to the standard questionnaire | Everything, plus `response_status` |
| **C** | A first-hand document (contract, offer letter, payslip) shown to a maintainer, redacted, **never published or stored** | Everything, with `evidence=C` visible on the row |
| **D** | First-hand testimony with no document | Only `paid`; a figure is shown as "community-reported" once two independent D reports agree within 10% |

Personal data is never committed: no names of interns, no personal e-mail addresses. Organisation
contact points for the questionnaire live in `data/contacts.local.csv`, which is git-ignored.

## Columns you must fill on every change

`source_url` (the A/B page or `questionnaire` for B), `last_checked` (YYYY-MM), and, in the PR
description, the evidence class and the GitHub handle of who checked. The git history is the audit log.

## The response ledger

`response_status` has exactly these values:

| Value | Meaning | Public label |
|---|---|---|
| `classified` | Compiled from public research, not yet verified | unverified |
| `pending` | Questionnaire delivered, within 30 days | response pending |
| `verified` | Replied with verifiable paid, compliant terms | verified compliant |
| `disclosed` | Replied, confirming unpaid or below the livable floor | disclosed sub-standard |
| `refused` | No reply after two reminders and 30 days | **did not disclose** |

Process: log the send date; remind at day 14 and day 28; flip to `refused` at day 30 only with a
second maintainer's approval on the PR. Every reply is archived locally and summarised publicly. Any
organisation can have a verbatim right of reply attached to its row; corrections are merged within
72 hours. We publish dated facts ("no reply as of 2026-11-01"), never motives.

## Checks that run on every PR

`python3 data/check.py` validates the CSV and the housing-index math; `python3 build.py` must build.
Both run in GitHub Actions. A weekly job runs `python3 data/verify_sources.py` and opens an issue
if a source page no longer shows the figure we publish.

## Adding a city or a country

A city goes live with 25 curated organisations carrying sources, a sourced room-rent constant, a
local legal note, and a named lead plus a backup. A country row in `countries.csv` needs the legal
status of unpaid internships with a citation. See `STRATEGY.md` section 5 for roles.

## Code

Stdlib only, no new dependencies, one PR per change. Mark intentional shortcuts with a `ponytail:`
comment naming the ceiling and the upgrade path. MIT header on every new source file.
