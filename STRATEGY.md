# internunion — strategy and operating plan

*Written September 2026 for the maintainer and for the people we hope will join. It is a working
document: correct it by pull request. Technical roadmap lives in [ROADMAP.md](ROADMAP.md); data
rules in [CONTRIBUTING.md](CONTRIBUTING.md); research to run in [RESEARCH_PROMPTS.md](RESEARCH_PROMPTS.md).*

---

## 0. In one paragraph

internunion is an open-data project that shows what interns are paid against what it costs to live
where they work, and keeps a public, evidence-based record of which employers answer a standard
questionnaire about their trainees. Brussels is the pilot. The aim is not a website; it is a shared,
transnational instrument that interns, unions, youth organisations, journalists and legislators can
all point to when they argue that interns must be paid enough to live. Everything below is organised
around one constraint: the maintainer has about 30 minutes a day.

## 1. Goal and theory of change

**North star.** Every internship in Europe is paid at least a livable floor, and interns are treated as
the first rung of the workforce rather than as free labour.

**Instrument.** Transparency, not protest. A public, auditable dataset plus a public record of who
answered. The record does the persuading; we describe, we do not accuse.

**Chain.** Verified data → shareable comparisons → press and peer pressure → employers move to
"verified compliant" → the same data becomes evidence for legislators (Traineeships Directive
transposition, Belgian follow-up to the European Social Charter ruling, national laws) → paid
internships become the norm and unpaid ones become reputationally expensive.

**Why Brussels is the testbed, not just the first city.** Brussels' defining feature is that its
interns *leave*. Cohorts turn over every five months and go home to Rome, Warsaw, Madrid and Dublin.
That is usually described as the thing that killed every previous Brussels intern campaign, and it
did. Inverted, it is the distribution engine: the method, the questionnaire and the code are all
public and forkable, so an intern who used the Brussels map can stand up their own city with a CSV
and a weekend. **If even one country reproduces the system, the project has already won**, because
the argument stops being one website's claim and becomes a comparable measurement. So every design
decision is judged by one question: does this make the thing easier to copy? That is why the
questionnaire is published verbatim, why the pipeline is stdlib-only with no account to create, and
why a city goes live on 25 rows rather than 500.

**Three horizons.**
1. *Brussels proof (Oct 2026 – mid 2027).* A defensible dataset, a working response ledger, first
   employers moved, first press, first allies.
2. *National chapters (2027).* Two or three more cities live under the same method, each with a
   local lead. A national page per country with the legal floor and the affordability ratio.
3. *Federation (2028).* A light, shared governance for the method and the questionnaire; the code
   and data stay in one repo; each chapter owns its rows.

**What success looks like.**

| Horizon | Measure |
|---|---|
| 6 months | 100 Brussels rows verified at source; 40 organisations sent the questionnaire; 10 "verified compliant"; 2 press mentions; 3 committed collaborators |
| 12 months | 1 second city live; the ledger cited by a youth organisation, a union, or an MEP in a public document; 1 university career service links to us |
| 24 months | 3 cities live; a national lead in 2 countries; the dataset cited in a parliamentary question or a directive-transposition consultation |

## 2. Where we stand (September 2026)

- Live at internunion-production.up.railway.app; the custom domain internunion.com is configured in
  the code but not yet pointed. The submit form endpoint is still a placeholder.
- Dataset: 3,424 organisations, of which 69 are curated with addresses and 27 carry a stipend figure.
  Every row is still `classified`, meaning compiled from research and not yet verified by opening
  the source. The other ~3,350 rows are the EU Transparency Register layer (candidates, pay unknown).
- Method, questionnaire, privacy page, guardrails and licences exist and are published.
- No collaborators yet, no legal entity, no money needed yet.
- Validated by the research already done: the wedge (the response ledger), the guardrails (no
  scraping of job boards or LinkedIn, no invented data), and the complementarity positioning with
  job boards, review sites and civic-tech projects.

