# Validation Report — The H-1B Sponsorship Reallocation Engine

**Course:** INFO 7375 — Computational Skepticism for AI
**Assignment:** The Reallocation Engine, Audited
**Domain:** People/time — reallocating a candidate's own limited job-search effort (hours/week) across employers by H-1B sponsorship reliability. *(Corrected from an earlier draft's "Access/eligibility" label: the resource being moved is the candidate's own time, not something being allocated across different people, which is what the Access/eligibility category describes.)*
**Anchor text:** Brown, *The Reallocation Engine*, Ch. 7 — "Who Sponsors: The 80 Days Sponsorship Scorer" (`chapters/07-who-sponsors-the-80-days-sponsorship-scorer.md`) — primary anchor. *Honest correction:* this project adapts the chapter's **Unknown-≠-Avoid discipline** (a true absence of filings is not the same as a name-match join artifact, and neither is the same as evidence the company doesn't sponsor) and its **approval-rate-as-signal concept**, using a Wilson-lower-bound-adjusted approval rate as a conservative proxy. **It does NOT implement the chapter's full four-term weighted composite** (LCA filing rate × 0.40 + approval rate × 0.30 + funding recency × 0.20 + company-size × 0.10) — an earlier draft of this report incorrectly claimed it did. The underlying data has the columns needed to build the full composite (funding recency, company size), but `engine.py` currently scores on approval-rate/Wilson-bound alone; combining all four terms is disclosed here as a named, undone extension, not a silently patched one. *Note: the source is a Markdown chapter file, not a paginated edition, so the chapter and file path are cited in place of a page number.* Secondary methodology framework: Brown, *Computational Skepticism for AI*, Ch. 7, 9, 12 (fairness metrics, delegation, accountability).
**Data:** `SEC_DOL_H1b_data_mapped.csv` — real, employer-level data joining SEC/startup metadata with DOL H-1B LCA approval/denial history (n=30,369 companies; 1,557 with any H-1B filing on record)

---

## 1. The Working Tool (Component 1)

**Objective, stated plainly:** recommend more of a candidate's limited job-search effort toward employers with strong, statistically credible evidence of H-1B sponsorship follow-through, and less toward employers with weak evidence — while explicitly separating "weak evidence" from "no evidence" rather than collapsing them.

**What the objective leaves out:** job fit, career growth, interview likelihood, and — critically — it rewards employers who sponsor *often*, which mechanically favors large filers over small employers who sponsor everyone who asks but have filed only a handful of times (see Component 5).

**How it works:** each employer's historical approval rate is converted to a 95% Wilson score interval (not a bare point estimate), and tiered by the *lower bound* of that interval:

| Tier | Rule | Count (of 1,557 scored) |
|---|---|---|
| PRIORITIZE | Wilson lower bound ≥ 0.70 | 771 |
| CONSIDER | Wilson lower bound in [0.40, 0.70) | 446 |
| DEPRIORITIZE | Wilson lower bound < 0.40 | 23 |
| LOW-CONFIDENCE | fewer than 3 total filings | 317 |
| INSUFFICIENT_EVIDENCE | no H-1B filing on record at all | 28,812 |

This five-tier split is a direct application of Ch. 7's central warning: *"the most common misread of this system is treating Unknown as Avoid."* This engine keeps that distinction structural rather than cosmetic — INSUFFICIENT_EVIDENCE is never collapsed into DEPRIORITIZE, because silence (no filing on record) and negative evidence (a demonstrated non-sponsor) are different claims, and only the second one justifies actively skipping a company.

