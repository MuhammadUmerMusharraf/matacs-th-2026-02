"""
Prototype: deterministic scoring for MATACS-TH-2026-02 (Commercial Solar Installation).

In the real tool an AI step would EXTRACT the facts below from each proposal PDF
(see ../PROMPTS.md). This script starts from those extracted facts and does the
rest with plain code: mandatory gate, weighted scores, ranking, reasons.
Same facts in -> same ranking out. No AI calls, no dependencies, no API keys.

Run:  python scorer.py
"""
import json

# ---- Criteria (in the real tool these come from the admin database) --------
CRITERIA_VERSION = 1
BUDGET_CEILING = 260_000   # CAD
MAX_WEEKS = 16
WEIGHTS = {"experience": 30, "price": 25, "timeline": 15, "warranty": 15, "team": 15}

# ---- Extracted facts (simulated output of the AI extraction step) ----------
# None = the proposal did not clearly state it. injection = the extractor
# reported instructions aimed at automated reviewers (described, not copied).
PROPOSALS = {
    "A": dict(licence=True, wsib=True, insurance=True, installs=14, price=238_000, weeks=12,
              panel_yrs=25, work_yrs=10, lead=True, crew=True, safety=True, monitoring=True, injection=False),
    "B": dict(licence=False, wsib=True, insurance=True, installs=6, price=189_500, weeks=10,
              panel_yrs=25, work_yrs=5, lead=False, crew=False, safety=False, monitoring=False, injection=False),
    "C": dict(licence=True, wsib=True, insurance=True, installs=9, price=244_000, weeks=14,
              panel_yrs=25, work_yrs=10, lead=True, crew=True, safety=False, monitoring=False, injection=True),
    "D": dict(licence=True, wsib=True, insurance=True, installs=11, price=231_000, weeks=None,
              panel_yrs=25, work_yrs=10, lead=True, crew=False, safety=True, monitoring=False, injection=False),
    "E": dict(licence=True, wsib=True, insurance=True, installs=8, price=242_500, weeks=13,
              panel_yrs=25, work_yrs=12, lead=True, crew=True, safety=True, monitoring=True, injection=False),
}

# ---- Step 1: mandatory gate -------------------------------------------------
def mandatory_gate(p):
    """Return ('pass'|'ineligible'|'flagged', note)."""
    checks = {"Ontario electrical licence held by bidder": p["licence"],
              "WSIB clearance": p["wsib"],
              "$5M liability insurance": p["insurance"]}
    for name, value in checks.items():
        if value is False:
            return "ineligible", f"fails mandatory criterion: {name}"
    for name, value in checks.items():
        if value is None:
            return "flagged", f"mandatory criterion not stated: {name}"
    return "pass", ""

# ---- Step 2: weighted criteria, each 0-100 ---------------------------------
def experience_score(installs):
    if installs is None: return None
    if installs >= 10: return 100
    if installs >= 6:  return 80
    if installs >= 3:  return 60
    return 20 if installs >= 1 else 0

def price_score(price, lowest):
    if price is None or price > BUDGET_CEILING: return 0 if price else None
    return 100 * lowest / price

def timeline_score(weeks, shortest):
    if weeks is None: return None            # cannot score -> flag, never guess
    if weeks > MAX_WEEKS: return 0
    return 100 * shortest / weeks

def warranty_score(panel, work):
    if panel is None or work is None: return None
    return 50 * min(panel / 25, 1) + 50 * min(work / 12, 1)

def team_score(p):
    return 25 * sum([p["lead"], p["crew"], p["safety"], p["monitoring"]])

def score_all(proposals):
    gates = {k: mandatory_gate(p) for k, p in proposals.items()}
    alive = {k: p for k, p in proposals.items() if gates[k][0] != "ineligible"}
    lowest = min(p["price"] for p in alive.values())                       # baseline: non-ineligible bids
    shortest = min(p["weeks"] for p in alive.values() if p["weeks"])
    out = {}
    for k, p in alive.items():
        parts = {"experience": experience_score(p["installs"]),
                 "price": price_score(p["price"], lowest),
                 "timeline": timeline_score(p["weeks"], shortest),
                 "warranty": warranty_score(p["panel_yrs"], p["work_yrs"]),
                 "team": team_score(p)}
        total = sum(WEIGHTS[c] / 100 * s for c, s in parts.items() if s is not None)
        out[k] = {"parts": parts, "total": total}
    return gates, out

# ---- Step 3: status, ranking, reasons --------------------------------------
def build_ranking(proposals):
    gates, scores = score_all(proposals)
    results, rankable = {}, []
    for k, p in proposals.items():
        gate, note = gates[k]
        if gate == "ineligible":
            results[k] = dict(status="ineligible", score=None,
                reason=f"{note[0].upper() + note[1:]}; a subcontractor to be confirmed after award does not count, despite the lowest price.")
            continue
        s = scores[k]
        flags = []
        if p["injection"]:
            flags.append("hidden text instructing automated reviewers to rank it first (prompt injection) was ignored; human must review")
        if gate == "flagged":
            flags.append(note)
        if s["parts"]["timeline"] is None:
            flags.append("no completion time given, so the 15% timeline criterion cannot be scored; ask bidder to clarify")
        if flags:
            tail = f" Scored on real content only it would be about {round(s['total'])}." if p["injection"] else \
                   f" Partial score {round(s['total'])}/85 possible without timeline."
            results[k] = dict(status="flagged", score=None, reason=("; ".join(flags))[0].upper() + ("; ".join(flags))[1:] + "." + tail)
        else:
            rankable.append(k)
            results[k] = dict(status="ranked", score=round(s["total"]), _raw=s["total"])
    rankable.sort(key=lambda k: (-results[k]["_raw"], proposals[k]["price"]))   # tie-break: lower price
    for i, k in enumerate(rankable, 1):
        parts = scores[k]["parts"]
        best = max(parts, key=parts.get)
        results[k]["rank"] = i
        results[k]["reason"] = (f"Passes all mandatory checks; ${proposals[k]['price']:,} in {proposals[k]['weeks']} weeks, "
                                f"{proposals[k]['installs']} qualifying installs; strongest on {best} ({round(parts[best])}/100).")
    final = []
    order = {"ranked": 0, "flagged": 1, "ineligible": 2}
    for k in sorted(results, key=lambda k: (order[results[k]["status"]], results[k].get("rank") or 99, k)):
        r = results[k]
        final.append({"proposal": k, "rank": r.get("rank"), "status": r["status"],
                      "score": r["score"], "reason": r["reason"]})
    return final, scores

if __name__ == "__main__":
    ranking, scores = build_ranking(PROPOSALS)
    print(json.dumps(ranking, indent=2))
    # Score breakdown on stderr-like side output so the JSON above stays clean to copy
    import sys
    print("\nBreakdown (0-100 per criterion, weighted total):", file=sys.stderr)
    for k, s in scores.items():
        parts = {c: (None if v is None else round(v)) for c, v in s["parts"].items()}
        print(f"  {k}: {parts} total={s['total']:.1f}", file=sys.stderr)