## 3. Who tried before, and what we learn from them

| Who | Where / when | What they did | What happened |
|---|---|---|---|
| Génération Précaire | France, 2005– | White-mask protests, testimonies, lobbying | Mandatory *gratification* for internships over 2 months (2006, tightened 2014). Movement is now dormant, law stayed. |
| La Repubblica degli Stagisti | Italy, 2007– | Journalism plus the **"Bollino OK Stage"**: employers who meet published pay and quality criteria get a certified badge | Still active; regional minimum stipends for extra-curricular internships since the 2012 labour reform. The badge is the closest precedent to our "verified compliant". |
| Intern Aware | UK, 2010– | Minimum-wage enforcement route: complaints to the tax authority, test cases | Several back-pay wins; faded once founders moved on. |
| Plattform Generation Praktikum | Austria, 2007– | Surveys and legal information | Kept the issue in national debate. |
| Sandwich Protest → InternsGoPro, Brussels Interns NGO | Brussels, 17 July 2013 | Protest on Place du Luxembourg; then an intern rating platform and an NGO | Both faded within a few years: five-month trainee cycles destroyed continuity, and a rating site without an institutional partner had no engine. |
| Fair Internship Initiative | Geneva and Brussels, 2015– | Born from the UN intern who lived in a tent; campaigns for paid UN and EU traineeships | Still active; Council of Europe traineeships became paid. Natural transnational ally. |
| Pay Our Interns | USA, 2016– | One data report ("Experience Doesn't Pay the Bills") counting which congressional offices paid interns | Congress created a paid-intern fund in 2018. The strongest proof that a **count** changes behaviour. |
| European Ombudsman | 2017 | Found unpaid traineeships in EU delegations to be maladministration | The EEAS started paying delegation trainees in 2018. |
| European Parliament | 2019 | Bureau decision ending unpaid traineeships in MEP offices | Now paid Schuman and MEP traineeships. |
| European Youth Forum | 2017–2023 | Collective complaint to the European Committee of Social Rights against Belgium | Belgium found in breach of the European Social Charter over "bogus" unpaid internships (decision published February 2023). Ten years of campaigning for a directive. |
| EU legislator | 2014–2026 | Quality Framework for Traineeships (2014, soft), Parliament's legislative-initiative resolution (2023), Commission's directive proposal (March 2024), Council position (June 2025, narrow scope), Parliament position (October 2025, rapporteur Alicia Homs), trilogues from November 2025 | As of the latest public sources found, the trilogue has not concluded. **Verify before citing** (research prompt 6). |

**Lessons we build on.**
1. Every campaign that won paired a **legal hook** with a **data product**. We have the hook (Social
   Charter ruling, directive, CIP minimum); we are building the product.
2. Rating sites without an institutional partner died. We embed from day one with organisations
   that outlive intern cohorts: youth forums, unions, universities.
3. Intern turnover is the enemy of continuity. Our data lives in a public repo, roles are written down,
   and every role has a backup. Nothing depends on one person's laptop or inbox.
4. Positive incentives work. Repubblica degli Stagisti's badge shows that employers will move for
   recognition. "Verified compliant" is the reward; the public record is the floor.
5. Headlines come from **one number** and **one face**. The dataset supplies the number; consenting
   interns supply the face.

## 4. Legal robustness

**Entity.** Stay an unincorporated open-source project (MIT code, CC BY 4.0 data) until money or a
formal partnership requires more. Then prefer *fiscal sponsorship* by an existing Belgian ASBL over
founding one. Long term, an AISBL fits the transnational goal. Do not spend 2026 on statutes.

**Not a trade union.** The name means "a union of interns and allies". Say so on the About page.
Belgian law reserves collective-bargaining roles to recognised unions; we work with them, we are not one.

**Personal data (GDPR).** We publish organisation-level facts only. Contact addresses used for the
questionnaire stay in `data/contacts.local.csv`, which is git-ignored and never published.
Submissions: consent, minimisation, stated retention, an erasure route via the privacy page.
Personal testimonies are published only with written consent and after anonymisation; the original
is deleted after publication.

