"""Figure 2: re-identification and belief-driven shifts across the masking ladder.

Usage:  python -m analysis.figure2   (after analysis.knowledge and probes.reidentify)
Writes results/figures/figure2_masking_and_belief.png
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import RESULTS_DIR

LEV = ["raw", "names", "generalised", "paraphrased"]
LAB = ["Raw", "Names\nremoved", "Dates and amounts\ngeneralised", "Paraphrased"]


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    r = pd.read_csv(RESULTS_DIR / "reid_rates.csv")
    k = pd.read_csv(RESULTS_DIR / "knowledge_leakage.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.1), dpi=200)
    x = np.arange(4)
    piv = r.pivot_table(index="level", columns="model", values="hit").reindex(LEV) * 100
    a.fill_between(x, piv.min(axis=1), piv.max(axis=1), color="#2f6fb0", alpha=0.15, lw=0,
                   label="Range across six models")
    for m in piv.columns:
        a.plot(x, piv[m], color="#2f6fb0", alpha=0.35, lw=0.8)
    a.plot(x, piv.mean(axis=1), "o-", color="#2f6fb0", lw=2.2, ms=6, label="Average of six models")
    a.set_ylim(0, 100)
    a.set_ylabel("Filings whose firm the model names (%)")
    a.set_title("A. Removing names does not hide the firm", loc="left", fontsize=10, fontweight="bold")
    a.legend(frameon=False, loc="lower left", fontsize=8)
    for task, lab, col, off in [("predict_bankruptcy", "Predicted bankruptcy risk", "#2f6fb0", -0.07),
                                ("construct_bankruptcy_events", "Coded financial distress", "#c2541c", 0.07)]:
        g = k[k.task == task].set_index("level").reindex(LEV)
        est = (g.moderator_interaction / g.score_sd).values
        ci = 1.96 * (g.moderator_se / g.score_sd).values
        b.errorbar(x + off, est, yerr=ci, fmt="o-", color=col, lw=2, ms=6, capsize=3, label=lab)
    b.axhline(0, color="#6b7280", lw=0.9)
    b.set_ylim(-0.2, 0.38)
    b.set_ylabel("Shift where the model believes the firm\nwent bankrupt (SD of score, 95% CI)")
    b.set_title("B. Belief about the firm shifts predictions, not codes", loc="left", fontsize=10,
                fontweight="bold")
    b.legend(frameon=False, loc="lower left", fontsize=8)
    for ax in (a, b):
        ax.set_xticks(x, LAB, fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e7eb", lw=0.8)
        ax.set_axisbelow(True)
    fig.tight_layout(w_pad=3)
    out = RESULTS_DIR / "figures" / "figure2_masking_and_belief.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
