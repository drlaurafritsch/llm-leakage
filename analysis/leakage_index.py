"""Estimate leakage for every task, measure and masking level.

Usage:  python -m analysis.leakage_index

Reads data/interim/sample.csv, results/model_outputs.jsonl and (if present)
results/reidentify_scored.csv. Writes to results/:
    long_predict.csv, long_construct.csv   analysis-ready long frames
    leakage_estimates.csv                  one row per task x measure x level
    auc.csv                                discrimination, knowable vs not
    reid_rates.csv                         re-identification by model and level
    report.md                              plain-language summary
"""

from __future__ import annotations

import pandas as pd

from common import INTERIM_DIR, RESULTS_DIR, load_config, read_jsonl
from diagnostic.leakcheck import auc_table, estimate, verdict
from masking.mask import LEVELS

CONSTRUCTS = ["financial_distress", "managerial_optimism", "risk_candour"]


def outcome_names() -> list[str]:
    return list(load_config("sample")["outcomes"])


def load_outputs() -> pd.DataFrame:
    rows = list({r["key"]: r for r in read_jsonl(RESULTS_DIR / "model_outputs.jsonl")
                 if r.get("parsed")}.values())
    if not rows:
        raise SystemExit("No model outputs yet; run python -m coding.run_models first.")
    return pd.DataFrame(rows)


def load_sample() -> pd.DataFrame:
    s = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str})
    date_cols = [f"{o}_date" for o in outcome_names()]
    s["first_event_date"] = s[date_cols].apply(pd.to_datetime, errors="coerce").min(axis=1)
    return s


def build_long(outputs: pd.DataFrame, sample: pd.DataFrame):
    keep = ["doc_id", "cik", "log_assets", "first_event_date", "any_event"] + [
        f"{o}_date" for o in outcome_names()]
    base = sample[keep]
    out = outputs.merge(base, on="doc_id", how="inner")
    out["parsed"] = out["parsed"].map(lambda p: p if isinstance(p, dict) else {})

    pred_rows, cons_rows = [], []
    for r in out.itertuples():
        common = {"doc_id": r.doc_id, "cik": r.cik, "model": r.model, "level": r.level,
                  "cutoff": r.training_cutoff, "log_assets": r.log_assets}
        if r.task == "predict":
            for o in outcome_names():
                ev = getattr(r, f"{o}_date")
                pred_rows.append({**common, "measure": o, "unit": f"{r.doc_id}:{o}",
                                  "score": pd.to_numeric(r.parsed.get(o), errors="coerce"),
                                  "outcome": int(pd.notna(ev)), "event_date": ev})
        elif r.task == "construct":
            for c in CONSTRUCTS:
                cons_rows.append({**common, "measure": c, "unit": r.doc_id,
                                  "score": pd.to_numeric(r.parsed.get(c), errors="coerce"),
                                  "outcome": int(r.any_event), "event_date": r.first_event_date})
    return pd.DataFrame(pred_rows), pd.DataFrame(cons_rows)


def estimates_for(df: pd.DataFrame, task: str, pooled_label: str | None) -> tuple[list, list]:
    rows, aucs = [], []
    if df.empty:
        return rows, aucs
    groups = []
    for (measure, level), g in df.groupby(["measure", "level"]):
        groups.append((measure, level, g))
    if pooled_label:
        for level, g in df.groupby("level"):
            groups.append((pooled_label, level, g))
    for measure, level, g in groups:
        label = {"task": task, "measure": measure, "level": level}
        try:
            r = estimate(g, unit="unit", model="model", score="score", outcome="outcome",
                         event_date="event_date", cutoff="cutoff", cluster="cik", model_controls=["log_assets"],
                         label=label)
        except ValueError as err:
            rows.append({**label, "note": str(err)})
            continue
        row = r.as_row()
        row["verdict"] = verdict(r)
        rows.append(row)
        if measure == pooled_label:
            # AUC across outcome types with different base rates is not meaningful.
            continue
        a = auc_table(g, model="model", score="score", outcome="outcome",
                      event_date="event_date", cutoff="cutoff")
        a = a.assign(**label)
        aucs.append(a)
    return rows, aucs


