"""
Regenerates figures/uncertainty_bands.png from real engine output.
Addresses a disclosed gap: the original figure had no generating script
in the repo. This one is real, runs, and produces a comparable chart --
though it will not pixel-match the original exactly, since exact company
selection for a "contrasting examples" chart is itself a judgment call
(see figure caption for what selection rule this version uses).

Run: python3 src/make_uncertainty_figure.py
"""

import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "data/engine_output.csv"
OUT_PATH = "figures/uncertainty_bands.png"


def build_figure(df):
    scored = df[df["wilson_lower"].notnull()].copy()

    # Selection rule, stated explicitly (this is a judgment call, not a
    # record): 6 highest-volume PRIORITIZE employers (narrow bands) +
    # 6 lowest-volume employers at exactly total_filed==4 (widest bands
    # at the LOW-CONFIDENCE boundary), for the starkest same-rate-different-
    # trust contrast. This is 12 companies, NOT "top-15" -- correcting an
    # earlier caption error.
    high_volume = scored.sort_values("total_filed", ascending=False).head(6)
    low_volume = scored[scored["total_filed"] == 4].sort_values(
        "point_rate", ascending=False
    ).head(6)
    combined = pd.concat([high_volume, low_volume]).sort_values(
        "point_rate", ascending=False
    )

    fig, ax = plt.subplots(figsize=(11, 7))
    y_pos = range(len(combined))

    for i, (_, row) in enumerate(combined.iterrows()):
        color = "steelblue" if row["total_filed"] >= 100 else "indianred"
        ax.plot([row["wilson_lower"], row["wilson_upper"]], [i, i],
                color=color, linewidth=6, alpha=0.6, solid_capstyle="round")
        ax.scatter(row["point_rate"], i, color="black", zorder=5, s=40)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([
        f"{row['company_name']} (n={int(row['total_filed'])})"
        for _, row in combined.iterrows()
    ])
    ax.axvline(0.70, color="green", linestyle="--", alpha=0.6, label="PRIORITIZE threshold (70%)")
    ax.axvline(0.40, color="orange", linestyle="--", alpha=0.6, label="CONSIDER threshold (40%)")
    ax.set_xlabel("Approval rate (with 95% Wilson interval)")
    ax.set_title(
        "Same-looking point estimate, very different trust level\n"
        "blue = high filing volume (narrow band) | red = low filing volume (wide band)"
    )
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150)
    print(f"Figure written to {OUT_PATH} ({len(combined)} companies shown, not 'top-15' -- see selection rule in source)")


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    build_figure(df)
