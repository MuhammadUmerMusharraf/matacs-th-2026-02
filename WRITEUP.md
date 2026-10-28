# Write-up: AI Proposal Triage (MATACS-TH-2026-02)

Flow diagram: `diagram/process-flow.png`. Proposals are referred to by letter (A-E).

## How the sample set ranks
Rank 1 is **A** (98), rank 2 is **E** (92). **B** is ineligible (no own licence). **C** is flagged (hidden instruction aimed at AI reviewers). **D** is flagged (no completion time given). See `ranking.json`.

Scoring rules used (all in code): Price = lowest eligible price / bid price. Timeline = shortest weeks / bid weeks. Experience bands: 10+ installs = 100, 6-9 = 80, 3-5 = 60. Warranty = 50% panel (25 yrs = full) + 50% workmanship (12 yrs = full). Team = 25 points each for named lead, crew size, safety plan, monitoring plan.

## 1. AI vs. rules
**AI is used for one job: reading messy proposal text and extracting facts with a quote as evidence.** Proposals are free text in different formats, so rules alone cannot read them.
**Everything else is plain code:** file checks, loading criteria, the mandatory pass/fail gate, score formulas, ranking, and the audit log. These must be exact and repeatable, and AI can make arithmetic or judgement mistakes. The line is: *AI reads, code decides.*

## 2. Consistency and explainability
- AI only outputs facts (e.g. price = 238000, workmanship = 10 years), never scores. Scores come from fixed formulas, so the same facts always give the same score.
- Extraction runs at temperature 0 with a fixed model version and a schema-constrained output. Small wording differences could still occasionally change an extracted value, so the extraction is saved: re-ranking reuses the saved extraction instead of calling the AI again. With the saved extraction, the ranking is identical every time.
- Every score shows its quote and formula on the review screen: "Price 97/100: $238,000 vs lowest eligible $231,000 ('Our total price is...')". A non-technical reviewer can click any number and see where it came from.

## 3. Human in the loop
- The reviewer sees all proposals, including ineligible and flagged ones with the reason. They can confirm the ranking, override a status or score (reason is required), or ask a bidder to clarify (e.g. D's schedule).
- A human, not the tool, makes the final award decision. The tool only recommends.
- Audit log per run: who uploaded, file hash, criteria version, prompt version, model name, raw AI output, validation results, scores, flags, every override with user/time/reason, and the final decision.

## 4. Changing criteria
Each run stores the **criteria version** it used. Editing criteria creates a new version; old results are never silently changed. Old results are marked "scored under version 3 (outdated)". The reviewer can click "re-score", which re-runs only the scoring step in code on the saved extractions (cheap, no new AI call) and creates a new, separate result. If a new criterion needs a fact that was not extracted before, only the extraction step is re-run. Admin edits are logged with who/when, and results already used for an award are locked.

## 5. Risks
| Risk | Safeguard |
|---|---|
| Wrong extraction | Each fact needs an exact quote; code checks the quote exists in the text; reviewer sees quotes; unclear = null and flagged |
| Made-up facts | "Never guess" rule; missing = null; null on a mandatory criterion means flagged, not pass |
| Manipulation / prompt injection (C) | Proposal text is wrapped as data; injected sentences are reported and ignored; AI never produces the score, so it cannot give "full marks"; proposal flagged for a human |
| Misleading claims (B's licence, or a fake licence number) | Bidder must hold the licence itself; subcontractor "to be confirmed" fails. AI cannot verify licence numbers, so the human checks the number in the official ESA/ECRA register |
| Bias | Criteria and weights come from the admin, not the AI; company name and location are not scoring inputs; the same formulas apply to everyone; reviewer can see and override |
| Missing information (D) | Not guessed and not scored as zero: flagged, reviewer asks for clarification |
| Scanned/unreadable PDFs | File check and OCR; if text is poor, flag it |
| Cost and privacy | One extraction call per proposal, cached; scoring costs no AI calls; PDF size limit; no personal data sent beyond the proposal; vendor data-retention settings checked |
| Over-trusting the ranking | UI labels it "recommendation"; human confirms every run |

## Assumptions
- "Last 5 years" counted from 2026, so installs since 2021. C's installs "since 2020" may include one before the window, so a human should check.
- Only A-E were scored; weights are those in the admin criteria.