def reid_with_leakage(long: pd.DataFrame) -> pd.DataFrame | None:
    """Does leakage concentrate where the model can re-identify the firm?"""
    path = RESULTS_DIR / "reidentify_scored.csv"
    if not path.exists() or long.empty:
        return None
    reid = pd.read_csv(path, dtype={"doc_id": str})
    m = long.merge(reid[["doc_id", "model", "level", "hit"]], on=["doc_id", "model", "level"],
                   how="left")
    rows = []
    for level, g in m.groupby("level"):
        if g["hit"].isna().all():
            continue
        try:
            r = estimate(g.fillna({"hit": 0}), unit="unit", model="model", score="score",
                         outcome="outcome", event_date="event_date", cutoff="cutoff",
                         cluster="cik", model_controls=["log_assets"], moderator="hit", standardise_moderator=False,
                         label={"level": level})
        except ValueError:
            continue
        rows.append({"level": level, "gamma_if_not_identified": r.gamma,
                     "extra_gamma_if_identified": r.moderator_interaction,
                     "se_extra": r.moderator_se, "p_extra": r.moderator_p})
    return pd.DataFrame(rows)


def level_order(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["level"] = pd.Categorical(df["level"], categories=LEVELS, ordered=True)
    return df.sort_values([c for c in ("task", "measure", "level") if c in df.columns])


def write_report(est: pd.DataFrame, reid_rates: pd.DataFrame | None,
                 reid_leak: pd.DataFrame | None) -> str:
    lines = ["# Leakage report", ""]
    for (task, measure), g in est.groupby(["task", "measure"], observed=True):
        lines.append(f"## {task}: {measure}")
        for r in g.itertuples():
            if isinstance(getattr(r, "verdict", None), str):
                lines.append(f"- **{r.level}**: {r.verdict}")
            else:
                lines.append(f"- **{r.level}**: {getattr(r, 'note', 'not estimated')}")
        lines.append("")
    if reid_rates is not None and not reid_rates.empty:
        lines += ["## Re-identification rate by masking level", "",
                  reid_rates.to_markdown(index=False, floatfmt=".2f"), ""]
    if reid_leak is not None and not reid_leak.empty:
        lines += ["## Leakage split by re-identification (pooled prediction)", "",
                  reid_leak.to_markdown(index=False, floatfmt=".3f"), ""]
    return "\n".join(lines)


def main() -> None:
    outputs, sample = load_outputs(), load_sample()
    long_pred, long_cons = build_long(outputs, sample)
    long_pred.to_csv(RESULTS_DIR / "long_predict.csv", index=False)
    long_cons.to_csv(RESULTS_DIR / "long_construct.csv", index=False)

    rows_p, auc_p = estimates_for(long_pred, "predict", pooled_label="all_outcomes")
    rows_c, auc_c = estimates_for(long_cons, "construct", pooled_label=None)
    est = level_order(pd.DataFrame(rows_p + rows_c))
    est.to_csv(RESULTS_DIR / "leakage_estimates.csv", index=False)
    if auc_p or auc_c:
        pd.concat(auc_p + auc_c).to_csv(RESULTS_DIR / "auc.csv", index=False)

    reid_rates = None
    path = RESULTS_DIR / "reidentify_scored.csv"
    if path.exists():
        reid = pd.read_csv(path)
        reid_rates = level_order(reid.groupby(["model", "level"], as_index=False)["hit"].mean())
        reid_rates.to_csv(RESULTS_DIR / "reid_rates.csv", index=False)
    reid_leak = reid_with_leakage(long_pred)

    report = write_report(est, reid_rates, reid_leak)
    (RESULTS_DIR / "report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
