"""Command-line leakage check for any corpus.

Input: a CSV in long format with one row per (unit, model):
    unit        document identifier
    model       model name (must match a key in the cutoffs file)
    score       the LLM-produced measure
    outcome     1 if the later outcome occurred for this unit, else 0
    event_date  date the outcome occurred (blank if none)
    cluster     optional clustering variable, e.g. firm id
    level       optional grouping, e.g. masking level (one estimate per level)

Cutoffs: a YAML or CSV mapping model -> training cutoff date.

Example:
    python -m diagnostic.leakcheck scores.csv --cutoffs cutoffs.yaml --cluster firm --by level
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from diagnostic.leakcheck.core import auc_table, estimate, verdict


def load_cutoffs(path: Path) -> dict[str, str]:
    if path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(path.read_text())
        if isinstance(data, dict) and "models" in data:  # config/models.yaml format
            return {m["key"]: str(m["training_cutoff"]) for m in data["models"]}
        return {str(k): str(v) for k, v in data.items()}
    df = pd.read_csv(path)
    return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))


def main() -> None:
    p = argparse.ArgumentParser(description="Detect look-ahead leakage in LLM-coded measures.")
    p.add_argument("csv", type=Path)
    p.add_argument("--cutoffs", type=Path, required=True)
    p.add_argument("--unit", default="unit")
    p.add_argument("--model", default="model")
    p.add_argument("--score", default="score")
    p.add_argument("--outcome", default="outcome")
    p.add_argument("--event-date", default="event_date")
    p.add_argument("--cluster", default=None)
    p.add_argument("--moderator", default=None)
    p.add_argument("--by", default=None, help="Column to split estimates by, e.g. level")
    p.add_argument("--json", action="store_true", help="Print JSON instead of text")
    a = p.parse_args()

    df = pd.read_csv(a.csv)
    cutoffs = load_cutoffs(a.cutoffs)
    df["_cutoff"] = df[a.model].astype(str).map(cutoffs)
    if df["_cutoff"].isna().any():
        missing = sorted(df.loc[df["_cutoff"].isna(), a.model].astype(str).unique())
        raise SystemExit(f"No cutoff for models: {missing}")

    groups = [(None, df)] if not a.by else list(df.groupby(a.by))
    out = []
    for key, g in groups:
        r = estimate(g, unit=a.unit, model=a.model, score=a.score, outcome=a.outcome,
                     event_date=a.event_date, cutoff="_cutoff", cluster=a.cluster,
                     moderator=a.moderator, label={a.by: key} if a.by else {})
        aucs = auc_table(g, model=a.model, score=a.score, outcome=a.outcome,
                         event_date=a.event_date, cutoff="_cutoff")
        out.append({"result": r.as_row(), "verdict": verdict(r), "auc": aucs.to_dict("records")})

    if a.json:
        print(json.dumps(out, indent=2, default=str))
        return
    for item in out:
        r = item["result"]
        head = f"[{a.by} = {r.get(a.by)}] " if a.by else ""
        print(f"{head}gamma = {r['gamma']:.4f} (se {r['se']:.4f}, p {r['p_value']:.3g}); "
              f"{r['n_identifying_units']} identifying units")
        print(f"  {item['verdict']}")


if __name__ == "__main__":
    main()
