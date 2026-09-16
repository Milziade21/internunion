# The employer email series

Four emails, sent from the project address to an organisation's **public** contact point (its EU
Transparency Register contact, or the address on its own contact page). Never to a named individual's
personal address. The whole series is published here so that any organisation can read, in advance,
exactly what it will receive and what will be published about it.

**Tone rule, absolute.** We describe, we never accuse. Every sentence must survive being read aloud
by the recipient's communications director. Praise is specific; criticism is a dated fact. We never
write "refused", only "did not disclose".

**Cadence.** Day 0, day 14, day 28, then the state flips on day 30. Each email is short enough to
read on a phone. The subject line never changes across the series, so it threads.

**Mail merge fields:** `{{org}}`, `{{city}}`, `{{sent_date}}`, `{{deadline_date}}`, `{{org_url}}`,
`{{questionnaire_url}}`, `{{ledger_url}}`.

---

## Email 1 — day 0: the ask

**Subject:** Internship pay and conditions at {{org}} — a public transparency record

> Dear {{org}} team,
>
> internunion is an open-data project that records what interns in {{city}} are paid against what it
> costs to live there. The dataset is public, the method is published in full, and every figure is
> traceable to its source.
>
> We are asking every organisation we list the same eight questions. They take about five minutes and
> the exact wording is published in advance here: {{questionnaire_url}}
>
> 1. Does your organisation host interns or trainees in {{city}}?
> 2. Under which contract type (professional immersion agreement, academic convention, employment
>    contract, other)?
> 3. Are internships paid, and what is the gross monthly stipend for a full-time trainee?
> 4. Does that meet or exceed the local legal floor?
> 5. What non-cash benefits are provided (transport, meals, housing support)?
> 6. Typical duration and weekly hours.
> 7. Approximately how many trainees per year?
> 8. A contact point we can cite for verification.
>
> Your answer will be published as organisation-level open data. We never publish an individual's
> personal data. If you reply with paid, compliant terms we can verify, your entry is marked
> **verified compliant** and appears above organisations that have not answered.
>
> If we do not hear from you by {{deadline_date}}, your entry will record, factually, that the
> questionnaire was sent on {{sent_date}} and that no reply was received. You can change that at any
> time, including after the date.
>
> With thanks,
> internunion — {{ledger_url}}

---

## Email 2 — day 14: the reminder

**Subject:** (same thread)

> Dear {{org}} team,
>
> A short reminder about the eight questions below. The record for {{org}} currently reads
> "questionnaire sent {{sent_date}}, response pending".
>
> If it is easier, a single line is enough: whether you host trainees, whether they are paid, and the
> monthly amount. We will follow up for the rest.
>
> If your organisation does not host interns at all, telling us so is also useful — we will mark the
> entry accordingly rather than leaving it open.

---

## Email 3 — day 28: last call, with the date

**Subject:** (same thread)

> Dear {{org}} team,
>
> On {{deadline_date}} the public entry for {{org}} will change from "response pending" to
> "did not disclose". That label is a statement about correspondence, not about your organisation's
> conduct: it records that a questionnaire was delivered on {{sent_date}} and that no reply was
> received by {{deadline_date}}.
>
> It can be changed on the day you reply. Organisations also have a standing right of reply: send us
> a statement and we will attach it verbatim to your entry.
>
> The questions are unchanged and published at {{questionnaire_url}}.

---

## Email 4 — after a reply: confirmation

**Subject:** (same thread)

> Dear {{org}} team,
>
> Thank you. We have recorded the following for {{org}} and it is now public at {{org_url}}:
>
> - Contract type: …
> - Paid: … Monthly stipend: €…
> - Benefits: …
> - Status: **verified compliant** / **disclosed sub-standard**
>
> Please check it. If anything is wrong we will correct it within 72 hours — accuracy matters more to
> us than being first.
>
> If your terms change, tell us and we will update the entry and the date.

---

## The self-reported criteria shown on the map

Beyond the stipend, an organisation may self-report against these criteria. Each is shown on its entry
as **yes / no / not answered**, always labelled as self-reported and dated. We do not audit them; the
point is that the organisation put its answer on the public record.

1. Every trainee has a written agreement stating pay before they start.
2. The stipend meets or exceeds the local legal floor.
3. Public transport is reimbursed.
4. Trainees are covered by health and accident insurance.
5. Trainees have a named supervisor and a written training plan.
6. Trainees are not used to replace a staff post.
7. Recruitment is open and advertised publicly, not by internal referral only.
8. Trainees may apply for internal vacancies on the same terms as external candidates.
9. There is a route to a paid contract after the traineeship.
10. Pay and conditions are the same regardless of nationality or residence status.

## Rules for running the series

- Send from the project address, never a personal one. Keep contacts in the git-ignored local file.
- Log `contacted_on` in the dataset on the day of sending; the state flip on day 30 needs a second
  maintainer's approval on the pull request.
- Archive every reply locally; publish only an organisation-level summary.
- If an organisation asks to be removed from the list: we keep the entry, because the register is
  public and the fact is public, but we attach their statement verbatim and correct any error at once.
- If an organisation replies angrily: answer once, factually, offering the right of reply. Do not argue.