**Reputation and right of reply.** The ledger states verifiable facts, dated. "Questionnaire sent on
DATE to the organisation's registered contact point; no reply as of DATE" is a fact. "Refuses" is a
motive we cannot prove, so the public label becomes **"did not disclose"**, never "refused". Two
reminders (day 14 and 28), state flips at day 30, every reply is archived locally and summarised
publicly, any organisation can obtain a verbatim right of reply on its row, corrections within 72
hours, and the git history is the audit trail.

**The Pay Transparency Directive claim.** The site said that under the directive "refusing to
disclose is itself a red flag". Belgium missed the 7 June 2026 transposition deadline and asked for
six more months, and the directive covers *workers*, so its application to trainees depends on
national law. Reworded in this change to "the direction of travel". Do not lean on it in press work.

**Scraping and database rights.** We fetch only an organisation's own traineeship page, identified
by a clear user agent, at most weekly, honouring robots.txt, storing only the extracted figure and a
hash of the page. The EU Transparency Register is open data reusable with attribution. No LinkedIn,
no job boards, no review sites.

**Conflict of interest.** The maintainer is an intern in a listed organisation. Publish a one-line
disclosure on the About page, treat that row exactly like every other row, and have another
maintainer approve any change to it.

**Name.** Before printing anything, check "internunion" against the Benelux (BOIP) and EU (EUIPO)
trade-mark registers. Ten minutes.

## 5. Structure: city, national, transnational

Governance mirrors the data model, which is already city rows plus country rows.

| Layer | Owns | Minimum commitment | Goes live when |
|---|---|---|---|
| **City lead** (plus one backup) | Their city's rows in `institutions.csv`, the local rent constant, the local legal note, the questionnaire mailings for their city | 2 hours a month, one PR a month | 25 curated organisations with sources, sourced rent figure, local legal page, lead and backup named |
| **National lead** | Their row in `countries.csv`, the national legal page (contract types, legal floor, who to call), translation of the questionnaire | 2 hours a month | Legal page published, questionnaire translated |
| **Core maintainers** (2–3 people) | Method, questionnaire text, the four states, code, licences, the corrections log | Weekly | Now |

**Rules of the federation.** Same method, same questionnaire (translated), same four states, local
legal floor. A chapter may add columns, never remove them. Method changes go through a 7-day
request-for-comments issue with lazy consensus. A `MAINTAINERS.md` lists who holds which role and
who their backup is. Onboarding a lead is one merged PR plus a 30-minute call.

**Candidate next cities**, chosen by ally availability rather than size: Luxembourg (institutions,
data already partly in hand), Geneva (Fair Internship Initiative), Strasbourg (Parliament and Council
of Europe), Rome or Milan (Repubblica degli Stagisti), Paris, Berlin, Vienna, The Hague.

## 6. Allies: who, what to ask, where to meet them

**Tier 1, ask this autumn.** Each ask is one sentence; each ally gets something back (data, a
dashboard, a co-branded chart).

- **European Youth Forum** (Brussels). Owns the directive campaign and the Social Charter case. Ask:
  cite the ledger in the "Can you afford to work for free?" material; co-host a Brussels moment on
  International Interns' Day, 10 November. Give: a Brussels dataset they can quote.
- **ETUC Youth Committee** (Brussels). Co-litigant on the Belgian case; wants sector-level evidence.
  Ask: a legal-review contact and amplification through affiliates. Give: a white-label view of the
  ledger by sector.
- **Fair Internship Initiative**. Ask: be our Geneva and UN counterpart, share their questionnaire
  experience. Give: the method and the code, ready to fork.
- **Trainee committees**: Blue Book Stagiaires Committee (Commission), Schuman trainees (Parliament),
  Council, EESC and CoR trainee groups. They renew every five months and have WhatsApp groups of
  hundreds. Ask: one message to the cohort with the submit link at intake (1 October, 1 March).
