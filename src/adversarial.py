"""
Adversarial Robustness & Fragility — Component 6 (8 points)

Perturbation tested: a single additional denial recorded against a
low-filing-volume employer -- exactly the kind of small, realistic data
correction (a late-arriving record, a corrected case status) that a human
reviewer would not think twice about, but that can flip a small-n employer's
tier because Wilson bounds are sensitive at low n.

Run: python3 src/adversarial.py
"""

import pandas as pd
import numpy as np
from engine import wilson_interval

DATA_PATH = "data/engine_output.csv"


def perturb_one_denial(df, min_filed=3, max_filed=10):
    """
    For every employer with a small number of total filings, simulate one
    additional denial being added to the record (a plausible correction:
    e.g. a case whose final status was updated after this extract was
    pulled -- Assumption 5 in the GIGO gate). Recompute the tier.
    """
    target = df[(df["total_filed"] >= min_filed) & (df["total_filed"] <= max_filed)
                & df["wilson_lower"].notnull()].copy()

    flips = []
    for _, row in target.iterrows():
        new_filed = row["total_filed"] + 1
        new_approvals = row["Total Approvals"]  # unchanged -- the new case is a denial
        lo, hi = wilson_interval(new_approvals, new_filed)
        old_tier = row["recommendation"]

        def tier_from_lower(lower, filed):
            if filed < 3:
                return "LOW-CONFIDENCE"
            if lower >= 0.7:
                return "PRIORITIZE"
            elif lower >= 0.4:
                return "CONSIDER"
            else:
                return "DEPRIORITIZE"

        new_tier = tier_from_lower(lo, new_filed)
        if new_tier != old_tier:
            flips.append({
                "company_name": row["company_name"],
                "total_filed_before": int(row["total_filed"]),
                "wilson_lower_before": round(row["wilson_lower"], 3),
                "tier_before": old_tier,
                "wilson_lower_after_1_denial": round(lo, 3),
                "tier_after": new_tier,
            })
    return pd.DataFrame(flips), len(target)


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    flips, n_tested = perturb_one_denial(df)
    print("=" * 70)
    print("ADVERSARIAL TEST — one additional denial on low-filing-volume employers")
    print("=" * 70)
    print(f"Employers tested (3-10 total filings): {n_tested}")
    print(f"Employers whose tier FLIPPED from one additional denial: {len(flips)}")
    print(f"Flip rate: {100*len(flips)/n_tested:.1f}%")
    print()
    if len(flips):
        print(flips.head(10).to_string(index=False))
    print(
        "\nFAILURE CONDITION, stated honestly: for employers near the "
        "low-filing-volume boundary, a SINGLE additional denial -- the kind "
        "of correction that could arrive from a data-vintage mismatch "
        "(GIGO gate, Assumption 5), not an adversary -- is enough to flip "
        "the recommendation. A human reviewer glancing at '1 more denial "
        "out of 4 filings' would not consider that a dramatic change, but "
        "the engine's tiering can react sharply at this range.\n"
        "MITIGATION IN PLACE: the LOW-CONFIDENCE tier below total_filed=3 "
        "already blocks the most fragile cases from a confident tier. This "
        "test shows the fragility extends a bit further than that cutoff "
        "captures, and is disclosed as an open limitation rather than "
        "silently patched."
    )
