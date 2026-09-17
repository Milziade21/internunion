# Agents: what they may do, and what a fetcher does instead

**The rule.** If a task can be done by a deterministic fetcher, it is done by a deterministic
fetcher. An agent never fetches, never classifies, and never writes to the dataset. An agent reads
what a fetcher produced and answers one judgement question about it, as a proposal a human merges.

This is not a style preference. The project's credibility rests on every figure being traceable and
reproducible: anyone who clones the repo and runs the scripts must get the same numbers we publish.
A model in the data path breaks that, because its output is not reproducible and cannot be audited
by a journalist or a court. So the data path is closed to models, permanently.

```
  cron / daily run
        |
        v
  [ deterministic fetcher ]  -- writes raw output + a diff
        |
        v
  [ review agent ]           -- reads the output, answers ONE question, opens a PR or a comment
        |
        v
  [ human ]                  -- merges, or does not
```

## The audit: what was a candidate for an agent, and what replaced it

Every row here was a place where it would have been easy to reach for a model. None of them do.

| Task | Could a fetcher do it? | What actually does it |
|---|---|---|
| Collect open internships | Yes | `data/vacancies.py` — official views, sitemaps, employers' own ATS endpoints |
| Check a published stipend is still on its source page | Yes | `data/verify_sources.py` — numeric forms of the amount, or a per-org regex |
| Place an office at its street address | Yes | `data/geocode_precise.py` — offline address file, then a keyless geocoder |
| Import the EU Transparency Register | Yes | `data/ingest_register.py` |
| Find which organisations lobbied a policy file | Yes | `data/haveyoursay.py` — joined on Transparency Register number |
| Find an employer's contact address | Yes | `data/find_emails.py` — prefers a generic mailbox over a named person |
| Decide an organisation's sector | Yes | a lookup table in `ingest_register.py`, register category to our sector |
| Decide what experience a vacancy asks for | Yes | a keyword table in `vacancies.py`; the self-test pins the ordering |
| Match an employer name to our row | Yes | exact match plus `data/aliases.csv`; never fuzzy |
| Read a stipend off an awkward page | Yes, with a per-org rule | a regex line in `data/fetchers.csv`. An agent may *propose* the line; the fetcher runs it |

**Removed in this change:** `data/geocode.py`, which used the public Nominatim instance. Its usage
policy forbids systematic queries and its share-alike licence conflicts with our CC BY release. It
was superseded by `geocode_precise.py` and left in the repo it would have been an invitation to
break the sourcing policy.

## The four agents that survive

Each has one question, one input, one output. None writes to `data/*.csv` directly.

### 1. `drift-triage`
- **Question:** the weekly source check says this figure is no longer on its page. Why?
- **Input:** the drift report issue opened by `.github/workflows/verify-sources.yml`.
- **Output:** a comment on that issue classifying each drift as *page moved* (proposes a new
  `source_url`), *figure changed* (proposes the new amount plus the quote that supports it),
  *page is now script-rendered* (proposes a `data/fetchers.csv` line), or *source is gone*
  (proposes dropping to `unknown`). One line of evidence per claim, quoted from the page.
- **Never:** edits the CSV, invents a figure it could not see, or resolves a drift it is unsure about.

### 2. `submission-triage`
- **Question:** which evidence class does this submission meet, and what row change does it justify?
- **Input:** a stipend-report or correction issue.
- **Output:** a comment stating the class (A/B/C/D), the exact field changes it would justify, and
  anything missing that the contributor should be asked for. Opens a PR only for class A with a
  working source URL.
- **Never:** publishes a figure on class D alone, or accepts a source it did not open.

### 3. `reply-triage`
- **Question:** this employer replied to the questionnaire. Which of the four states does the reply
  support, and what did they actually disclose?
- **Input:** the pasted text of a reply, from the local archive.
- **Output:** a proposed row change with the sentence from the reply that supports each field.
- **Never:** marks `refused`. That state comes from silence plus a date, never from a judgement, and
  needs a second maintainer on the PR.

### 4. `weekly-draft`
- **Question:** what is this week's post?
- **Input:** the week's merged diffs and the current dataset.
- **Output:** a draft chart or post. Outside the data path entirely; it reports numbers, never sets them.
- **Never:** states a figure that is not already in a committed CSV.

## Where the agents run

In the daily Claude Code session, on the maintainer's machine, not in CI. That is deliberate: it
needs no API key, adds no cost, no secret, and no account (see [ACCOUNTS.md](ACCOUNTS.md)), and it
keeps a human in the loop at the moment the judgement is made. The fetchers run in CI on a schedule
because they are deterministic and safe to run unattended. The reviewers do not, because their
output is a proposal and a proposal with nobody reading it is just noise.

If that ever changes, the agent still only opens pull requests, and branch protection still requires
a human review. No agent gets merge rights, ever.

## Adding a fifth agent

Answer this first, in the pull request: **what deterministic fetcher did you try, and why did it
fail?** If the answer is "I did not try", write the fetcher. An agent is the fallback for judgement
over free text, not the default for work nobody felt like automating.