- **Alicia Homs's office** (S&D rapporteur) and the shadow rapporteurs on the traineeships file
  (names on the Parliament's legislative observatory page). Ask: what evidence would help them, and
  a 15-minute call. Give: Brussels numbers for their speeches.
- **Bruxelles Formation and Actiris** (CIP administrators). Ask: confirm the CIP figures and the
  "who to call" text on the rights page. Give: a clearer public explanation of the CIP than exists today.

**The youth and union layer — who can actually carry a process.** The question is not who agrees
with us; in Brussels almost everyone does. It is who is still here in eighteen months. Youth
organisations turn over with their cohorts and their elected boards; unions do not, and unions have
lawyers. Rank by permanence and by what each one holds that we do not.

| Ally | Holds what we lack | Ask | Give |
|---|---|---|---|
| **ETUC Youth Committee** (Brussels) | The only youth structure with a seat at European social dialogue, and affiliates in every member state | A named legal contact, and one line of support at the 10 November moment | Ledger cuts by sector |
| **Belgian union youth wings** — Jeunes CSC / ACV Enter, Jeunes FGTB / ABVV Jongeren, Jong CGSLB | A Belgian legal service, permanent staff, and standing to act for someone on a CIP | Whether a CIP trainee can be represented, and by whom | Brussels rows; the questionnaire in FR and NL |
| **CSC United Freelancers** (and the FGTB equivalent) | An existing Belgian union structure built for people who are *not* employees — the nearest template for interns | Thirty minutes on how they built it and what it cost | Nothing yet; this is a study call |
| **European Youth Forum** | The one table where every European party youth wing already sits | Put intern pay on a Council of Members agenda once, so we brief them all in one room | A dataset they can quote |
| **Conseil de la Jeunesse (FWB) and Vlaamse Jeugdraad** | A statutory right to hand their governments an opinion that must be received | An own-initiative opinion citing the ledger | The Brussels figures, before publication |
| **European party youth wings** — YEPP, YES, LYMEC, FYEG, Young European Left, ECR youth, plus JEF Europe | Reach into their own parties' MEP offices, which is faster than ours | The same email, on the same day, to all of them | The same data to all of them |
| **EU staff unions** — Union Syndicale, R&D, Generation 2004, FFPE, Solidarité Européenne | Standing inside the institutions, and a record on junior and precarious categories | Whether trainees can be represented at all under the Staff Regulations | Institutional trainee stipends counted against the floor |
| **ETUI** (Brussels) | The union movement's research institute, publishing on precarious work | A method review, then a co-published note | Data and co-authorship |

**Rule for the party youth wings: all or none, same day, same text.** One family's launch is the end
of the cross-party frame (§10) and of every centre-right conversation after it. If only one answers,
take the meeting, take no logo, and keep asking the others. Research prompt 11 exists to establish
what any of this is legally, before we ask anyone for it.

**Tier 2, over the winter.** VUB and ULB
student social services and career services; College of Europe and IES student bodies; the European
Students' Union and Erasmus Student Network Brussels; JEF Europe; Generation2030; CESI Youth; Social
Platform; Transparency International EU and LobbyFacts (Corporate Europe Observatory) for the
lobbying-spend cross-reference; Open Knowledge Belgium and the Brussels civic-tech meetups for
developer collaborators; well-paying employers who benefit from being named first.

**Peers for the transnational layer.** Repubblica degli Stagisti (IT), Génération Précaire (FR),
Intern Aware (UK), Plattform Generation Praktikum (AT), DGB Jugend (DE), union youth sections in
ES and IT, Pay Our Interns (US), Interns Australia, Canadian Intern Association.

**Media.** Brussels Times, POLITICO Europe (Playbook and its trainee-season pieces), Euractiv,
EUobserver, The Parliament Magazine, Bruzz, Le Soir, De Standaard. Pitch a data table, not an opinion.

**Where to actually meet people with 30 minutes a day.** Thursday evening on Place du Luxembourg
during trainee season (the whole ecosystem is there); European Youth Forum and ETUC public events;
trainee committee socials and the intake welcome events on 1 October and 1 March; Press Club Brussels
Europe evenings; Open Knowledge Belgium and civic-tech meetups; European Youth Week and the European
Youth Event in Strasbourg; International Interns' Day on 10 November, which we should co-organise
rather than attend. One event a month is enough if you leave each with two names and send both a
follow-up the next morning.

**Money, only when needed.** Patreon exists. Erasmus+ Youth Participation Activities and the Council
of Europe's European Youth Foundation fund youth-led projects at the size we would need, but both
require a legal entity or a sponsoring organisation. Not before 2027.

## 6b. Carrot and stick

The ledger alone is a stick, and a stick-only project gets ignored by the people it needs. So the
tool carries both, and the carrot is what makes an intern visit in the first place.

**The carrot: every open internship in Brussels, in one place, with the pay attached.**
`data/vacancies.py` collects live traineeship and internship postings and files each one by the
experience it actually asks for: internship, entry (0–2 years), mid, senior, unspecified. It draws
only on sources cleared in [SOURCES_POLICY.md](SOURCES_POLICY.md) — the EU's own consolidated
traineeships view, the EU Agencies Network sitemap, and each employer's own applicant-tracking
system. Job boards are never ingested; we link out to them. Crucially, each vacancy sits next to what
that employer pays and whether they answered the questionnaire, which is the one thing no job board
will ever show. That is the reason to come back, and the reason journalists and students will link to it.

**The stick: a public record of who answered.** Four emails over 30 days to each organisation's public
contact point, published verbatim in [outreach/employer-emails.md](outreach/employer-emails.md), plus
ten self-reported criteria shown on the map as yes / no / not answered. An organisation that replies
gets **verified compliant** and is listed above the ones that did not. The stick is only ever a dated
fact about correspondence; the carrot is where the energy goes.

**The loop that connects them.** A live vacancy identifies an employer. The employer gets the
questionnaire. The reply, or its absence, becomes a public status. That status is then attached to
their next vacancy. Every posting makes the ledger more complete, and every reply makes the job map
more useful.

## 7. Product: catchy, simple, shareable

Rebuild the front around one question, one number, one action.

- **Homepage.** "Can an intern afford to live here?" A city selector, then three cards: median
  stipend, cost of a room, what is left after the livable floor. Below it the ledger, sorted so that
  "verified compliant" employers come first. The Europe map moves below the fold.
- **One page per organisation** (`/org/<slug>`), with the figure, the status, the source, the date
  last checked, and a share row: native share, copy link, LinkedIn share URL, Bluesky intent. Four
  static social-preview images, one per status, so every shared link carries its verdict.
- **Every number wears its source and its date.** No exceptions; it is the whole credibility.
- **Mobile first.** The list before the map on small screens.
- **Embeddable badge** for universities and NGOs: a script tag or iframe that shows an employer's
  status, so a career service can drop it into its portal.
- **Languages.** English first; French and Dutch for the Brussels legal pages; national leads
  translate their own pages.
- **The 3D city.** The Brussels map is a white-and-grey three-dimensional city with a beam rising
  from each organisation and a coloured cap on top. Beam height is the disclosed monthly stipend;
  organisations that have not disclosed pay are a short grey stub, never a low beam, so missing data
  never reads as bad pay. The point is that the employers who pay well visibly stand above the quarter.
- **Open internships**, filterable by the experience level they ask for, each shown next to that
  employer's pay and response status.
- **Do not build:** accounts, comments, a mobile app, our own job board. We catalogue and link out.

All of this stays a zero-dependency static build in `build.py`. Each item is one Claude Code session
scoped to one pull request.

## 8. Contributions: gathered, audited, added precisely

Full rules in [CONTRIBUTING.md](CONTRIBUTING.md). The shape:

- **Three doors, one queue.** GitHub issue forms (structured, preferred), the website form
  (Formspree → maintainer opens the issue), and email. Everything becomes an issue, then a PR.
- **Evidence classes.** A = the organisation's own public page; B = the organisation's written reply
  to the questionnaire; C = a first-hand document (contract, payslip) seen by a maintainer, redacted,
  never published; D = first-hand testimony without a document. A figure is published with A, B or C.
  D alone only sets `paid` and is labelled "community-reported" once two independent reports agree.
- **Every change is a PR** that names the evidence class, the source, the date and who checked.
  `data/check.py` runs on every PR. Status changes to "did not disclose" need a second maintainer.
- **The fetcher.** `data/verify_sources.py` opens every sourced stipend page and reports whether the
  figure still appears; a weekly GitHub Action opens an issue on drift. Organisation pages that need
  a specific pattern get a one-line regex in `data/fetchers.csv`. Deterministic, no AI in the data path.
- **The ledger process.** Mail merge from the local contacts file; log `contacted_on`; reminders at
  day 14 and 28; state flips at day 30; replies archived locally, summarised publicly.

## 9. Distribution

**Cadence that fits the time budget.** One LinkedIn post a week, one press pitch a month, one event
a month, one quarterly index.

**Formats.**
- *LinkedIn:* native PDF scorecards (the feed favours documents over links), one chart a week.
- *Instagram and TikTok:* a carousel "what your stipend buys you in Brussels", made once per intake.
- *Bluesky and X:* threads aimed at journalists and MEP staff, always with the table.
- *Trainee WhatsApp and Telegram groups:* the highest-yield channel; one message per intake via the
  trainee committees, never spam.
- *University newsletters and career portals:* the badge.
- *Press:* the quarterly "Brussels Internship Transparency Index" as a ready-made table.

**Hooks in the calendar.** 1 October and 1 March (Commission and Parliament intakes), 10 November
(International Interns' Day), directive trilogue milestones, Belgium's pay-transparency transposition,
the annual rent barometer, the Brussels back-to-school week. The next hook is in two weeks.

**Launch sequence for 1 October 2026.** Verify the 27 stipend rows at source (about ten a week from
now), wire the form, point the domain, publish a "welcome to Brussels, here is what your stipend
buys" post and a one-page flyer for Schuman and Place du Luxembourg, and message the new cohorts
through their committees.

## 10. Language: the consensus frame

Interns should be paid more. The frame that gets there is not left or right; it is a set of
arguments that each political family already believes.

| Audience | Argument that already belongs to them |
|---|---|
| Centre-right, liberals | **Merit.** An unpaid internship selects for parents' wallets, not for talent. Fair pay is how you get the best people. |
| Employers, SMEs | **Fair competition.** An employer that pays is undercut by one that does not. Belgium's own labour minister called unpaid internships "unfair competition". A common floor protects the compliant. |
| Conservatives, national governments | **Workforce formation is a national duty.** Countries with shrinking youth cohorts cannot afford to lose the first rung of the career ladder to those who can wait unpaid. Underpaid Brussels traineeships drain talent from poorer regions and member states. |
| Security and institutions | **Integrity.** Trainees in institutions, consultancies and law firms handle sensitive files. Financial precarity is a recognised vulnerability in every vetting framework. An intern with €180 left after rent is an avoidable risk. |
| Rule of law | **Compliance.** Belgium was found in breach of the European Social Charter. The institutions that write Europe's labour law should model it. |
| Fiscal hawks | **Public finance.** Paid interns pay contributions and taxes; unpaid ones are subsidised by families and, indirectly, by the state. Parliament, the EEAS and the Council of Europe all switched to paid and did not collapse. |
| Progressives | **Equality and cohesion.** A European civil service that only the well-off can enter loses its legitimacy. |
| Employers again | **Retention.** Paid interns stay, and the cost of hiring a known trainee is a fraction of an external hire. |

**Words.** Use: fair pay, livable stipend, transparency, public record, verified, did not disclose,
who answers. Avoid: exploitation, slavery, boycott, name-and-shame, refuse, scandal. Describe, never
accuse. Praise first: the employers who pay well are named before the ones who do not. No party
logos on anything.

The research prompts in [RESEARCH_PROMPTS.md](RESEARCH_PROMPTS.md) exist to put sourced evidence
behind each row of this table.

## 11. Time: 30 minutes a day

That is roughly 3.5 hours a week and 15 hours a month. It is enough if the work is batched and
nothing is started that cannot finish in one sitting.

**Weekly rhythm.**

| Day | 30 minutes on |
|---|---|
| Monday | Verify two rows at source; flip status; commit |
| Tuesday | Two outreach messages (one new, one follow-up) |
| Wednesday | One build task, scoped to one PR, run with Claude Code |
| Thursday | Read the answers to a research prompt fired in the morning; or an evening event |
| Friday | Write and post the week's chart or scorecard |
| Weekend | Optional: the month's press pitch or the quarterly index |

**Rules.** Fire Gemini deep research in the morning, read it in the evening. Every Claude Code
session ends with a merged PR or is reverted. Anything that needs more than 30 uninterrupted
minutes waits for a weekend or a collaborator. Say no to features.

**First 90 days.**

| Weeks | Deliverables |
|---|---|
| 1–2 (to 1 Oct) | 27 stipend rows verified; form wired; domain pointed; About page disclosure; 1 October post and flyer; message to the trainee committees |
| 3–6 | Questionnaire sent to the 69 curated organisations; first "verified compliant" badges; organisation pages shipped; European Youth Forum and ETUC Youth meetings held |
| 7–10 | 10 November co-organised; first press table published; first collaborator holds a role with a backup; `MAINTAINERS.md` |
| 11–13 | Luxembourg or Geneva scoped with a named lead; quarterly index no. 1; research prompts all run and folded into the About and Rights pages |

## 12. Risks

| Risk | Mitigation |
|---|---|
| Maintainer burnout or cohort turnover | Everything in the repo; two maintainers by month 3; roles with backups |
| Legal letter from a listed organisation | Factual dated wording, right of reply, corrections within 72 hours, a union or youth-forum legal contact lined up in advance |
| A wrong figure goes viral | Evidence classes, source and date on every number, public corrections log |
| Perceived party capture | Cross-party frame, no logos, praise-first ordering |
| Retaliation against the maintainer | Public disclosure, separation of personal and project identity, allies informed |
| Scope creep | The "do not build" list; one PR per session |

## 12b. Data ownership

The ambition of putting the dataset beyond any one person's control is right, and
[GOVERNANCE.md](GOVERNANCE.md) sets out how it is met: signed git history for tamper-evidence,
MIT and CC BY licences so anyone can fork without permission, per-city ownership enforced by code
owners, and a public request-for-comments process for any change to the method. It also explains why
a blockchain DAO is not the mechanism. The short version is that an immutable ledger cannot honour a
GDPR erasure request, and we hold interns' testimonies, so the two are incompatible in the
jurisdiction we are trying to reform.

## 13. Decisions for the owner

1. Approve the relabel of "refused to disclose" to "did not disclose" (done in this change, revert if you disagree).
2. Pick the second city to scope in weeks 11–13: Luxembourg (data ready) or Geneva (ally ready).
3. Decide whether the About page carries your name and your host organisation's disclosure now or after the first collaborator joins.
4. Choose the form provider (Formspree or Tally) and point the domain, both under 30 minutes.
5. Confirm the beam encoding: height = stipend, cap colour = kind of place. The alternative is cap
   colour = response status, which is truer to the wedge but shows one colour until replies arrive.
6. Approve the sourcing policy, in particular that jobsin.brussels and Idealist are permanently out
   of scope because their terms forbid automated collection, and that Google geocoding is
   disqualified because its terms forbid redistributing coordinates.
