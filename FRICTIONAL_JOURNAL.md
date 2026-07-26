# Frictional Journal

## Prediction (before building)

**Timestamp:** 2026-07-20, before writing any code for this engine.

**Author:** Shreya Kini

I expect the hardest failure to be in the **causal reasoning component** — I
think I'll be tempted to let "high historical approval rate" quietly stand
in for "good bet for me," and the hardest part will be naming the
confounders honestly instead of writing around them. I expect the engine to
turn out **weakly causally valid at best** — I'd put my confidence that it
reallocates on correlation dressed as causation at **80%** (i.e., I expect
the honest verdict to be "yes, mostly correlational").

For the bias audit, I expect the missingness in the data (I already know
from earlier exploration that most companies have no H-1B record at all) to
be the real story, more than any gap among the companies that *do* have
data.

I do **not** expect the adversarial test to be dramatic — my gut says a
single added denial should only flip a handful of borderline cases, maybe
5–10% of the small-filer group.

## Reflection (after building)

**Timestamp:** 26th july 2026, 4:47pm
**What actually happened:** the causal prediction held up almost exactly —
the verdict came out "yes, largely correlational," for the reasons I
expected (survivorship, role-mixture confounding) but also for one I hadn't
anticipated: I assumed filing volume and approval rate would be positively
correlated (bigger, more experienced filers = more reliable), and the real
correlation came out at r=0.008 — essentially zero. I had to catch myself
almost writing the "obvious" story into the report before checking the
actual number, which is a good, uncomfortable reminder of exactly what this
course is about.

**Where my prediction was wrong:** the adversarial test. I predicted a mild
5–10% flip rate from one added denial. The actual number was **54.6%** —
more than five times my estimate. In hindsight, this makes sense once you
sit with the Wilson-interval math at low n (an interval built on 4 filings
is inherently wide), but my intuition badly underestimated how much a
"tiny," realistic correction could move a formally correct, formally
uncertainty-aware system. My calibration on "how fragile is a small-sample
statistical rule" was worse than I thought going in — I was reasoning from
"the fix (Wilson bounds) exists" to "therefore the fragility is mostly
handled," which the numbers didn't support.

**What this says about my calibration:** I'm reasonably well-calibrated
about causal structure (where I have real domain intuition from watching
H-1B outcomes among friends and colleagues), and poorly calibrated about
the numerical behavior of my own uncertainty quantification at small n —
I trusted the Wilson-interval fix more than the data justified. That's
useful information for how much scrutiny I give my own "we already handled
that" claims going forward.
