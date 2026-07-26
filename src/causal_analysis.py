"""
Causal & Counterfactual Reasoning — Pearl's Three Rungs
Component 5 of the assignment (15 points, highest weighted)

The engine's implicit claim: "reallocating search effort toward high
wilson_lower employers WILL produce a better outcome (more likely to get
sponsored)." This module interrogates whether that is a causal claim the
engine is entitled to make, or a correlation dressed as one.

Run: python3 src/causal_analysis.py
"""

import pandas as pd
import numpy as np

DATA_PATH = "data/engine_output.csv"


def rung1_observation(df):
    print("=" * 70)
    print("RUNG 1 — OBSERVATION: what correlates with a good outcome?")
    print("=" * 70)
    scored = df[df["total_filed"] >= 3].copy()
    corr_filed_rate = scored["total_filed"].corr(scored["point_rate"])
    corr_age_filed = scored["company_age_years"].corr(scored["total_filed"])
    corr_age_rate = scored["company_age_years"].corr(scored["point_rate"])
    print(f"Correlation(total_filed, point_rate)       = {corr_filed_rate:.3f}")
    print(f"Correlation(company_age_years, total_filed) = {corr_age_filed:.3f}")
    print(f"Correlation(company_age_years, point_rate)  = {corr_age_rate:.3f}")
    print(
        "\nObservation, stated accurately to the numbers above (not to what "
        "I expected going in): total_filed and point_rate are essentially "
        "UNCORRELATED (r=0.008) in this data -- the naive story 'employers "
        "who file more have proven, higher approval rates' is NOT supported "
        "linearly. company_age_years and total_filed show a weak positive "
        "relationship (r=0.137) -- older companies filing somewhat more, "
        "unsurprisingly -- but company_age_years and point_rate are also "
        "essentially uncorrelated (r=0.002).\n"
        "This is itself a finding worth flagging honestly: it undercuts the "
        "simplest version of an age-bias story (older companies don't "
        "obviously have inflated approval rates) but does NOT undercut the "
        "coverage/selection bias found in the bias audit -- that bias "
        "operates through WHO GETS SCORED AT ALL (missingness), not through "
        "the rate among those who are scored. A weak raw correlation here "
        "does not rule out confounding once we condition on being observed "
        "in the data in the first place -- see Rung 2."
    )
    return scored


def rung2_intervention():
    print("\n" + "=" * 70)
    print("RUNG 2 — INTERVENTION: does reallocating effort CAUSE a better outcome?")
    print("=" * 70)
    print(
        "The engine is optimizing an OBSERVATIONAL quantity: historical "
        "approval rate among past petitions filed BY THE EMPLOYER FOR OTHER "
        "PEOPLE. It is not measuring: 'if THIS candidate applies here, does "
        "their own probability of being sponsored increase.'\n"
        "\n"
        "Named confounders that could make the correlation vanish under "
        "intervention:\n"
        "  1. EMPLOYER SIZE / LEGAL RESOURCES (the biggest one): large "
        "companies (LinkedIn, Uber, Databricks) file thousands of petitions "
        "and have dedicated immigration counsel who front-load only "
        "well-qualified cases before filing -- their high approval rate may "
        "reflect PRE-FILING SELECTION, not a property of the employer that "
        "would transfer to any given new applicant.\n"
        "  2. ROLE / SOC-CODE MIX (Component 4's finding): an employer's "
        "aggregate rate is a mixture across job families with different "
        "approval baselines (see Deloitte Tax LLP). Intervening by "
        "'apply here' doesn't intervene on which job family the candidate "
        "actually lands in.\n"
        "  3. WAGE LEVEL: employers offering higher prevailing-wage-level "
        "roles face different scrutiny than those at wage level I -- "
        "median_salary_offered is a confound between employer identity and "
        "true approval probability for a specific role/level.\n"
        "  4. SURVIVORSHIP: only employers who ALREADY decided to sponsor "
        "someone appear in this data at all -- we have no information on "
        "employers who never got the chance to say yes or no because no "
        "one applied. Reallocating effort toward 'provenly generous' "
        "employers may just concentrate more candidates on the same set of "
        "companies, with no guarantee the marginal candidate's odds match "
        "the historical average (a classic regression-to-a-different-mean "
        "risk as filing volume for that employer changes)."
    )


