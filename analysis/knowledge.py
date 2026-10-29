"""Did the models know the outcomes, and did knowing them move their codes?

Usage:  python -m analysis.knowledge   (after probes.knowledge and analysis.leakage_index)

Writes to results/:
    knowledge_rates.csv     share answering "yes", by model, outcome and status
                            (event knowable to the model / event after its
                            cutoff / control firm)
    knowledge_first_stage.csv
                            gamma with the model's "yes" as the score: how much
                            more often a model reports an outcome it could know
    knowledge_leakage.csv   leakage in the coding and prediction tasks, split
                            by whether that model knew that firm's outcome
    knowledge_report.md     plain-language summary
"""

from __future__ import annotations

import pandas as pd

from common import RESULTS_DIR
from diagnostic.leakcheck import estimate
from diagnostic.leakcheck.core import add_knowable


def status(df: pd.DataFrame) -> pd.Series:
    k = add_knowable(df, "outcome", "event_date", "cutoff")
    return pd.Series(
        ["event, knowable" if kk else ("event, after cutoff" if o else "control")
         for kk, o in zip(k, df["outcome"])], index=df.index)


def main() -> None:
    kn = pd.read_csv(RESULTS_DIR / "knowledge_scored.csv", dtype={"doc_id": str})
    kn["status"] = status(kn)

    rates = (kn.groupby(["model", "measure", "status"])
               .agg(n=("says_yes", "size"), says_yes=("says_yes", "mean"),
                    says_unknown=("says_unknown", "mean"))
               .reset_index())
    rates.to_csv(RESULTS_DIR / "knowledge_rates.csv", index=False)

    # First stage: does knowability raise "yes" answers, net of model and firm?
    first = []
    kn["unit"] = kn["doc_id"] + ":" + kn["measure"]
    for label, g in [("pooled", kn)] + [(m, g) for m, g in kn.groupby("measure")]:
        r = estimate(g, unit="unit", model="model", score="says_yes", outcome="outcome",
                     event_date="event_date", cutoff="cutoff", cluster="cik",
                     label={"measure": label})
        first.append(r.as_row())
    first = pd.DataFrame(first)
    first.to_csv(RESULTS_DIR / "knowledge_first_stage.csv", index=False)

    # Leakage split by knowledge: does a model that knows the outcome code differently?
    knows = kn[["doc_id", "model", "measure", "says_yes"]].rename(columns={"says_yes": "knows"})
    pred = pd.read_csv(RESULTS_DIR / "long_predict.csv", dtype={"doc_id": str})
    cons = pd.read_csv(RESULTS_DIR / "long_construct.csv", dtype={"doc_id": str})
    any_knows = (knows[knows["knows"] == 1].groupby(["doc_id", "model"]).size()
                 .rename("knows").clip(upper=1).reset_index())
    out = []
    for task, df, keys in [("predict", pred, ["doc_id", "model", "measure"]),
                           ("construct", cons[cons.measure == "financial_distress"], ["doc_id", "model"])]:
        src = knows if task == "predict" else any_knows
        d = df.merge(src, on=keys, how="left").fillna({"knows": 0})
        # Only a correct "yes" counts as knowing: it must be about an event that happened.
        d["knows"] = d["knows"] * d["outcome"]
        for level, g in d.groupby("level"):
            try:
                r = estimate(g, unit="unit", model="model", score="score", outcome="outcome",
                             event_date="event_date", cutoff="cutoff", cluster="cik",
                             moderator="knows", standardise_moderator=False,
                             label={"task": task, "level": level})
            except ValueError:
                continue
            row = r.as_row()
            row["share_knowable_known"] = float(
                g.loc[add_knowable(g, "outcome", "event_date", "cutoff") == 1, "knows"].mean())
            out.append(row)
    leak = pd.DataFrame(out)
    leak.to_csv(RESULTS_DIR / "knowledge_leakage.csv", index=False)

    ev = rates[rates.status != "control"]
    lines = ["# Knowledge probe", "",
             "## Share of models answering 'yes'", "",
             rates.pivot_table(index=["measure", "model"], columns="status", values="says_yes")
                  .round(3).to_markdown(), "",
             "## First stage: extra 'yes' when the outcome is knowable", "",
             first[["measure", "gamma", "se", "p_value", "n_identifying_units"]].round(4)
                  .to_markdown(index=False), "",
             "## Leakage among models that knew the outcome", "",
             "`gamma` = leakage when the model did not report knowing the outcome; "
             "`moderator_interaction` = additional leakage when it did.", "",
             leak[["task", "level", "share_knowable_known", "gamma", "moderator_interaction",
                   "moderator_se", "moderator_p"]].round(4).to_markdown(index=False)
             if not leak.empty else "_not estimable_", ""]
    _ = ev
    (RESULTS_DIR / "knowledge_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
