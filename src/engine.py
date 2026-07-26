"""
The H-1B Sponsorship Reallocation Engine
Component 1 of the assignment (12 points)

WHAT IT REALLOCATES: a candidate's limited job-search effort (applications,
tailored resumes, interview-prep hours) across a set of prospective employers.

OBJECTIVE (stated plainly, per the assignment's requirement):
  "Recommend more search effort toward employers with strong, statistically
   credible evidence of H-1B sponsorship follow-through, and less effort
   toward employers with weak or contradictory evidence -- while explicitly
   flagging employers we simply don't have evidence on, rather than treating
   silence as a bad signal."

WHAT THIS OBJECTIVE LEAVES OUT (stated honestly, per the assignment):
  - It says nothing about job fit, compensation beyond median wage, career
    growth, or whether the candidate would even get an interview.
  - It rewards employers who sponsor OFTEN, which mechanically favors large
    employers who file many petitions -- a small employer that sponsors
    every single person who asks looks statistically weaker under this
    objective purely because they've filed fewer times. This is a real,
    named blind spot, not a hidden one (see Component 5, causal analysis).

Run: python3 src/engine.py
"""

import pandas as pd
import numpy as np
import sys
from gigo_gate import load_raw, run_gigo_gate

DATA_PATH = "data/SEC_DOL_H1b_data_mapped.csv"

