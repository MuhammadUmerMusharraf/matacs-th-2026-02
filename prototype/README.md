# Prototype: deterministic scorer (optional, extra credit)

A small script that shows the "code decides" half of the design. It uses **only the Python standard library**, needs no API key, and makes no AI calls.

## Run
```
python scorer.py
```
Needs Python 3.8+. The ranking JSON (same format as `../ranking.json`) is printed to the terminal. A score breakdown per criterion is printed separately (stderr), so you can save only the JSON with:
```
python scorer.py > output.json
```

## What it does
1. Starts from the **extracted facts** for proposals A-E. In the real tool, the AI extraction prompt in `../PROMPTS.md` would produce these; here they are typed in so the script runs offline. Proposal text is not copied into this repo.
2. **Mandatory gate:** licence held by the bidder, WSIB clearance, $5M insurance. A clear "no" means `ineligible`; a missing answer means `flagged`.
3. **Weighted scores (0-100 each):** Experience 30% (bands by number of installs), Price 25% (lowest bid / this bid), Timeline 15% (shortest weeks / this bid's weeks), Warranty 15% (panel + workmanship years), Team 15% (named lead, crew size, safety plan, monitoring plan, 25 points each).
4. **Edge cases:**
   - B: licence is via a subcontractor to be confirmed -> `ineligible`.
   - C: extractor reported an instruction aimed at automated reviewers -> `flagged`, ignored for scoring, human review.
   - D: no completion time -> timeline not scored, `flagged`, ask bidder to clarify.
5. **Ranks** only clean proposals (ties go to the lower price) and prints the result as JSON.

## Changing the rules
Edit `WEIGHTS`, `BUDGET_CEILING` or `MAX_WEEKS` at the top of `scorer.py`, or the facts in `PROPOSALS`, and run again. The same input always gives the same output.
