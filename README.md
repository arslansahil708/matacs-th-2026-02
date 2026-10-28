# MATACS-TH-2026-02: AI Proposal Triage Design

- **Name:** Muhammad Arslan
- **Reference:** MATACS-TH-2026-02
- **Time actually spent:** About 30 minutes

## Files

- [WRITEUP.md](WRITEUP.md): answers to the five questions
- [diagram/flow.png](diagram/flow.png): final process flow diagram (AI steps, rule/code steps, human checkpoints)
- [diagram/flow.dot](diagram/flow.dot): an earlier, more complex version of the diagram generated with Claude; kept for reference only
- [PROMPTS.md](PROMPTS.md): extraction prompt and reason prompt, as I would send them
- [ranking.json](ranking.json): expected ranking of proposals A to E
- [prototype/](prototype/): small script that runs the scoring rules on extracted facts (`python3 prototype/score.py`)

## How I used AI tools

I used ChatGPT and Claude while designing the flow, the prompts and the scoring approach.

**Where I disagreed with or corrected the AI:** I was not satisfied with the diagram created by Claude. I used ChatGPT to create a simpler and clearer concept diagram that was easier to understand and better matched my requirements. While reviewing it, I also noticed that three code steps (loading criteria, extracting PDF text, calculating the weighted score) were coloured as AI steps. This contradicted my design, where AI never scores, so I corrected them to rule/code steps.
