# Write-up: AI Proposal Triage (MATACS-TH-2026-02)

## The flow in short

1. Admin criteria are stored as versioned data (never hard-coded).
2. Reviewer uploads PDFs and picks a category; the system loads that category's current criteria version.
3. Text is extracted from each PDF (OCR if scanned).
4. **AI** reads each proposal and returns structured facts with an evidence quote for each fact.
5. Code checks the AI output (valid format, every quote really appears in the proposal).
6. Code applies the mandatory pass/fail gates.
7. Code calculates weighted scores and ranks.
8. **AI** writes a one-line reason for each position from the already-calculated numbers.
9. A human reviews, can override, then makes the award decision.

See `diagram/flow.png`.

## 1. AI vs. rules

**AI is used for reading, not judging.** Proposals are free text written in different styles, so extracting "14 installs", "12 weeks" or "licence held by a subcontractor, to be confirmed" is a language task. Rules are poor at that. The AI also writes the short reason sentence.

**Plain code is used for everything that decides a result:** the pass/fail gates, the weights, the score formulas, the ranking and the status. These must be exact, identical on every run, and editable by an admin. The line is: *AI turns text into facts; code turns facts into decisions.*

## 2. Consistency and explainability

- The AI never produces a score. It only extracts facts, at temperature 0, with a fixed JSON format.
- Scores come from written formulas (e.g. price = weight × lowest eligible price ÷ this price; experience uses fixed tiers). Same facts + same criteria version = same score.
- **Same proposals ranked twice?** The scoring and ranking are identical. The extraction step could differ slightly in rare cases, so extracted facts are saved per proposal and reused on a re-rank instead of calling the AI again. Re-extraction only happens when the reviewer asks for it.
- **Why a proposal ranked where it did:** the reviewer sees a table of points per criterion, and each extracted fact is shown next to its evidence quote and page number. Clicking a fact shows the exact sentence it came from.

## 3. Human in the loop

- **Review points:** (a) any flagged or unclear proposal must be resolved by a person before it can be ranked; (b) the reviewer sees the full ranking with evidence and may correct a fact or override a status or score, always with a written reason; (c) the human makes the final award, outside the tool. The tool only recommends.
- **Audit log (per run):** who uploaded what; file hashes; criteria version; prompt version and model name; raw AI output; validation results; every score by criterion; final ranking; every override (who, when, old value, new value, reason); and the final decision.

## 4. Changing criteria

Criteria are versioned. An edit creates version N+1 and never changes version N, so old results stay explainable.

- Old scores keep showing "scored under v1".
- If the edit changes only weights or formulas, the saved facts are reused and proposals are re-scored by code. This is fast and free.
- If the edit adds or changes a criterion that needs new facts, only that new fact is extracted again.
- The reviewer sees a banner "criteria changed since scoring" and chooses to re-score. Nothing is re-ranked silently, and both versions are kept for audit.
- Weighted criteria must still total 100%, otherwise the admin screen refuses to save.

## 5. Risks and safeguards

| Risk | Safeguard |
|---|---|
| **Wrong extraction** (misread number, wrong unit) | Evidence quote required for each fact; code checks the quote exists in the text and values are in a sensible range; reviewer sees the evidence. |
| **Made-up facts** | Prompt says "not stated" instead of guessing; missing facts get zero or a flag, never an assumed value. |
| **Manipulation (prompt injection)** | Proposal text is treated as data only. The prompt tells the AI to report instructions aimed at reviewers, not obey them. Code never lets text change a score, so a hidden "rank me first" cannot move the result. The proposal is flagged for a human. |
| **Bias** (favouring polished writing or big firms) | Scoring uses facts only (numbers, yes/no items), not tone or length. Company names are not used in scoring. Humans review the result. |
| **Cost** | One AI call per proposal, with facts cached and reused on re-score. Scoring is free code. |
| **Unclear or missing info** | Gate "unclear" goes to a person, not silently pass or fail. |

## How the sample set was handled

- **A:** Rank 1 (90.5). Strongest on experience, with good price, timeline and team.
- **E:** Rank 2 (80.4). Best warranty and a full team plan, but fewer installs than A.
- **D:** Rank 3 (71.8). Lowest price but no schedule given, so zero timeline points. I assumed a missing schedule is a scoring gap, not a failed gate, because the brief makes only the licence and WSIB/insurance mandatory. The reviewer is prompted to ask for a completion time.
- **C:** Flagged, not ranked. It contains a hidden instruction for automated systems. It is not trusted and not obeyed; a clean shadow score (about 70) is shown to the reviewer only. Also, "since 2020" may include installs older than 5 years, so the experience count needs checking.
- **B:** Ineligible. The electrical licence is deferred to an unnamed subcontractor, so the bidder does not hold it. Its low price does not matter because the gate is pass/fail.

## Assumptions

- Tier cut-offs and "full marks" benchmarks (e.g. 12 weeks workmanship warranty) are example admin settings, stored in the criteria data and editable.
- Price uses the lowest price among clean, eligible bidders as the baseline, so a flagged proposal cannot shift others' scores.
