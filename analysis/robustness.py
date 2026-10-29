"""Identification and power checks on the cached model outputs (no new model calls).

Usage:  python -m analysis.robustness   (after analysis.leakage_index and analysis.knowledge)

Checks, all on the raw-text rung unless stated:
    main            gamma with and without the size term, with minimum detectable effects
                    (80% power, 5% two-sided: 2.8 x SE), in SD of the score
    windows         how the identifying events spread across the intervals between cutoffs
    leave_one_out   gamma and the size interaction with each model dropped in turn
    horizon         model x outcome x time-to-event slopes, so that a later model's better
                    reading of near-term distress cannot load onto gamma
    placebo         one matched control per set inherits its event's date as a pseudo-event;
                    gamma should be zero
    permutation     exact randomisation inference over all 720 assignments of the six
                    stated cutoffs to the six models
    first_stage     probe "yes" rates for events before and after each model's cutoff
    knows_diff      leakage where the model knew of the bankruptcy, prediction against coded
                    distress, in SD units, with a firm-bootstrap test of the difference
    signal          AUC by rung for events no model could know (signal retained by masking)

Writes results/robustness_*.csv and results/robustness_report.md.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from common import INTERIM_DIR, RESULTS_DIR
from diagnostic.leakcheck import estimate
from diagnostic.leakcheck.core import add_knowable

MDE_FACTOR = 2.8
RNG = np.random.default_rng(20261101)


# --------------------------------------------------------------------------- data

def load() -> dict[str, pd.DataFrame]:
    sample = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str})
    pred = pd.read_csv(RESULTS_DIR / "long_predict.csv", dtype={"doc_id": str})
    cons = pd.read_csv(RESULTS_DIR / "long_construct.csv", dtype={"doc_id": str})
    meta = sample[["doc_id", "filing_date", "bankruptcy_date", "match_set", "role"]]
    pred = pred.merge(meta, on="doc_id", how="left")
    cons = cons.merge(meta, on="doc_id", how="left")
    distress = cons[cons.measure == "financial_distress"].copy()
    # Coded distress against bankruptcy only: bankruptcy filers and outcome-free controls.
    bdist = distress[distress.bankruptcy_date.notna() | (distress.outcome == 0)].copy()
    bdist["outcome"] = bdist.bankruptcy_date.notna().astype(int)
    bdist["event_date"] = bdist.bankruptcy_date
    return {
        "Prediction, bankruptcy": pred[pred.measure == "bankruptcy"].copy(),
        "Prediction, pooled": pred.copy(),
        "Coding, distress (bankruptcy)": bdist,
        "Coding, distress (pooled)": distress,
    }


def est(df, **kw):
    kw.setdefault("model_controls", ["log_assets"])
    return estimate(df, unit="unit", model="model", score="score", outcome="outcome",
                    event_date="event_date", cutoff="cutoff", cluster="cik", **kw)


def row(r, **label) -> dict:
    sd = r.score_sd
    out = {**label, "gamma_sd": r.gamma / sd, "ci_low_sd": r.ci_low / sd,
           "ci_high_sd": r.ci_high / sd, "se_sd": r.se / sd, "mde_sd": MDE_FACTOR * r.se / sd,
           "p": r.p_value, "n_identifying": r.n_identifying_units}
    if r.moderator_interaction is not None:
        out.update(size_sd=r.moderator_interaction / sd, size_se_sd=r.moderator_se / sd,
                   size_p=r.moderator_p)
    return out


# --------------------------------------------------------------------- fast gamma

def _design(d: pd.DataFrame, cut: pd.Series, extra: list[str] | None = None):
    keep = d.score.notna()
    d, cut = d[keep], cut[keep]
    models = sorted(d.model.unique())
    know = add_knowable(d.assign(_c=cut), "outcome", "event_date", "_c")
    X = {}
    for m in models[1:]:
        X[f"m{m}"] = (d.model == m).astype(float)
        X[f"o{m}"] = ((d.model == m) & (d.outcome == 1)).astype(float)
    for c in extra or []:
        X[c] = d[c].astype(float)
    X["knowable"] = know
    X = pd.DataFrame(X, index=d.index)
    Xw = X - X.groupby(d.unit).transform("mean")
    yw = d.score - d.score.groupby(d.unit).transform("mean")
    Xw = Xw.loc[:, Xw.abs().sum() > 1e-12]
    return Xw, yw


def gamma_only(d: pd.DataFrame, cut: pd.Series) -> float:
    Xw, yw = _design(d, cut)
    if "knowable" not in Xw:
        return np.nan
    d = d[d.score.notna()]
    beta, *_ = np.linalg.lstsq(Xw.values, yw.values, rcond=None)
    return float(beta[list(Xw.columns).index("knowable")] / d.score.std(ddof=0))


# ------------------------------------------------------------------------ checks

def main_estimates(data) -> pd.DataFrame:
    out = []
    for name, d in data.items():
        g = d[d.level == "raw"]
        out.append(row(est(g), spec=name, size="no"))
        out.append(row(est(g, moderator="log_assets"), spec=name, size="yes"))
    return pd.DataFrame(out)


def windows(data) -> pd.DataFrame:
    d = data["Prediction, pooled"]
    d = d[(d.level == "raw") & (d.outcome == 1)].drop_duplicates("unit")
    cuts = sorted(pd.to_datetime(data["Prediction, pooled"].cutoff.unique()))
    edges = [pd.Timestamp.min] + cuts + [pd.Timestamp.max]
    labels = ["before all cutoffs"] + [f"{a:%b %Y} to {b:%b %Y}" for a, b in zip(cuts, cuts[1:])] \
        + ["after all cutoffs"]
    ev = pd.to_datetime(d.event_date)
    d = d.assign(window=pd.cut(ev, edges, labels=labels, right=False))
    return (d.groupby(["window", "measure"], observed=False).size().unstack(fill_value=0)
             .reset_index())


def leave_one_out(data) -> pd.DataFrame:
    out = []
    for name in ["Prediction, bankruptcy", "Prediction, pooled",
                 "Coding, distress (bankruptcy)", "Coding, distress (pooled)"]:
        g = data[name][data[name].level == "raw"]
        for m in ["none"] + sorted(g.model.unique()):
            h = g if m == "none" else g[g.model != m]
            try:
                out.append(row(est(h, moderator="log_assets"), spec=name, dropped=m))
            except ValueError:
                out.append({"spec": name, "dropped": m})
    return pd.DataFrame(out)


def horizon(data) -> pd.DataFrame:
    """Add model x outcome x years-to-event (and its square) slopes."""
    out = []
    for name, d in data.items():
        g = d[d.level == "raw"].copy()
        yrs = (pd.to_datetime(g.event_date) - pd.to_datetime(g.filing_date)).dt.days / 365.25
        yrs = (yrs - yrs[g.outcome == 1].mean()).where(g.outcome == 1, 0.0).fillna(0.0)
        extra = []
        for m in sorted(g.model.unique())[1:]:
            on = (g.model == m) & (g.outcome == 1)
            g[f"h{m}"] = yrs * on
            g[f"h2{m}"] = yrs ** 2 * on
            extra += [f"h{m}", f"h2{m}"]
        g = g[g.score.notna()]
        Xw, yw = _design(g, g.cutoff, extra)
        import statsmodels.api as sm
        fit = sm.OLS(yw, Xw).fit(cov_type="cluster",
                                 cov_kwds={"groups": pd.factorize(g.cik)[0]})
        sd = g.score.std(ddof=0)
        b, se = fit.params["knowable"], fit.bse["knowable"]
        out.append({"spec": name, "gamma_sd": b / sd, "ci_low_sd": (b - 1.96 * se) / sd,
                    "ci_high_sd": (b + 1.96 * se) / sd, "p": fit.pvalues["knowable"]})
    return pd.DataFrame(out)


def _fit(g: pd.DataFrame, extra: list[str], size: bool) -> dict:
    import statsmodels.api as sm
    g = g[g.score.notna()].copy()
    z = (g.log_assets - g.log_assets.mean()) / g.log_assets.std(ddof=0)
    cols = list(extra)
    if size:
        know = add_knowable(g, "outcome", "event_date", "cutoff")
        g["know_size"] = know * z.fillna(0)
        cols.append("know_size")
    Xw, yw = _design(g, g.cutoff, cols)
    fit = sm.OLS(yw, Xw).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g.cik)[0]})
    sd = g.score.std(ddof=0)
    b, se = fit.params["knowable"], fit.bse["knowable"]
    out = {"gamma_sd": b / sd, "ci_low_sd": (b - 1.96 * se) / sd, "ci_high_sd": (b + 1.96 * se) / sd,
           "p": fit.pvalues["knowable"]}
    if size and "know_size" in fit.params:
        out.update(size_sd=fit.params["know_size"] / sd, size_se_sd=fit.bse["know_size"] / sd,
                   size_p=fit.pvalues["know_size"])
    return out


def model_size(data) -> pd.DataFrame:
    """Size interaction with and without model-specific size slopes, real and placebo."""
    out = []
    for name, d in data.items():
        for sample, g in [("real", d[d.level == "raw"]), ("placebo", _placebo_frame(d))]:
            g = g.copy()
            z = (g.log_assets - g.log_assets.mean()) / g.log_assets.std(ddof=0)
            extra = []
            for m in sorted(g.model.unique())[1:]:
                g[f"sz{m}"] = z.fillna(0) * (g.model == m)
                extra.append(f"sz{m}")
            for ctl, cols in [("no", []), ("model x size", extra)]:
                out.append({"spec": name, "sample": sample, "controls": ctl,
                            **_fit(g, cols, size=True)})
    return pd.DataFrame(out)


def _placebo_frame(d: pd.DataFrame) -> pd.DataFrame:
    g = d[d.level == "raw"].copy()
    ev = g[g.outcome == 1].drop_duplicates("doc_id").set_index("match_set")
    dates = ev.event_date.groupby(level=0).first()
    ctrl = g[(g.role == "control") & g.match_set.isin(dates.index)]
    first = (ctrl.drop_duplicates("doc_id").sort_values("doc_id")
                 .groupby("match_set").doc_id.first())
    p = ctrl.copy()
    p["outcome"] = p.doc_id.isin(set(first)).astype(int)
    p["event_date"] = p.match_set.map(dates).where(p.outcome == 1)
    return p


def placebo(data, reps: int = 1) -> pd.DataFrame:
    out = []
    for name, d in data.items():
        g = d[d.level == "raw"].copy()
        ev = g[g.outcome == 1].drop_duplicates("doc_id").set_index("match_set")
        dates = ev.event_date.groupby(level=0).first()
        ctrl = g[(g.role == "control") & g.match_set.isin(dates.index)]
        first = (ctrl.drop_duplicates("doc_id").sort_values("doc_id")
                     .groupby("match_set").doc_id.first())
        p = ctrl.copy()
        p["outcome"] = p.doc_id.isin(set(first)).astype(int)
        p["event_date"] = p.match_set.map(dates).where(p.outcome == 1)
        if name.startswith("Prediction, pooled"):
            p = p.drop_duplicates(["doc_id", "model", "measure"])
        out.append(row(est(p, moderator="log_assets"), spec=name))
    return pd.DataFrame(out)


def permutation(data) -> pd.DataFrame:
    out = []
    for name in ["Prediction, bankruptcy", "Prediction, pooled",
                 "Coding, distress (bankruptcy)", "Coding, distress (pooled)"]:
        g = data[name][data[name].level == "raw"].copy()
        stated = g.groupby("model").cutoff.first()
        models = list(stated.index)
        obs = gamma_only(g, g.cutoff)
        draws = []
        for perm in itertools.permutations(stated.values):
            mapping = dict(zip(models, perm))
            draws.append(gamma_only(g, g.model.map(mapping)))
        draws = np.array([x for x in draws if np.isfinite(x)])
        out.append({"spec": name, "gamma_sd": obs, "n_perms": len(draws),
                    "p_two_sided": float(np.mean(np.abs(draws) >= abs(obs) - 1e-12)),
                    "perm_q025": float(np.quantile(draws, 0.025)),
                    "perm_q975": float(np.quantile(draws, 0.975))})
    return pd.DataFrame(out)


def first_stage() -> pd.DataFrame:
    r = pd.read_csv(RESULTS_DIR / "knowledge_rates.csv")
    t = r.pivot_table(index=["measure", "model"], columns="status",
                      values=["says_yes", "n"]).reset_index()
    t.columns = ["_".join(c).strip("_") for c in t.columns]
    return t


def knows_diff(reps: int = 300) -> pd.DataFrame:
    """Leakage where the model knew the bankruptcy: prediction vs coded distress, SD units."""
    sample = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str})
    kn = pd.read_csv(RESULTS_DIR / "knowledge_scored.csv", dtype={"doc_id": str})
    kb = kn[kn.measure == "bankruptcy"][["doc_id", "model", "says_yes"]]
    pred = pd.read_csv(RESULTS_DIR / "long_predict.csv", dtype={"doc_id": str})
    cons = pd.read_csv(RESULTS_DIR / "long_construct.csv", dtype={"doc_id": str})
    bp = pred[(pred.measure == "bankruptcy") & (pred.level == "raw")].merge(
        kb, on=["doc_id", "model"], how="left")
    bc = (cons[(cons.measure == "financial_distress") & (cons.level == "raw")]
          .merge(kb, on=["doc_id", "model"], how="left")
          .merge(sample[["doc_id", "bankruptcy_date"]], on="doc_id"))
    bc = bc[bc.bankruptcy_date.notna() | (bc.outcome == 0)].copy()
    bc["outcome"] = bc.bankruptcy_date.notna().astype(int)
    bc["event_date"] = bc.bankruptcy_date
    frames = {}
    for name, d in [("prediction", bp), ("coding", bc)]:
        d = d.fillna({"says_yes": 0})
        d["knows"] = d.says_yes * d.outcome
        frames[name] = d

    def lam(d):
        r = est(d, moderator="knows", standardise_moderator=False)
        return r.moderator_interaction / r.score_sd

    point = {k: lam(v) for k, v in frames.items()}
    firms = frames["prediction"].cik.unique()
    grouped = {k: dict(tuple(d.groupby("cik"))) for k, d in frames.items()}
    boots = []
    for _ in range(reps):
        draw = RNG.choice(firms, len(firms), replace=True)
        counts = pd.Series(draw).value_counts()
        res = {}
        for k, d in frames.items():
            parts = []
            for cik, c in counts.items():
                part = grouped[k].get(cik)
                if part is None:
                    continue
                for j in range(c):
                    parts.append(part.assign(unit=part.unit.astype(str) + f"#{j}",
                                             cik=f"{cik}#{j}"))
            res[k] = lam(pd.concat(parts))
        boots.append(res)
    b = pd.DataFrame(boots)
    diff = b.prediction - b.coding
    d0 = point["prediction"] - point["coding"]
    return pd.DataFrame([{
        "lambda_prediction_sd": point["prediction"], "se_prediction": b.prediction.std(),
        "lambda_coding_sd": point["coding"], "se_coding": b.coding.std(),
        "difference_sd": d0, "se_difference": diff.std(),
        "ci_low": d0 - 1.96 * diff.std(), "ci_high": d0 + 1.96 * diff.std(),
        "p_difference": float(2 * min((diff <= 0).mean(), (diff >= 0).mean())),
        "boot_reps": reps}])


def signal() -> pd.DataFrame:
    a = pd.read_csv(RESULTS_DIR / "auc.csv")
    a = a[a.events == "not_knowable"]
    return (a.groupby(["task", "measure", "level"]).auc.mean().unstack("level")
             .reset_index())


def main() -> None:
    data = load()
    parts = {
        "main": main_estimates(data),
        "windows": windows(data),
        "leave_one_out": leave_one_out(data),
        "horizon": horizon(data),
        "placebo": placebo(data),
        "model_size": model_size(data),
        "permutation": permutation(data),
        "first_stage": first_stage(),
        "knows_diff": knows_diff(),
        "signal": signal(),
    }
    lines = ["# Robustness and power checks", ""]
    for k, df in parts.items():
        df.to_csv(RESULTS_DIR / f"robustness_{k}.csv", index=False)
        lines += [f"## {k}", "", df.round(4).to_markdown(index=False), ""]
    (RESULTS_DIR / "robustness_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
