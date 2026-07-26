# AI Use Disclosure

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

**What I changed:** I directed the fairness-metric anchor (Ch. 7) and the
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
consulting placements (YASH, and the wider ecosystem of firms like
Infosys/TCS/Cognizant-type employers I know from this industry), a
staffing/consulting employer's H-1B approval rate reflects a fundamentally
different sponsorship relationship than a direct-hire product company's:
staffing firms sponsor at high volume partly because they place workers
across many end-clients and can absorb individual case risk across a large
portfolio, while a smaller product company's identical approval rate
reflects a much more concentrated bet on specific hires. The dataset has no
column distinguishing "staffing/consulting" from "direct-hire" employers,
and Claude's analysis, working only from the columns present, could not
have surfaced this distinction or flagged it as a confound worth naming —
I added it as a scoping note for future work in the causal analysis
because it's a real business-model difference I know from being inside
this industry, not something derivable from the data as given. This is the
kind of gap the data alone will not show you, and it's the reason the
engine's recommendation is scoped to "an informative prior," never a
causal guarantee, in the final report.
