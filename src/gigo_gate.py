"""
GIGO Gate — Data Validation for the H-1B Sponsorship Reallocation Engine
Component 2 of the assignment (10 points)

Before the engine is allowed to reallocate a candidate's job-search effort,
the underlying data must pass an explicit, checkable quality gate.

Run: python3 src/gigo_gate.py
"""

import pandas as pd
import numpy as np
import re
import sys

DATA_PATH = "data/SEC_DOL_H1b_data_mapped.csv"

REQUIRED_COLUMNS = ["company_name", "Total Approvals", "Total Denials",
                    "Approval_Rate", "company_age_years", "median_salary_offered"]


def load_raw(path=DATA_PATH):
    return pd.read_csv(path)


def _normalize_name(name):
    if pd.isna(name):
        return name
    n = re.sub(r"[^A-Z0-9 ]", "", str(name).upper())
    for suffix in (" INC", " LLC", " CORP", " CORPORATION", " LTD", " LLP", " CO", " COMPANY"):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    return n.strip()


def run_gigo_gate(df):
    """
    Named hidden assumptions this dataset makes, and a checkable gate for each.
    Returns (passed: bool, report: dict, blocking_reasons: list[str])

    Two levels, not one:
      BLOCK  -- structurally broken data; the engine must not run at all.
      FLAG   -- real limitations that are disclosed and routed around, not
                fixed, per the assignment's "prefer disclosure to fabrication."
    """
    report = {}
    blocking_reasons = []
    n = len(df)

    # --- BLOCK 1: required columns must exist at all ---
    # CRITICAL: return immediately if any are missing. Continuing past this
    # point would crash with a KeyError on the first missing column accessed
    # below -- an uncontrolled crash is NOT the same as a clean BLOCK, and
    # an earlier version of this gate had exactly that bug (found via
    # deliberate testing: dropping company_name, Total Approvals,
    # company_age_years, or Approval_Rate each caused a raw KeyError instead
    # of a reported gate failure).
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        blocking_reasons.append(f"Missing required column(s): {missing_cols}")
        report["GATE_STANDARD"] = (
            "BLOCK: required schema is incomplete. No further checks were "
            "run because they depend on the missing column(s)."
        )
        report["BLOCKING_ISSUES"] = blocking_reasons
        return False, report, blocking_reasons

    # --- BLOCK 2: company_name must be present (can't score an unnamed row) ---
    if "company_name" in df.columns:
        null_names = df["company_name"].isnull().sum()
        if null_names > 0:
            blocking_reasons.append(f"{null_names} rows have a null company_name.")

    # --- BLOCK 3: negative filing counts are structurally impossible ---
    for col in ("Total Approvals", "Total Denials"):
        if col in df.columns:
            negatives = (df[col] < 0).sum()
            if negatives > 0:
                blocking_reasons.append(f"{negatives} rows have a negative value in '{col}'.")

    # --- Assumption 1: "No H-1B record" means the same thing for every row ---
    h1b_cols = ["Total Approvals", "Total Denials", "Approval_Rate",
                "median_salary_offered"]
    missing_h1b = df[h1b_cols].isnull().all(axis=1).sum()
    report["assumption_1_no_record_ambiguous"] = {
        "description": (
            "Absence of H-1B data is treated by a naive model as a single "
            "category ('no data'), but it silently conflates three different "
            "realities: never needed to sponsor, too new/small to have filed "
            "yet, or a join failure between the SEC/startup source and the "
            "DOL source."
        ),
        "rows_with_zero_h1b_signal": int(missing_h1b),
        "pct_of_total": round(100 * missing_h1b / n, 1),
        "gate_check": "FLAG — must not be silently imputed as 'risky'.",
    }

    # --- Assumption 2: company_age_years is reliable/complete ---
    missing_age = df["company_age_years"].isnull().sum()
    report["assumption_2_age_completeness"] = {
        "description": (
            "company_age_years is missing for a meaningful share of rows, "
            "and is exactly the variable needed to test whether 'no H-1B "
            "data' correlates with company age (the suspected bias path)."
        ),
        "rows_missing_age": int(missing_age),
        "pct_of_total": round(100 * missing_age / n, 1),
        "gate_check": "PASS with caveat — usable, but bias audit must report "
                      "on the age-known subset only and say so explicitly.",
    }

    # --- Assumption 3: Approval_Rate is comparable across companies regardless
    # of how many total petitions it's based on ---
    has_h1b = df[df["Total Approvals"].notnull()].copy()
    has_h1b["total_filed"] = has_h1b["Total Approvals"].fillna(0) + has_h1b["Total Denials"].fillna(0)
    low_volume = (has_h1b["total_filed"] < 3).sum()
    report["assumption_3_approval_rate_small_n"] = {
        "description": (
            "Approval_Rate is a proportion computed on a small denominator "
            "for many employers (e.g. 1 filing = 0% or 100% rate). Treating "
            "a rate from n=1 the same as a rate from n=500 overstates "
            "confidence for small filers."
        ),
        "employers_with_fewer_than_3_filings": int(low_volume),
        "pct_of_employers_with_any_h1b_data": round(100 * low_volume / len(has_h1b), 1),
        "gate_check": "FLAG — engine must attach an uncertainty band that "
                      "widens as total_filed shrinks, not report a bare rate.",
    }

    # --- Assumption 4a: no EXACT duplicate company rows inflating counts ---
    dupes = df["company_name"].duplicated().sum()
    report["assumption_4a_exact_duplicate_employers"] = {
        "description": "Duplicate company_name rows would double-count an employer's signal.",
        "duplicate_rows": int(dupes),
        "gate_check": "PASS" if dupes == 0 else "FLAG",
    }

    # --- Assumption 4b: normalized-name duplicates (a distinct, real risk
    # exact-match misses -- e.g. "Acme Inc" vs "Acme LLC" vs "ACME, Inc.") ---
    norm = df["company_name"].apply(_normalize_name)
    norm_group_sizes = norm.value_counts()
    norm_dupe_groups = norm_group_sizes[norm_group_sizes > 1]
    report["assumption_4b_normalized_name_duplicates"] = {
        "description": (
            "Exact-match duplicate checking (4a) misses entity-resolution "
            "failures where the same real company appears under legal-suffix "
            "or punctuation variants. This is a DIFFERENT and NOT smaller "
            "risk than 4a -- it can silently split one employer's real "
            "filing history across two 'different' rows, understating its "
            "true filing volume and Wilson confidence."
        ),
        "normalized_duplicate_groups": int(len(norm_dupe_groups)),
        "rows_in_duplicate_groups": int(norm_dupe_groups.sum()),
        "gate_check": (
            "FLAG — not resolved in this project. These are CANDIDATE "
            "duplicates from string normalization only (stripped punctuation "
            "and common legal suffixes); confirming they are the same real "
            "entity requires human review per Ch. 7's own entity-resolution "
            "rule ('must never enable fuzzy matching without a human "
            "sign-off'). Reported as an open limitation, not auto-merged."
        ),
    }

    # --- Assumption 5: measurement protocol did not change mid-collection ---
    report["assumption_5_measurement_protocol"] = {
        "description": (
            "The file has no reporting-period or extraction-date column, so "
            "we cannot confirm all H-1B figures were pulled from the same "
            "DOL disclosure vintage. This is a real, undocumented gap."
        ),
        "gate_check": "FLAG — documented limitation, not fixable from this "
                      "file alone; disclosed in the validation report.",
    }

    # Human-checkable pass/fail standard (stated up front, per the assignment):
    scored_rows = has_h1b[has_h1b["total_filed"] >= 1]
    insufficient_evidence_rows = n - len(scored_rows)

    report["GATE_STANDARD"] = (
        "BLOCK the run entirely if the schema is broken or contains "
        "structurally impossible values (missing required columns, null "
        "company names, negative filing counts). Otherwise, a row may be "
        "SCORED only if it has >=1 actual H-1B filing on record; all other "
        "rows are routed to an explicit INSUFFICIENT_EVIDENCE bucket -- "
        "never dropped, never defaulted to a risk score."
    )
    report["rows_scored"] = int(len(scored_rows))
    report["rows_insufficient_evidence"] = int(insufficient_evidence_rows)
    report["pct_insufficient_evidence"] = round(100 * insufficient_evidence_rows / n, 1)
    report["BLOCKING_ISSUES"] = blocking_reasons if blocking_reasons else "None"

    passed = len(blocking_reasons) == 0
    return passed, report, blocking_reasons


def print_report(report):
    print("=" * 70)
    print("GIGO GATE REPORT — SEC_DOL_H1b_data_mapped.csv")
    print("=" * 70)
    for key, val in report.items():
        if isinstance(val, dict):
            print(f"\n[{key}]")
            for k, v in val.items():
                print(f"  {k}: {v}")
        else:
            print(f"\n{key}: {val}")


if __name__ == "__main__":
    df = load_raw()
    passed, report, blocking_reasons = run_gigo_gate(df)
    print_report(report)
    print("\n" + "=" * 70)
    if passed:
        print("GATE STATUS: PASSED -- engine may proceed to scoring.")
    else:
        print("GATE STATUS: BLOCKED -- engine execution halted. Reasons:")
        for reason in blocking_reasons:
            print(f"  - {reason}")
        sys.exit(1)
