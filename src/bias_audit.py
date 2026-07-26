"""
Bias Audit — anchored to Brown, "Computational Skepticism for AI," Ch. 7,
"Fairness Metrics: Choosing a Definition and Defending It."
Component 3 of the assignment (10 points)

WHERE BIAS ENTERS (traced data -> output):
  The dataset's H-1B coverage is not random. Younger, smaller, less-funded
  companies are structurally less likely to have ANY H-1B filing on record
  -- not because they are worse sponsors, but because they haven't had
  occasion to file yet (fewer employees, shorter operating history, less
  capital for immigration legal support). This enters at the SAMPLING stage,
  not the labels or the objective: the DOL disclosure file only contains
  employers who have actually filed, so young/small non-filers are invisible
  to the engine by construction. The feedback loop: if candidates follow the
  engine's recommendations, young companies get systematically less
  candidate attention, which further reduces their chance of ever building
  an H-1B track record -- a compounding exclusion.

GROUP DEFINITION (grounded in the real data, not invented):
  Group ESTABLISHED: company_age_years >= 10  (75th percentile of known ages)
  Group YOUNG:       company_age_years <= 4   (25th percentile of known ages)
  (Restricted to rows where company_age_years is known -- see GIGO gate.)

Y (ground truth, defined only where we have it):
  Y = 1 if point_rate >= 0.70  (employer is a "reliable" sponsor in the data
      we do have)
  Restricted to employers with >=3 total filings (per the GIGO gate's
  small-n flag), so Y itself is not built on a noisy 1-filing coin flip.

Y_hat (engine's decision):
  Y_hat = 1 if wilson_lower >= 0.70  i.e. tier == PRIORITIZE

Run: python3 src/bias_audit.py
"""

import pandas as pd
import numpy as np

DATA_PATH = "data/engine_output.csv"


def prepare_audit_frame(df):
    d = df[(df["total_filed"] >= 3) & (df["company_age_years"].notnull())].copy()
    d["Y"] = (d["point_rate"] >= 0.70).astype(int)
    d["Y_hat"] = (d["recommendation"] == "PRIORITIZE").astype(int)

    age_established_cut = 10
    age_young_cut = 4
    d = d[(d["company_age_years"] >= age_established_cut) |
          (d["company_age_years"] <= age_young_cut)].copy()
    d["group"] = np.where(d["company_age_years"] >= age_established_cut,
                           "ESTABLISHED", "YOUNG")
    return d


def rate(mask_num, mask_den):
    denom = mask_den.sum()
    return np.nan if denom == 0 else mask_num.sum() / denom


def demographic_parity(d):
    out = {}
    for g in ["YOUNG", "ESTABLISHED"]:
        sub = d[d["group"] == g]
        out[g] = round(sub["Y_hat"].mean(), 3)
    out["gap"] = round(out["ESTABLISHED"] - out["YOUNG"], 3)
    return out


def equalized_odds(d):
    out = {}
    for g in ["YOUNG", "ESTABLISHED"]:
        sub = d[d["group"] == g]
        tpr = rate((sub["Y_hat"] == 1) & (sub["Y"] == 1), sub["Y"] == 1)
        fpr = rate((sub["Y_hat"] == 1) & (sub["Y"] == 0), sub["Y"] == 0)
        out[g] = {"TPR": round(tpr, 3) if not np.isnan(tpr) else None,
                   "FPR": round(fpr, 3) if not np.isnan(fpr) else None}
    return out


def calibration_check(d, n_bins=4):
    """Within score buckets, is the actual positive rate similar across groups?"""
    d = d.copy()
    d["score_bin"] = pd.qcut(d["wilson_lower"], n_bins, duplicates="drop")
    table = d.groupby(["score_bin", "group"], observed=True)["Y"].agg(["mean", "count"])
    return table


