"""Sensitivity of leakage estimates to shifting every stated cutoff.

Usage:  python -m analysis.sensitivity
Writes results/cutoff_sensitivity.csv (raw text; no size moderator).
"""

from __future__ import annotations

import pandas as pd

from common import RESULTS_DIR
from diagnostic.leakcheck import estimate

SHIFTS = [-6, -3, 0, 3, 6]


def main() -> None:
    pred = pd.read_csv(RESULTS_DIR / "long_predict.csv")
    cons = pd.read_csv(RESULTS_DIR / "long_construct.csv")
    sets = {
        ("predict", "all_outcomes"): pred,
        ("predict", "bankruptcy"): pred[pred.measure == "bankruptcy"],
        ("construct", "financial_distress"): cons[cons.measure == "financial_distress"],
    }
    rows = []
    for months in SHIFTS:
        for (task, measure), df in sets.items():
            d = df[df.level == "raw"].copy()
            d["shifted"] = (pd.to_datetime(d.cutoff) + pd.DateOffset(months=months)).dt.strftime("%Y-%m-%d")
            r = estimate(d, unit="unit", model="model", score="score", outcome="outcome",
                         event_date="event_date", cutoff="shifted", cluster="cik")
            rows.append({"shift_months": months, "task": task, "measure": measure,
                         "gamma_std": r.gamma_std, "ci_low_std": r.ci_low / r.score_sd,
                         "ci_high_std": r.ci_high / r.score_sd, "p_value": r.p_value,
                         "n_identifying_units": r.n_identifying_units})
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS_DIR / "cutoff_sensitivity.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
