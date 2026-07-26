"""
Delegation Map + Hard-Stop Gate — Component 7 (10 points)
Anchored secondarily to Ch. 9 (Delegation, Trust, and the Supervisor Role)
and Ch. 12 (Accountability: Who Is Responsible).

Run: python3 src/delegation_hardstop.py
"""

DELEGATION_MAP = [
    {
        "component": "GIGO gate (data admission)",
        "tool_decides": "Whether a row has >=1 real H-1B filing on record.",
        "human_decides": "Whether the 94.9% missing-data rate is acceptable "
                          "to proceed with at all, and how insufficient-"
                          "evidence employers are communicated to the user.",
        "override_point": "Human can override the GATE_STANDARD threshold "
                           "(e.g. relax to >=1 filing already done here) but "
                           "must document why in the run log.",
    },
    {
        "component": "Wilson-bound tiering",
        "tool_decides": "The numeric tier (PRIORITIZE/CONSIDER/DEPRIORITIZE/"
                         "LOW-CONFIDENCE) from the formula.",
        "human_decides": "Whether the 70%/40% thresholds are the right cut "
                          "points, and whether a specific employer's tier "
                          "should be manually adjusted given job-family "
                          "mismatch (Component 4's Deloitte Tax finding).",
        "override_point": "PROPOSED, NOT IMPLEMENTED: any employer flagged "
                           "by the explainability check as having a "
                           "job-title mismatch would ideally be downgraded "
                           "to CONSIDER regardless of its numeric tier, "
                           "pending human review of role fit -- engine.py "
                           "does not currently do this automatically; a "
                           "human must apply this judgment manually today.",
    },
    {
        "component": "Bias-audited group comparison",
        "tool_decides": "Computes demographic parity / equalized odds gap "
                         "between young and established employers.",
        "human_decides": "Whether the observed gap (Component 3) is "
                          "tolerable, and whether the objective should be "
                          "adjusted to explicitly boost young-company "
                          "visibility as a correction.",
        "override_point": "A human supervisor, not the tool, decides "
                           "whether to apply a fairness correction and "
                           "which definition (demographic parity vs. "
                           "equalized odds) to prioritize -- per Ch. 7, this "
                           "is a values choice the tool cannot make for you.",
    },
    {
        "component": "Final action: applying, interviewing, accepting an offer",
        "tool_decides": "Nothing. The tool never applies to a job, submits "
                         "an application, or contacts an employer.",
        "human_decides": "Everything past the recommendation.",
        "override_point": "N/A -- this is the hard-stop boundary itself.",
    },
    {
        "component": "Explainability interpretation",
        "tool_decides": "Computes the mechanical decomposition of a "
                         "recommendation (filings, rate, Wilson bound vs. "
                         "threshold) and flags a title-mismatch case.",
        "human_decides": "Whether a flagged title mismatch (e.g. Deloitte "
                          "Tax LLP) means this employer's tier doesn't "
                          "apply to their own target role, and whether to "
                          "act on the recommendation anyway.",
        "override_point": "Human can discount or ignore a tier entirely on "
                           "role-fit grounds the tool cannot verify.",
    },
    {
        "component": "Causal-validity judgment (Component 5)",
        "tool_decides": "Computes the correlation statistics and confounder "
                         "list mechanically from the data.",
        "human_decides": "Whether the honest 'correlation, not causation' "
                          "verdict changes how much weight to put on the "
                          "engine's recommendation at all, for their own "
                          "specific situation.",
        "override_point": "The candidate decides how much to trust the "
                           "prior versus their own information (a recruiter "
                           "conversation, an insider signal) -- the tool "
                           "cannot make this tradeoff for them.",
    },
    {
        "component": "Adversarial-response decision (Component 6)",
        "tool_decides": "Runs the perturbation test and reports the flip "
                         "rate mechanically.",
        "human_decides": "Whether a 54.6% flip rate at low n means the "
                          "candidate should simply avoid trusting any tier "
                          "near the LOW-CONFIDENCE boundary, regardless of "
                          "what the formula outputs.",
        "override_point": "Human can raise the LOW-CONFIDENCE cutoff above "
                           "n=3 for their own use if they want a more "
                           "conservative tool; the tool does not do this "
                           "automatically.",
    },
    {
        "component": "Uncertainty communication",
        "tool_decides": "Computes and displays the Wilson interval width "
                         "for each scored employer.",
        "human_decides": "Whether a given interval width is 'trustworthy "
                          "enough' for their own risk tolerance -- the tool "
                          "reports the number, not a verdict on adequacy.",
        "override_point": "N/A -- this is informational, not actionable, "
                           "by design.",
    },
    {
        "component": "Data-source / provenance acceptance",
        "tool_decides": "Nothing -- the tool has no mechanism to vet its "
                         "own input data's origin.",
        "human_decides": "Whether the data source (see DATA_SOURCE.md) is "
                          "acceptable for this use, including the disclosed "
                          "fact that it was not independently re-sourced "
                          "from dol.gov/uscis.gov by this project.",
        "override_point": "A human (the candidate, or a course grader) "
                           "signs off on provenance before trusting any "
                           "output -- this is never self-certified by the "
                           "tool.",
    },
]


HARD_STOP_GATE = {
    "trigger": "Any action that would spend money, commit a resource, or "
               "change a person's access.",
    "applies_to_this_engine": [
        "Submitting a job application on the candidate's behalf: BLOCKED. "
        "Requires explicit human action every time.",
        "Auto-messaging an employer or recruiter: BLOCKED. Never implemented.",
        "Silently excluding an employer from the candidate's consideration "
        "set (e.g. hiding INSUFFICIENT_EVIDENCE employers entirely): "
        "BLOCKED -- they are shown, just flagged, per the GIGO gate.",
        "Auto-adjusting the fairness threshold to 'fix' the bias-audit gap "
        "without a human sign-off: BLOCKED -- see delegation map above.",
    ],
    "response_per_trigger": "BLOCK (not flag, not approve) -- none of these "
                            "actions are things this engine is built to do "
                            "at all in its current scope; the gate is "
                            "enforced by the engine simply having no write "
                            "access to any external system, not by a "
                            "runtime check that could be bypassed.",
    "who_resolves": "The candidate (Shreya) for application decisions; "
                    "a human course-grader/supervisor for any proposed "
                    "change to the fairness-metric choice or thresholds.",
    "why_non_negotiable_here": "This engine touches a real, personal, "
                               "high-stakes decision (a visa-dependent "
                               "person's job search). Recommending is "
                               "useful; auto-acting on an unverified, "
                               "confounded, small-n statistical signal "
                               "(Component 5, 6) on someone's behalf would "
                               "be reckless regardless of how good the "
                               "underlying model becomes.",
}


def print_all():
    print("=" * 70)
    print("DELEGATION MAP")
    print("=" * 70)
    for row in DELEGATION_MAP:
        print(f"\n[{row['component']}]")
        for k, v in row.items():
            if k != "component":
                print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("HARD-STOP GATE")
    print("=" * 70)
    for k, v in HARD_STOP_GATE.items():
        print(f"\n{k}:")
        if isinstance(v, list):
            for item in v:
                print(f"  - {item}")
        else:
            print(f"  {v}")


if __name__ == "__main__":
    print_all()
