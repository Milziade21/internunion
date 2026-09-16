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

## The three layers of ownership

- **Core maintainers (2–3 people).** Own the method, the questionnaire, the four states, the code and
  the licences. Cannot unilaterally change a city's rows.
- **City leads (one per city, plus a backup).** Own their rows, their local rent constant, their legal
  note and their questionnaire mailings. Two hours a month.
- **National leads.** Own their country row and the national legal page. Two hours a month.

A chapter may add columns; it may never remove them. Same method, same questionnaire in translation,
same four states, local legal floor.

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
