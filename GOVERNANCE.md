# Governance: how the data commons is owned

The goal is that internunion's dataset belongs to no single person, cannot be quietly altered, and
survives its founder losing interest. This document says how that is achieved, and why it is not
achieved with a blockchain DAO.

## The honest answer on a DAO

A DAO was the stated ambition: decentralised ownership of the data, the collection and the fetching.
The ambition is right. The blockchain mechanism is the wrong tool for it, for four reasons, one of
which is fatal.

1. **It is fatal on GDPR.** An immutable public ledger cannot honour a deletion request. We handle
   interns' testimonies and, in the Have Your Say layer, named individuals. Article 17 gives those
   people a right to erasure that an append-only chain structurally cannot satisfy. Putting
   personal data on-chain would make the project unlawful in the jurisdiction it is trying to reform.
   No pseudonymisation scheme fixes this: regulators treat on-chain hashes of personal data as
   personal data.
2. **It solves a problem we do not have.** A DAO's contribution is trustless coordination between
   parties who cannot trust each other. Our contributors are youth organisations, unions and interns
   who share a goal. Our actual coordination problem is *turnover* — people leave every five months —
   and a token does nothing about that.
3. **It adds a second legitimacy problem.** Token-weighted voting means whoever holds the most tokens
   decides what counts as a verified employer. That is exactly the capture risk we exist to expose.
4. **It costs the thing we have least of.** Thirty minutes a day does not stretch to treasury
   management, contract audits or a governance forum.

What a DAO would genuinely give us is: tamper-evidence, no single owner, forkability, transparent
decisions, and verifiable authorship. Every one of those is available from plain infrastructure we
already run, at zero cost. That is what the rest of this document sets up.

## What we do instead: a git-native data commons

| Property a DAO promises | How we actually get it |
|---|---|
| Tamper-evident history | Git. Every figure's change is a commit with an author, a timestamp and a diff. The history is public and replicated on every clone. Maintainers sign commits, so authorship is cryptographically verifiable. |
| No single owner | The licences. Code MIT, data CC BY 4.0. Anyone may fork the whole dataset at any moment and continue without permission. That is the real exit right, and it is stronger than a token. |
| Decentralised collection | Per-city ownership. Each city's rows have a named lead and backup, recorded in `MAINTAINERS.md` and enforced by `CODEOWNERS`, so a chapter's data cannot be changed without its lead reviewing. |
| Transparent decisions | A seven-day request-for-comments issue with lazy consensus for any change to the method, the questionnaire or the four response states. Decisions live as closed issues, permanently readable. |
| Verified contributions | Evidence classes A to D, a second maintainer required for any status change to "did not disclose", and a weekly automated source check that opens an issue when a published figure no longer appears at its source. |
| Resistance to capture | No money in the loop, no tokens, no employer funding. The only currency is a verifiable source. |

## How someone joins

The rule is that **responsibility is earned by merged work, never by asking**, and that every role
is small enough to do in two hours a month. Roles and their current holders live in
[MAINTAINERS.md](MAINTAINERS.md); claim one through the
[join issue](../../issues/new?template=join.yml).

| Step | What it takes | What it grants |
|---|---|---|
| **Contributor** | One merged pull request, or one accepted data submission | Named in the commit history, which is the permanent record |
| **Reviewer** | Five merged data contributions, and a core maintainer proposes it | May approve data pull requests for any city. Still cannot merge a method change |
| **City lead** | Bring a city live: 25 organisations with sources, a sourced rent figure, a local legal note, and a **named backup** | Owns that city's rows via `CODEOWNERS`. No one changes them without their review |
| **National lead** | Publish the national legal page and translate the questionnaire | Owns that country's row in `countries.csv` |
| **Core maintainer** | Sustained work across areas, and unanimous agreement of existing core maintainers | Method, questionnaire, code, licences |

Four things are deliberately true about this ladder:

1. **A backup is a precondition, not a nice-to-have.** A city does not go live, and a role is not
   announced, until someone else is named who can take it. Brussels intern cohorts turn over every
   five months; the projects that died here died of that, not of bad data.
2. **Leaving well is part of the job.** Say you are stopping and hand to your backup. Going quiet is
   the only thing that actually damages the project, because the rows keep aging while looking maintained.
3. **Nobody is blocked from contributing.** You do not need a role to submit a figure or fix a page.
   Roles exist to say who *reviews*, not who is allowed to help.
4. **Inactive roles are reclaimed, not held.** Three months without a response to a mention, and a
   core maintainer moves the role to the backup and marks it open. No hard feelings; five-month
   cohorts make this normal rather than a failure.

## Changing the method: the request for comments

The method is the questionnaire text, the four response states, the evidence classes, the sourcing
policy and the affordability constants. A change to any of these changes what every published figure
*means*, including figures collected before the change. So:

1. Open an issue titled `RFC: <change>` saying what changes, why, and what happens to rows already
   collected under the old rule.
2. Seven days, minimum. Anyone may object; an objection must say what would resolve it.
3. Lazy consensus: no unresolved objection at the deadline means it passes. One core maintainer
   merges, and the issue stays open and readable as the permanent record of the decision.
4. If the change makes old and new figures non-comparable, the rows say so. We never silently
   re-interpret a number someone else collected.

The files under `CODEOWNERS` that require this are marked there.

## The three layers of ownership

- **Core maintainers (2–3 people).** Own the method, the questionnaire, the four states, the code and
  the licences. Cannot unilaterally change a city's rows.
- **City leads (one per city, plus a backup).** Own their rows, their local rent constant, their legal
  note and their questionnaire mailings. Two hours a month.
- **National leads.** Own their country row and the national legal page. Two hours a month.

A chapter may add columns; it may never remove them. Same method, same questionnaire in translation,
same four states, local legal floor.

## Who does the work: fetchers, agents, people

Contribution is not only human. The project runs deterministic fetchers on a schedule, and review
agents that read what those fetchers produced. The rule, set out in [AGENTS.md](AGENTS.md), is that
**anything a deterministic fetcher can do is done by a fetcher, and an agent only reviews the
result.** No agent writes to the dataset and no agent has merge rights.

That rule is a governance rule, not just an engineering one. A model in the data path would mean
published figures that cannot be reproduced by someone who clones the repo, which breaks the only
promise the project makes. It would also quietly concentrate authority in whoever runs the model.
Keeping judgement in pull requests keeps it visible and contestable, which is the thing a DAO was
supposed to provide and this provides for free.

## Rules that make it survive turnover

1. **Nothing lives on a laptop.** If it is not in the repository, it does not exist. The one exception
   is the employer contact file, which is personal data and is deliberately git-ignored.
2. **Every role has a named backup** before it is announced anywhere.
3. **Every automated job is in the repository**, so anyone who forks it inherits a working pipeline,
   not a description of one.
4. **The questionnaire and the method are published verbatim**, so a fork is a real continuation and
   not a rebuild from scratch.

## Where a cryptographic mechanism would actually earn its place

Two narrow cases, neither needed yet, both compatible with GDPR because neither puts personal data
on a chain:

- **Signed employer attestations.** An employer that replies "we pay €1,400" could sign that statement
  with a key tied to its domain. The claim becomes independently verifiable rather than something we
  assert on their behalf. Plain DKIM-style signing over the reply achieves this without a chain.
- **A notarised dataset digest.** Publishing a periodic hash of the dataset to any public timestamping
  service makes "this figure was published on this date" provable to a journalist or a court, without
  putting any content on-chain. This is worth doing once the ledger is cited publicly.

Both are additions to the git model, not replacements for it.