def evidence_coverage_by_group(full_df):
    """
    THE metric the earlier version of this audit was missing: demographic
    parity and equalized odds only measure the ~1,557 employers that made
    it INTO the scored population. They say nothing about the sampling
    bias itself -- whether young and established companies get INTO that
    population at the same rate in the first place. This function measures
    exactly that, on the full 30,369-row population, before any n>=3 filter.
    """
    d = full_df[full_df["company_age_years"].notnull()].copy()
    d["has_evidence"] = d["recommendation"] != "INSUFFICIENT_EVIDENCE — not scored, do not treat as risky"

    young = d[d["company_age_years"] <= 4]
    established = d[d["company_age_years"] >= 10]

    young_cov = young["has_evidence"].mean() * 100
    established_cov = established["has_evidence"].mean() * 100

    return {
        "young_n": len(young),
        "young_with_evidence": int(young["has_evidence"].sum()),
        "young_coverage_pct": round(young_cov, 2),
        "established_n": len(established),
        "established_with_evidence": int(established["has_evidence"].sum()),
        "established_coverage_pct": round(established_cov, 2),
        "coverage_gap_pct_points": round(established_cov - young_cov, 2),
        "young_to_established_coverage_ratio": round(young_cov / established_cov, 2),
    }


def print_report(d, full_df=None):
    print("=" * 70)
    print(f"BIAS AUDIT — YOUNG (age<=4, n={ (d['group']=='YOUNG').sum() }) vs "
          f"ESTABLISHED (age>=10, n={ (d['group']=='ESTABLISHED').sum() })")
    print("=" * 70)

    print("\n--- Evidence Coverage by Group (the SAMPLING bias itself, "
          "measured directly, on the full population before any filter) ---")
    if full_df is not None:
        cov = evidence_coverage_by_group(full_df)
        print(cov)
        print(
            f"This is the number the demographic-parity/equalized-odds "
            f"metrics below CANNOT see, because they only run on employers "
            f"who already made it into the scored population. Young "
            f"companies have H-1B evidence at {cov['young_coverage_pct']}% "
            f"vs. established companies at {cov['established_coverage_pct']}% "
            f"-- a {cov['coverage_gap_pct_points']}-point gap, meaning a "
            f"young company is roughly "
            f"{round(1/cov['young_to_established_coverage_ratio'],1)}x LESS "
            f"likely to have any H-1B record at all. THIS, not the "
            f"recommendation-rate gap among the scored minority, is the "
            f"real leverage point -- and the strongest intervention is "
            f"improving entity resolution and data coverage upstream, not "
            f"adjusting recommendation thresholds downstream."
        )

    print("\n--- Demographic Parity: P(recommend PRIORITIZE | group) ---")
    dp = demographic_parity(d)
    print(dp)
    print("Values claim embedded: positive-recommendation rates should not "
          "depend on company age, regardless of underlying reliability "
          "differences.")

    print("\n--- Equalized Odds: TPR / FPR by group ---")
    eo = equalized_odds(d)
    print(eo)
    print("Values claim embedded: the cost of a wrong recommendation "
          "(missed a good employer, or wasted effort on a bad one) should "
          "fall equally on young and established companies.")

    print("\n--- Calibration check (is a given score equally trustworthy "
          "across groups?) ---")
    cal = calibration_check(d)
    print(cal)

    print("\n--- THE CONFLICT (Ch. 7's impossibility, worked on this data) ---")
    print(
        "Base rates of Y=1 differ by group (established employers accumulate "
        "long, consistent filing histories; young employers' rates are "
        "noisier even after the n>=3 filter). Per Ch.7's proof, when base "
        "rates differ, calibration parity and equalized odds cannot both "
        "hold exactly -- whichever holds, the other will show a gap. See "
        "the numbers above for which one actually breaks on this data."
    )


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    d = prepare_audit_frame(df)
    print_report(d, full_df=df)
    d.to_csv("data/bias_audit_frame.csv", index=False)