**The concrete reallocation (the assignment's actual requirement — move quantity Q from A to B, not just a ranked list):** given a candidate's own shortlist and a weekly effort budget (your-input, e.g. 20 hours/week), the engine computes a baseline (equal hours across the shortlist) versus a recommended allocation (hours proportional to each employer's Wilson lower bound), and outputs the literal move:

```
Shortlist: Juniper Networks, Confluent, LinkedIn, 3DEO Inc, Accela Inc
Baseline: 4.0 hours/week each (20 total)
Recommended move: move 1.0 hours/week from 3DEO INC to JUNIPER NETWORKS INC
Uncertainty: JUNIPER's recommended hours range from 4.97–4.99 hrs depending on
             which end of its Wilson interval is true (corrected from an
             earlier draft that displayed 5.0–5.0 due to overly coarse
             rounding, which visually erased a real, if narrow, interval);
             3DEO's from 2.55–4.45 hrs, reflecting its much wider interval
             at n=4 filings.
```

**Two edge-case bugs found by deliberate testing and fixed:**
1. **GIGO gate crashed instead of blocking cleanly** when a required column was missing (e.g. dropping `company_name` or `Approval_Rate` raised a raw `KeyError`, not a controlled gate failure). Fixed by returning immediately once missing columns are detected, before any code touches them. Verified: all four tested columns (`company_name`, `Total Approvals`, `company_age_years`, `Approval_Rate`) now correctly report `passed: False` with a named reason instead of crashing.
2. **Unknown shortlist employers were silently dropped**, redirecting the candidate's entire effort budget to whichever real company happened to also be on the list — with an all-unknown shortlist, this crashed with an uncontrolled `ZeroDivisionError`. Fixed with explicit shortlist validation: any unmatched or unscored name now raises a clear, named error instead of silently vanishing or crashing. Verified against three cases (one fake name, all fake names, empty shortlist).

Full worked output: `data/reallocation_example.csv`. Run with `python3 src/engine.py`.

Full runnable output: `data/engine_output.csv` (30,369 rows). Run with `python3 src/engine.py`.

---

## 2. Data Validation & the GIGO Gate (Component 2)

Five named hidden assumptions were tested against the real file (`src/gigo_gate.py`), **plus one additional entity-resolution assumption found on rechecking (below).** The gate has two enforcement levels, not one: **BLOCK** (structurally broken data — missing required columns, null company names, negative filing counts — halts the run entirely, verified by deliberately corrupting a test copy of the data and confirming `engine.py` refuses to run) and **FLAG** (a real, disclosed limitation that is routed around, not silently fixed).

1. **"No H-1B record" is treated as one category, but isn't.** 28,812 of 30,369 rows (**94.9%**) have zero H-1B signal. This conflates "never needed to sponsor," "too new to have filed," and possible join gaps. Ch. 7 names exactly this split — a true absence of filings versus a name-match artifact from the entity-resolution join — and prescribes reading a join-coverage number before trusting either. **Honest limitation, disclosed rather than resolved:** this project does not run the chapter's own join-coverage tooling (`validate-h1b-join-sample.py`, `audit-sec-dol-h1b-data.py`) against this specific file, so the 94.9% figure is reported as one undifferentiated bucket — it is not yet split into "true absence" vs. "failed name match." **Gate response: FLAG — these rows are never scored, never defaulted to a risk label — routed to an explicit INSUFFICIENT_EVIDENCE bucket** — which correctly avoids the chapter's named misread (Unknown-as-Avoid) even without yet separating the two causes of Unknown from each other.
2. **company_age_years completeness** — missing for 18.6% of rows (5,634), which matters directly because it's the variable the bias audit depends on. Bias audit reported on the age-known subset only, and says so. **Gate response: FLAG.**
3. **Approval_Rate on small denominators** — 20.4% of employers with any H-1B data (317 of 1,557) have fewer than 3 total filings, meaning a bare rate is one data point away from being 0% or 100%. **Gate response: FLAG — Wilson interval, not raw rate; LOW-CONFIDENCE tier below n=3.**
4a. **Exact-match duplicate employers** — none found (0 duplicate company_name rows). Passes clean.
4b. **Normalized-name duplicates — a real gap the exact-match check missed.** Stripping punctuation and common legal suffixes (Inc/LLC/Corp/Ltd/LLP/Co) and re-checking surfaces **190 groups covering 380 rows** where the same apparent company may appear under name variants (e.g. "Acme Inc" vs. "Acme LLC"). **Gate response: FLAG, not auto-merged** — per Ch. 7's own rule that entity resolution must never enable fuzzy matching without a human sign-off, these are reported as candidates for review, not silently combined. If real, this would understate the true filing volume (and thus Wilson confidence) for the affected employers.
5. **Measurement-protocol stability** — the file has no reporting-period or extraction-date column, so we cannot confirm all figures are from the same DOL disclosure vintage. **Gate response: FLAG — a disclosed, unresolved limitation, not a fixed one.**

**GATE_STANDARD (the checkable rule, now actually enforced):** the run is BLOCKED if the schema is broken (missing required columns, null company names, negative filing counts); otherwise, a row may be *scored* only if it has ≥1 actual H-1B filing on record, and everything else is flagged, never dropped and never defaulted to "risky." `engine.py` now imports and calls this gate before scoring anything — verified by deliberately injecting a negative filing count and a null company name into a test copy and confirming the gate correctly reports `passed: False` with both reasons named. Run with `python3 src/gigo_gate.py`.

---

## 3. Bias Audit — data → output (Component 3)

**Anchored to *Computational Skepticism for AI*, Ch. 7 (fairness metrics methodology).** Where bias enters: the *sampling* stage. The DOL disclosure file only contains employers who have actually filed an H-1B petition — young, small, or capital-constrained employers who simply haven't had occasion to file yet are structurally invisible to the engine, not because they're worse sponsors.

**Groups (grounded in the real data):** ESTABLISHED (company_age_years ≥ 10, n=357) vs. YOUNG (company_age_years ≤ 4, n=54), restricted to employers with ≥3 filings for the metrics below — **but see the coverage numbers first**, which are measured on the full population, not this restricted subset.

**Evidence coverage by group (the sampling bias itself, quantified — this was missing from an earlier draft):**
- YOUNG companies (n=6,330 at this age band): **1.50%** have any H-1B evidence at all (95 of 6,330).
- ESTABLISHED companies (n=8,179): **5.25%** have any H-1B evidence at all (429 of 8,179).
- **Gap: 3.74 percentage points — a young company is roughly 3.4× less likely to have any H-1B record at all.** This is the real leverage point the demographic-parity/equalized-odds metrics below cannot see, because those metrics only run on employers who already made it into the scored population.

**Demographic parity** — P(recommend PRIORITIZE | group), among the scored subset only:
- ESTABLISHED: 0.641
- YOUNG: 0.537
- **Gap: 0.104** — established companies get the favorable recommendation about 10 percentage points more often, among the small minority of each group that gets scored at all.

**Equalized odds** — TPR/FPR by group:
- ESTABLISHED: TPR 0.647, FPR 0.0
- YOUNG: TPR 0.537, FPR undefined (no Y=0 cases in this small subgroup — itself a small-n artifact worth flagging, not a clean zero)

**Calibration check** across score-quartile bins: within this scored population, actual reliability (Y) tracks the score similarly in both groups (mostly ~0.97–1.0 in every bin) — **but this is a weaker result than it looks**, because Y and the engine's score are both derived from the same historical counts with no independent holdout (see the honest limitation below).

**Two competing fairness definitions in tension:** satisfying demographic parity here would mean *recommending young and established companies at equal rates regardless of their different observed reliability* — a defensible "structural redress" stance given that young companies are underrepresented for reasons outside their control. Satisfying equalized odds/calibration instead accepts the current gap as reflecting genuine (if noisy) reliability differences. **Defended choice:** we prioritize calibration/informativeness for the *scored* population (a candidate deserves an honest signal about the specific employer), but treat the deeper unfairness — the coverage gap quantified above — as the real leverage point.

**Highest-leverage intervention point, stated explicitly:** improve entity resolution and data coverage upstream (e.g. resolving the 190 normalized-name duplicate groups flagged in the GIGO gate, and pursuing the chapter's own join-coverage tooling), not adjusting recommendation thresholds downstream. Merely labeling missing employers as INSUFFICIENT_EVIDENCE prevents harm from a false negative signal, but it does not repair the underlying exclusion — a young company that's actually a reliable sponsor stays invisible either way.

**Honest limitation:** Y (ground truth: point_rate ≥ 0.70) and Ŷ (Wilson lower bound ≥ 0.70) are both computed from the *same* historical filing counts — there is no independent, temporally-held-out outcome to validate against, since the file has no reporting-period field (GIGO gate, Assumption 5). The near-perfect calibration numbers above are partly an artifact of this overlap, not proof of a well-validated model. Run with `python3 src/bias_audit.py`.

---

## 4. Explainability & Its Critique (Component 4)

The engine's logic is a transparent threshold rule, so its "explanation" is an exact decomposition (filings, rate, Wilson bound vs. threshold) rather than an approximation — see `src/explainability.py`.

**The critique, a real case:** Deloitte Tax LLP scores PRIORITIZE at 99.3% approval (Wilson lower bound 98.8%) — a confident, *factually correct* recommendation. But `top_job_titles_sponsored` shows the filing history is almost entirely Tax-track roles (Tax Consultant, Tax Senior, Tax Manager, Tax Senior Manager), with only one Software Engineer title mixed in. A candidate targeting a general engineering role would read "PRIORITIZE, 99.3%" and reasonably assume this employer is a safe bet for *their* role — when the evidence is overwhelmingly about a different job function with its own SOC code, wage level, and scrutiny pattern. **The explanation is not wrong. It is silent about what it is actually evidence for.** This is a named, undone fix (re-scoping recommendations to the candidate's target job family), not a silently patched one.

---

## 5. Causal & Counterfactual Reasoning — Pearl's Three Rungs (Component 5)

**Rung 1 (Observation):** contrary to the intuitive story, `total_filed` and `point_rate` are essentially uncorrelated in this data (r = 0.008) — "employers who file more have proven higher rates" is *not* supported linearly. `company_age_years` correlates weakly with `total_filed` (r = 0.137) but not with `point_rate` (r = 0.002).

**Rung 2 (Intervention):** the engine optimizes an observational quantity — historical approval rate for *other* people — not an interventional one (does *this* candidate's probability rise if they apply here). Named confounders: employer size/legal-resource pre-filing selection, role/SOC-code mixture (Component 4's finding), wage-level scrutiny differences, and survivorship (only employers who already chose to sponsor someone appear in the data at all).

**Rung 3 (Counterfactual):** *corrected from an earlier draft, which asked the wrong question.* The earlier version varied Amgen's historical filing count — that changes the observed dataset, not a reallocation action, and doesn't answer what Rung 3 requires. The corrected version: a specific past week, the candidate split a 20-hour budget as 6 hours on Deloitte Tax LLP and 2 hours on Amgen Inc (both PRIORITIZE-tier). **Counterfactual question, stated correctly:** what would have happened had the candidate moved 3 hours from Deloitte Tax to Amgen that week? **Honest answer: this dataset cannot identify that outcome.** It contains employer-level petition counts, not candidate-level applications, interviews, or offers — there is no row representing "this candidate applied here and something happened." Under strong, explicitly unverifiable assumptions (role/SOC comparability — directly undercut by the Deloitte Tax LLP finding; policy stability across years, Assumption 5; exchangeability with the historical applicant population), the historical sponsorship *prior* would have shifted toward Amgen. What cannot be claimed under any assumption set is that the candidate's actual outcome would have differed — that remains genuinely unidentified from employer-level data, and the honest move is to say so rather than invent a number.

**Verdict, stated honestly:** yes, this engine reallocates substantially on correlation dressed as causation. What it can honestly claim: past approval rate with an uncertainty band is a legitimate *prior* to weight research effort by. What it cannot claim: that applying to a PRIORITIZE-tier employer *causes* a materially higher chance of sponsorship for any specific candidate. This distinction is enforced structurally by the hard-stop gate (Component 7) — the engine recommends, it never guarantees, and it never auto-acts. Run with `python3 src/causal_analysis.py`.

---

## 6. Adversarial Robustness & Fragility (Component 6)

**Perturbation:** one additional denial recorded against low-filing-volume employers (3–10 total filings) — a plausible, realistic correction (e.g., a case status updated after this data was pulled), not an engineered attack.

**Result: 267 of 489 tested employers (54.6%) flipped tiers** from a single additional denial. This was a genuinely surprising number — higher than expected going in (see Frictional Journal). A human reviewer glancing at "one more denial out of four filings" would not consider that dramatic, but the tiering reacts sharply in this range. **Mitigation in place:** the LOW-CONFIDENCE tier below n=3 filters the most fragile cases, but this test shows the fragility extends meaningfully past that cutoff — disclosed as an open limitation, not silently patched. Run with `python3 src/adversarial.py`.

---

## 7. Delegation Map + the Hard-Stop Gate (Component 7)

Full delegation map in `src/delegation_hardstop.py`, covering nine components (GIGO gate, tiering, bias-audited group comparison, explainability interpretation, causal-validity judgment, adversarial-response decision, uncertainty communication, data-source/provenance acceptance, and final action) — expanded from an earlier draft that covered only four — with an explicit tool/human split and override point at each. One overclaim corrected: the tiering row's "job-title-mismatch auto-downgrade" is a **proposed, not implemented** override — `engine.py` does not currently apply it automatically, and the map now says so plainly rather than describing behavior that doesn't exist in the code.

**The hard-stop gate:** this engine has no write access to any external system — it cannot submit an application, message an employer, or silently exclude an employer from view. Every one of those actions is BLOCKED by construction, not by a bypassable runtime check. **Why non-negotiable here:** this touches a real, personal, visa-dependent job search; given Components 5 and 6 (weak causal grounding, high fragility at low n), auto-acting on this signal on someone's behalf would be reckless regardless of how much the underlying data improves.

---

## Uncertainty Communication

See `figures/uncertainty_bands.png` — Wilson intervals, not point estimates, for **12 contrasting employers (6 high-filing-volume + 6 at exactly the n=4 boundary)**, chosen to make the same-rate-different-trust point starkly, not literally the "top-15" an earlier draft of this report claimed. The figure is now regenerable from real data — `python3 src/make_uncertainty_figure.py` — closing a reproducibility gap the original version had (no generating script existed). Plain-language summary: **a "99% approval rate" employer with only 4 filings is not nearly as trustworthy as a "99% approval rate" employer with 2,000 filings, even though the two numbers look identical** — the interval width is the honest signal, and it is what the engine's tiering actually uses. **Where not to trust this tool:** any employer in the LOW-CONFIDENCE or INSUFFICIENT_EVIDENCE buckets (a combined 94.9%+ of all employers in the file), and any PRIORITIZE-tier employer whose `top_job_titles_sponsored` doesn't clearly match the candidate's target role.

---

## AI Use Disclosure

**Tool(s) used:** Claude (Anthropic), via claude.ai chat with code execution.

**Portions assisted:** Repo scaffolding; all seven Python modules (GIGO gate,
core engine, bias audit, explainability, causal analysis, adversarial test,
delegation/hard-stop map); the validation report first draft; the DOL LCA
record-layout research.

**How used:** I described the assignment requirements and my domain
background (SAP/IT consulting on OPT, familiarity with H-1B sponsorship
patterns) to Claude, chose the domain and the specific dataset (a real
SEC/DOL-joined H-1B file I already had from a prior course exercise), and
had Claude draft the pipeline component by component, checking real
computed output at each step rather than accepting a written narrative on
faith.

**What I changed:** I directed the fairness-metric anchor and the
group-split choice (company age, since the real data doesn't have a
demographic field to split on). I caught that Claude's initial written
narrative for the causal Rung-1 section asserted "employers who file more
have proven higher approval rates" *before* checking whether the actual
computed correlation supported that — it didn't (r=0.008) — and had that
corrected rather than left as a plausible-sounding but false claim.

**What the AI could not do:** The engine's objective function treats
`total_filed` and `point_rate` as signals of a generic employer's
"reliability" as a sponsor. What Claude's analysis could not supply is the
domain-specific reason those signals mean something different depending on
*business model*, not just filing volume. From my own experience in SAP/IT
consulting placements, a staffing/consulting employer's H-1B approval rate
reflects a fundamentally different sponsorship relationship than a
direct-hire product company's: staffing firms sponsor at high volume partly
because they place workers across many end-clients and can absorb
individual case risk across a large portfolio, while a smaller product
company's identical approval rate reflects a much more concentrated bet on
specific hires. The dataset has no column distinguishing
"staffing/consulting" from "direct-hire" employers, and Claude's analysis,
working only from the columns present, could not have surfaced this
distinction or flagged it as a confound worth naming — I added it as a
scoping note for future work in the causal analysis because it's a real
business-model difference I know from being inside this industry, not
something derivable from the data as given. This is the kind of gap the
data alone will not show you, and it's the reason the engine's
recommendation is scoped to "an informative prior," never a causal
guarantee, in the final report.

*(Full disclosure also maintained separately in `AI_USE_DISCLOSURE.md`.)*