# Wilson score interval gives a defensible uncertainty band for a proportion
# (Approval_Rate) computed on a small number of trials (total_filed), which
# is exactly the failure mode the GIGO gate flagged.
def wilson_interval(successes, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    half_width = (z * np.sqrt((p_hat * (1 - p_hat) / n) + (z**2 / (4 * n**2)))) / denom
    return (max(0, center - half_width), min(1, center + half_width))


def build_engine_table(df):
    df = df.copy()
    df["total_filed"] = df["Total Approvals"].fillna(0) + df["Total Denials"].fillna(0)
    has_evidence = df["Total Approvals"].notnull()

    scored = df[has_evidence & (df["total_filed"] >= 1)].copy()
    no_evidence = df[~(has_evidence & (df["total_filed"] >= 1))].copy()

    # Uncertainty-aware score: Wilson lower bound, not the raw rate.
    # This is the "attach an uncertainty band" fix the GIGO gate demanded.
    lowers, uppers = [], []
    for _, row in scored.iterrows():
        lo, hi = wilson_interval(row["Total Approvals"], row["total_filed"])
        lowers.append(lo)
        uppers.append(hi)
    scored["wilson_lower"] = lowers
    scored["wilson_upper"] = uppers
    scored["point_rate"] = scored["Total Approvals"] / scored["total_filed"]
    scored["uncertainty_width"] = scored["wilson_upper"] - scored["wilson_lower"]

    # Recommendation tier -- uses the CONSERVATIVE (lower-bound) estimate,
    # not the point estimate, so a lucky small sample doesn't get over-trusted.
    def tier(row):
        if row["total_filed"] < 3:
            return "LOW-CONFIDENCE — insufficient filings to trust the rate"
        if row["wilson_lower"] >= 0.7:
            return "PRIORITIZE"
        elif row["wilson_lower"] >= 0.4:
            return "CONSIDER"
        else:
            return "DEPRIORITIZE"

    scored["recommendation"] = scored.apply(tier, axis=1)
    no_evidence["recommendation"] = "INSUFFICIENT_EVIDENCE — not scored, do not treat as risky"
    no_evidence["wilson_lower"] = np.nan
    no_evidence["wilson_upper"] = np.nan
    no_evidence["uncertainty_width"] = np.nan
    no_evidence["point_rate"] = np.nan

    combined = pd.concat([scored, no_evidence], ignore_index=True)
    return combined, scored, no_evidence


def reallocate_effort(scored, shortlist_names, total_hours_per_week=20):
    """
    Component 1's required output: not just a tier, but a concrete move --
    'move quantity Q of the resource (hours/week) from employer A to
    employer B' -- computed on a candidate's own shortlist.

    BASELINE (your-input, not a record): equal hours across the shortlist,
    the default a candidate would use with no scorer at all.

    RECOMMENDED: hours proportional to each employer's wilson_lower score,
    renormalized across the shortlist and scaled to the same total budget --
    so the total effort spent doesn't change, only its distribution does.

    ALLOCATION RANGE: recomputed at wilson_lower and wilson_upper, so the
    recommended hours for each employer come with the same uncertainty band
    Component 1's uncertainty requirement calls for -- not a bare point number.
    """
    if not shortlist_names:
        raise ValueError("The shortlist cannot be empty.")

    requested_names = set(shortlist_names)
    sub = scored[scored["company_name"].isin(requested_names)].copy()

    # CRITICAL: check for names that didn't match at all -- not just names
    # that matched but weren't scored. An earlier version of this function
    # silently dropped unmatched names entirely (e.g. a typo or an employer
    # in the INSUFFICIENT_EVIDENCE bucket), which meant the candidate's
    # whole budget got quietly redirected to whoever WAS found -- discovered
    # by testing with a deliberately fake company name and finding it
    # vanished with no warning, and with an all-fake shortlist, a raw
    # ZeroDivisionError instead of a clear error message.
    found_names = set(sub["company_name"])
    missing_names = sorted(requested_names - found_names)
    if missing_names:
        raise ValueError(
            "These employers could not be scored because they were not "
            f"found, or had insufficient evidence to be scored at all: "
            f"{missing_names}. Remove them from the shortlist or check "
            "INSUFFICIENT_EVIDENCE / LOW-CONFIDENCE status before retrying."
        )

    if sub["wilson_lower"].isnull().any():
        missing = sub[sub["wilson_lower"].isnull()]["company_name"].tolist()
        raise ValueError(
            f"Cannot reallocate effort toward unscored employers: {missing}. "
            "These belong in the INSUFFICIENT_EVIDENCE bucket, not a shortlist."
        )

    n = len(sub)
    baseline = total_hours_per_week / n
    sub["baseline_effort"] = baseline

    def scaled(col):
        weights = sub[col].clip(lower=0.01)  # avoid a literal-zero allocation
        return weights / weights.sum() * total_hours_per_week

    sub["recommended_effort"] = scaled("wilson_lower")
    sub["effort_delta"] = sub["recommended_effort"] - sub["baseline_effort"]

    # Per-employer allocation range: hold every OTHER employer's weight at its
    # own wilson_lower (the conservative baseline), and let only THIS
    # employer's own weight move from its wilson_lower to its wilson_upper.
    # This is the one thing that guarantees allocation_lower <= allocation_upper
    # for every row -- a full independent renormalization at each bound does
    # NOT guarantee that, because other employers' shares shift too.
    lower_weights = sub["wilson_lower"].clip(lower=0.01)
    total_lower = lower_weights.sum()
    alloc_lower, alloc_upper = [], []
    for idx, row in sub.iterrows():
        w_lo = max(row["wilson_lower"], 0.01)
        w_hi = max(row["wilson_upper"], 0.01)
        others_sum = total_lower - w_lo
        alloc_lower.append(w_lo / (w_lo + others_sum) * total_hours_per_week)
        alloc_upper.append(w_hi / (w_hi + others_sum) * total_hours_per_week)
    sub["allocation_lower"] = alloc_lower
    sub["allocation_upper"] = alloc_upper

    sub = sub.sort_values("effort_delta")
    move_from_row = sub.iloc[0]
    move_to_row = sub.iloc[-1]
    quantity_to_move = round(min(abs(move_from_row["effort_delta"]),
                                  move_to_row["effort_delta"]), 1)

    sub["move_from"] = move_from_row["company_name"]
    sub["move_to"] = move_to_row["company_name"]
    sub["quantity_to_move_hours_per_week"] = quantity_to_move

    return sub, move_from_row, move_to_row, quantity_to_move


def print_reallocation_example(scored):
    print("\n" + "=" * 70)
    print("CONCRETE REALLOCATION EXAMPLE (Component 1 requirement)")
    print("=" * 70)
    # A realistic 5-employer shortlist spanning tiers, for a worked example.
    example_shortlist = (
        scored.sort_values("wilson_lower", ascending=False).head(3)["company_name"].tolist()
        + scored[scored["recommendation"] == "CONSIDER"].head(2)["company_name"].tolist()
    )
    result, move_from, move_to, qty = reallocate_effort(scored, example_shortlist, total_hours_per_week=20)
    print(f"Candidate's weekly job-search effort budget: 20 hours/week (your-input, not a record)")
    print(f"Shortlist: {example_shortlist}\n")
    print(result[["company_name", "recommendation", "baseline_effort",
                  "recommended_effort", "effort_delta",
                  "allocation_lower", "allocation_upper"]].round(2).to_string(index=False))
    print(f"\nRECOMMENDED MOVE: move {qty} hours/week from "
          f"{move_from['company_name']} to {move_to['company_name']}.")
    print(f"Uncertainty on that move: recommended hours for "
          f"{move_to['company_name']} range from "
          f"{result[result['company_name']==move_to['company_name']]['allocation_lower'].iloc[0]:.2f} to "
          f"{result[result['company_name']==move_to['company_name']]['allocation_upper'].iloc[0]:.2f} "
          f"hours/week depending on which end of its Wilson interval is true.")
    return result


def summarize(scored):
    print("=" * 70)
    print("REALLOCATION RECOMMENDATION SUMMARY (scored employers only, n=%d)" % len(scored))
    print("=" * 70)
    print(scored["recommendation"].value_counts())
    print()
    print("Top 10 PRIORITIZE employers by Wilson lower bound (most defensible, not just highest raw rate):")
    top = scored[scored["recommendation"] == "PRIORITIZE"].sort_values(
        "wilson_lower", ascending=False
    ).head(10)
    print(top[["company_name", "total_filed", "point_rate", "wilson_lower",
               "wilson_upper", "median_salary_offered"]].to_string(index=False))


if __name__ == "__main__":
    df = load_raw()
    gate_passed, gate_report, blocking_reasons = run_gigo_gate(df)
    if not gate_passed:
        print("=" * 70)
        print("GIGO GATE FAILED. Engine execution BLOCKED. Reasons:")
        for reason in blocking_reasons:
            print(f"  - {reason}")
        print("Run `python3 src/gigo_gate.py` for the full report.")
        sys.exit(1)
    print("GIGO gate passed -- proceeding to scoring.\n")

    combined, scored, no_evidence = build_engine_table(df)
    summarize(scored)
    realloc_result = print_reallocation_example(scored)
    realloc_result.to_csv("data/reallocation_example.csv", index=False)
    combined.to_csv("data/engine_output.csv", index=False)
    print(f"\nFull output ({len(combined)} rows) written to data/engine_output.csv")
    print(f"Worked reallocation example written to data/reallocation_example.csv")