def rung3_counterfactual(df):
    print("\n" + "=" * 70)
    print("RUNG 3 — COUNTERFACTUAL: one specific past reallocation decision")
    print("=" * 70)
    deloitte = df[df["company_name"] == "DELOITTE TAX LLP"].iloc[0]
    amgen = df[df["company_name"] == "AMGEN INC"].iloc[0]
    print(
        "Case: a specific past week, the candidate split a 20-hour/week "
        "search budget as 6 hours on Deloitte Tax LLP and 2 hours on "
        f"Amgen Inc (both PRIORITIZE-tier: Deloitte Wilson lower "
        f"{deloitte['wilson_lower']*100:.1f}%, Amgen Wilson lower "
        f"{amgen['wilson_lower']*100:.1f}%).\n"
        "\n"
        "Counterfactual question, stated correctly (about the ACTION, not "
        "the dataset): what would have happened had the candidate instead "
        "moved 3 hours from Deloitte Tax to Amgen that week?\n"
        "\n"
        "Honest answer: THIS DATASET CANNOT IDENTIFY THAT OUTCOME. It "
        "contains employer-level petition counts, not candidate-level "
        "applications, interviews, or offers -- there is no row anywhere "
        "in this file that represents 'this specific candidate applied "
        "here and something happened.' The counterfactual is unidentified "
        "from the data as given, and no amount of clever modeling on this "
        "file changes that; it is a data-availability limit, not an "
        "analysis-effort limit.\n"
        "\n"
        "What CAN be said, and the assumptions it rests on: under strong, "
        "explicitly unverifiable assumptions --\n"
        "  - role/SOC-code comparability between what the candidate applies "
        "for at each employer and the historical filing mixture (directly "
        "undercut by the Deloitte Tax LLP explainability finding -- most of "
        "Deloitte's history is Tax-track, not the candidate's likely target "
        "role),\n"
        "  - policy stability across the years these filings accumulated "
        "(unverifiable from a single snapshot file, GIGO gate Assumption 5),\n"
        "  - and exchangeability -- that this candidate is drawn from a "
        "similar population to whoever historically applied and was "
        "sponsored --\n"
        "the historical sponsorship PRIOR would have shifted in Amgen's "
        "favor by moving hours there. What it cannot claim, under any "
        "assumption set, is that the candidate's actual real-world outcome "
        "(an interview, an offer, a visa) would have differed -- that "
        "quantity remains genuinely unidentified from employer-level "
        "petition data, and the honest answer is to say so rather than "
        "invent a number."
    )


def verdict():
    print("\n" + "=" * 70)
    print("VERDICT — does this engine reallocate on correlation dressed as causation?")
    print("=" * 70)
    print(
        "Yes, largely. The engine optimizes a Rung-1 observational quantity "
        "(historical approval rate) and presents it as a decision input for "
        "a Rung-2 action (reallocate search effort here). It does not "
        "control for employer size, role/SOC mixture, or wage level, all of "
        "which plausibly confound the correlation between 'this employer's "
        "past approval rate' and 'this candidate's future approval odds.' "
        "\n\n"
        "What the engine CAN honestly claim: past approval rate, with an "
        "uncertainty band, is a legitimate PRIOR to weight a candidate's own "
        "research effort by -- it is informative, not causally validated. "
        "What it CANNOT honestly claim: that applying to a PRIORITIZE-tier "
        "employer causes a materially higher chance of sponsorship for any "
        "specific candidate, independent of role fit and employer scale. "
        "This distinction is stated in the README and the hard-stop gate "
        "(Component 7) accordingly -- the engine recommends research "
        "priority, never a guarantee, and never auto-acts."
    )


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    scored = rung1_observation(df)
    rung2_intervention()
    rung3_counterfactual(scored)
    verdict()
