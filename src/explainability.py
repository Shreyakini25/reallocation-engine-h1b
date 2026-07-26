"""
Explainability & Its Critique — Component 4 (10 points)

The engine is a transparent rule (Wilson lower-bound threshold), not a
black-box model, so a faithful "explanation" is a decomposition of that
rule against the specific numbers for one employer -- this plays the role
SHAP/LIME would play for a black-box model, but is exactly correct here
rather than an approximation.

THE CRITIQUE (the point of this component): find a case where the
explanation is technically accurate and practically misleading.

Run: python3 src/explainability.py
"""

import pandas as pd
import ast

DATA_PATH = "data/engine_output.csv"


def explain_recommendation(row):
    lines = []
    lines.append(f"Employer: {row['company_name']}")
    lines.append(f"Recommendation: {row['recommendation']}")
    if pd.isna(row.get("wilson_lower", None)):
        lines.append("Reason: no H-1B filings on record (INSUFFICIENT_EVIDENCE bucket).")
        return "\n".join(lines)
    lines.append(
        f"Reason: {int(row['total_filed'])} total filings, "
        f"{row['point_rate']*100:.1f}% raw approval rate, "
        f"95% Wilson lower bound = {row['wilson_lower']*100:.1f}%."
    )
    lines.append(
        f"Threshold logic: PRIORITIZE requires wilson_lower >= 70%. "
        f"This employer's lower bound is {row['wilson_lower']*100:.1f}%, "
        f"which is {'above' if row['wilson_lower'] >= 0.7 else 'below'} that line."
    )
    return "\n".join(lines)


def critique_case(df):
    """
    THE GAP: 'Deloitte Tax LLP' scores PRIORITIZE at ~99.3% approval --
    a textbook confident recommendation by the numbers. But the
    top_job_titles_sponsored field shows the filing history is
    overwhelmingly Tax-track roles (Tax Consultant, Tax Senior, Tax
    Manager, Tax Senior Manager), with only one software-engineering
    title mixed in. A candidate targeting a general software engineering
    role would read "PRIORITIZE, 99.3% approval" and reasonably conclude
    this employer is a safe bet for THEIR role -- when the actual
    evidence is almost entirely about a different job function with a
    different visa-petition profile (different SOC code, different wage
    level, different scrutiny pattern). The explanation is not wrong.
    It is silent about what it is actually evidence FOR.
    """
    row = df[df["company_name"] == "DELOITTE TAX LLP"].iloc[0]
    titles = ast.literal_eval(row["top_job_titles_sponsored"])
    tax_titles = [t for t in titles if "tax" in t.lower()]
    eng_titles = [t for t in titles if t not in tax_titles]

    print("=" * 70)
    print("EXPLAINABILITY CRITIQUE — the case where the explanation lies by omission")
    print("=" * 70)
    print(explain_recommendation(row))
    print()
    print(f"Job titles behind this rate: {titles}")
    print(f"  -> Tax-track titles: {tax_titles}")
    print(f"  -> Non-tax titles: {eng_titles}")
    print()
    print(
        "THE GAP: the recommendation and its explanation are both factually\n"
        "correct -- 99.3% approval, high confidence -- but a candidate\n"
        "targeting a Software Engineer role would be misled: 4 of 5 listed\n"
        "titles are Tax-track roles, a functionally different hiring line\n"
        "with its own SOC code, wage level, and approval history. The\n"
        "aggregate rate is real. It is just evidence for the wrong question\n"
        "if the candidate isn't applying to the Tax practice.\n"
        "\n"
        "PROPOSED FIX -- NOT YET IMPLEMENTED: the engine's recommendation should be re-scoped to\n"
        "the candidate's target job family, not the employer as a whole, "
        "whenever top_job_titles_sponsored spans multiple, distinct role "
        "families. This is a named, undone fix, not a silently patched one "
        "-- engine.py does not currently do this."
    )


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    critique_case(df)
