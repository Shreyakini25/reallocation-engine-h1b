# The H-1B Sponsorship Reallocation Engine

A reallocation engine that recommends how a candidate on OPT/H-1B should
allocate limited job-search effort (in hours/week, moved concretely from
one employer to another) across employers, based on their historical H-1B
sponsorship track record — with an explicit uncertainty estimate, a
documented bias audit, causal honesty about what the signal can and can't
claim, adversarial stress-testing, and a hard-stop gate that blocks the
engine from ever acting on a candidate's behalf.

Built for INFO 7375 — Computational Skepticism for AI. Primary domain-text
anchor: *The Reallocation Engine*, Ch. 7, "Who Sponsors: The 80 Days
Sponsorship Scorer" (Unknown-≠-Avoid discipline, approval-rate-as-signal
concept — see `reports/Kini_Shreya_ReallocationEngine.md` for the full,
honest account of what is and isn't implemented from that chapter).
Secondary methodology anchor: *Computational Skepticism for AI*, Ch. 7, 9,
12 (fairness metrics, delegation, accountability).

**Python version:** developed and tested on Python 3.12.

## Data

`data/SEC_DOL_H1b_data_mapped.csv` — real employer-level data joining
SEC/startup metadata (funding, incorporation year) with DOL H-1B LCA
approval/denial counts. 30,369 companies; 1,557 have any H-1B filing on
record (94.9% do not — see the GIGO gate finding below, which is the
headline result of this project). See `DATA_SOURCE.md` for full
provenance disclosure.

## How to run

Run all commands from the **repo root** (not from inside `src/`) — the
scripts use paths relative to the root.

```bash
pip install -r requirements.txt
./run_all.sh
```

Or run each step individually, in this order (the GIGO gate is now
**enforced**, not just reported — `engine.py` will refuse to run if the
gate finds a structural problem):

```bash
python3 src/gigo_gate.py             # Component 2 — data validation (standalone report)
python3 src/engine.py                # Component 1 — core engine; calls the gate itself, halts if blocked
python3 src/bias_audit.py            # Component 3 — fairness metrics + sampling-bias coverage
python3 src/explainability.py        # Component 4 — explanation + its critique
python3 src/causal_analysis.py       # Component 5 — Pearl's three rungs
python3 src/adversarial.py           # Component 6 — fragility test
python3 src/delegation_hardstop.py   # Component 7 — delegation map + hard-stop
python3 src/make_uncertainty_figure.py  # regenerates figures/uncertainty_bands.png
```

`engine.py` must run before `bias_audit.py`, `explainability.py`,
`causal_analysis.py`, and `adversarial.py` — they read
`data/engine_output.csv`, which `engine.py` generates.

## Repo structure

```
data/                        real input data + generated engine output
src/
  gigo_gate.py                Component 2 (enforced BLOCK/FLAG gate)
  engine.py                   Component 1 (tiering + concrete reallocation quantity)
  bias_audit.py                Component 3 (fairness metrics + coverage quantification)
  explainability.py            Component 4
  causal_analysis.py           Component 5
  adversarial.py                Component 6
  delegation_hardstop.py       Component 7 (9-row delegation map)
  make_uncertainty_figure.py   regenerates the uncertainty figure from real data
figures/
  uncertainty_bands.png        Wilson-interval visualization (12 contrasting employers)
reports/
  Kini_Shreya_ReallocationEngine.md   full writeup, all seven components + AI disclosure
FRICTIONAL_JOURNAL.md          required prediction + reflection
AI_USE_DISCLOSURE.md           required AI use disclosure (also embedded in the report)
DATA_SOURCE.md                 data provenance disclosure
requirements.txt
run_all.sh
```

## Headline findings

- **94.9%** of employers in this file have no H-1B filing on record at
  all — the engine routes these to an explicit INSUFFICIENT_EVIDENCE
  bucket rather than defaulting to "risky."
- **The real sampling bias, quantified:** young companies have H-1B
  evidence at **1.50%** vs. established companies at **5.25%** — a
  young company is roughly 3.4× less likely to have any record at all.
  This is the actual leverage point, not the smaller gap among the
  minority that gets scored.
- **Demographic parity gap of 0.104** between established and young
  companies in who gets a PRIORITIZE recommendation, among that scored
  minority.
- The engine's causal reasoning verdict: **it reallocates substantially on
  correlation dressed as causation**, and is scoped accordingly (an
  informative prior, never a guarantee).
- **54.6%** of low-filing-volume employers flip recommendation tier from
  a single additional denial — a realistic data correction, not an
  engineered attack. The most surprising finding of the project (see
  `FRICTIONAL_JOURNAL.md`).
- **190 normalized-name duplicate groups (380 rows)** found in the GIGO
  gate that exact-match checking missed — flagged for human review, not
  auto-merged, per Ch. 7's own entity-resolution rule.
- Hard-stop gate: the engine cannot submit applications, message
  employers, or act on the candidate's behalf under any circumstance.
