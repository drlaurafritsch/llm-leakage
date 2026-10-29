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


def _size_cols(g: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Model-specific slopes on standardised log assets (the main specification)."""
    g = g.copy()
    z = ((g.log_assets - g.log_assets.mean()) / g.log_assets.std(ddof=0)).fillna(0)
    cols = []
    for m in sorted(g.model.unique())[1:]:
        g[f"sz{m}"] = z * (g.model == m)
        cols.append(f"sz{m}")
    return g, cols


def gamma_only(d: pd.DataFrame, cut: pd.Series, extra: list[str] | None = None) -> float:
    Xw, yw = _design(d, cut, extra)
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
                out.append(row(est(h), spec=name, dropped=m))
            except ValueError:
                out.append({"spec": name, "dropped": m})
    return pd.DataFrame(out)


def horizon(data) -> pd.DataFrame:
    """Add model x outcome x years-to-event (and its square) slopes."""
    out = []
    for name, d in data.items():
        g, extra = _size_cols(d[d.level == "raw"])
        yrs = (pd.to_datetime(g.event_date) - pd.to_datetime(g.filing_date)).dt.days / 365.25
        yrs = (yrs - yrs[g.outcome == 1].mean()).where(g.outcome == 1, 0.0).fillna(0.0)
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
        out.append(row(est(p), spec=name))
    return pd.DataFrame(out)


def permutation(data) -> pd.DataFrame:
    out = []
    for name in ["Prediction, bankruptcy", "Prediction, pooled",
                 "Coding, distress (bankruptcy)", "Coding, distress (pooled)"]:
        g, extra = _size_cols(data[name][data[name].level == "raw"])
        stated = g.groupby("model").cutoff.first()
        models = list(stated.index)
        obs = gamma_only(g, g.cutoff, extra)
        draws = []
        for perm in itertools.permutations(stated.values):
            mapping = dict(zip(models, perm))
            draws.append(gamma_only(g, g.model.map(mapping), extra))
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


# ----------------------------------------------------- round-two checks (v3)

def _ols(Xw, yw, groups):
    import statsmodels.api as sm
    return sm.OLS(yw, Xw).fit(method="pinv", cov_type="cluster",
                              cov_kwds={"groups": pd.factorize(groups)[0]})


def stacked(data) -> pd.DataFrame:
    """Clean comparisons for staggered cutoffs.

    For each pair of adjacent cutoffs k, k+1, keep the models up to k+1, the controls,
    and the events dated on or after cutoff k. Events dated between the two cutoffs are
    knowable only to model k+1; events after cutoff k+1 are knowable to none of these
    models and serve as not-yet-knowable comparisons. Events already knowable to an
    earlier model are dropped, so no already-treated observation acts as a control.
    The stacks are estimated jointly with stack-specific document, model, outcome-slope
    and size-slope terms. A window is skipped if fewer than 10 later events remain.
    """
    out = []
    for name in ["Prediction, bankruptcy", "Prediction, pooled",
                 "Coding, distress (bankruptcy)", "Coding, distress (pooled)"]:
        g = data[name][data[name].level == "raw"]
        g = g[g.score.notna()].copy()
        sd = g.score.std(ddof=0)
        order = g.groupby("model").cutoff.first().pipe(pd.to_datetime).sort_values()
        ev = pd.to_datetime(g.event_date)
        parts, windows = [], []
        for k in range(len(order) - 1):
            ck, ck1 = order.iloc[k], order.iloc[k + 1]
            keep = g.model.isin(order.index[: k + 2]) & ((g.outcome == 0) | (ev >= ck))
            h = g[keep].copy()
            e = pd.to_datetime(h.event_date)
            n_win = h[(h.outcome == 1) & (e < ck1)].unit.nunique()
            n_later = h[(h.outcome == 1) & (e >= ck1)].unit.nunique()
            windows.append({"spec": name, "treated_model": order.index[k + 1],
                            "window": f"{ck:%b %Y} to {ck1:%b %Y}",
                            "events_in_window": n_win, "later_events": n_later})
            if n_win == 0 or n_later < 10:
                windows[-1]["used"] = False
                continue
            windows[-1]["used"] = True
            try:
                r = est(h)
                windows[-1].update(gamma_sd=r.gamma / sd, se_sd=r.se / sd, p=r.p_value)
            except ValueError:
                pass
            h["unit"] = f"{k}|" + h.unit.astype(str)
            h["model"] = f"{k}|" + h.model.astype(str)
            parts.append(h)
        S = pd.concat(parts)
        S["stack"] = S.unit.str.split("|").str[0]
        z = ((S.log_assets - S.log_assets.mean()) / S.log_assets.std(ddof=0)).fillna(0)
        X = {}
        for k, gk in S.groupby("stack"):
            ref = sorted(gk.model.unique())[0]
            for m in sorted(gk.model.unique()):
                if m == ref:
                    continue
                on = S.model == m
                X[f"m{m}"] = on.astype(float)
                X[f"o{m}"] = (on & (S.outcome == 1)).astype(float)
                X[f"s{m}"] = z * on
        X["knowable"] = add_knowable(S, "outcome", "event_date", "cutoff")
        X = pd.DataFrame(X, index=S.index)
        Xw = X - X.groupby(S.unit).transform("mean")
        yw = S.score - S.score.groupby(S.unit).transform("mean")
        Xw = Xw.loc[:, Xw.abs().sum() > 1e-12]
        fit = _ols(Xw, yw, S.cik)
        b, se = fit.params["knowable"], fit.bse["knowable"]
        out.append({"spec": name, "gamma_sd": b / sd, "ci_low_sd": (b - 1.96 * se) / sd,
                    "ci_high_sd": (b + 1.96 * se) / sd, "p": fit.pvalues["knowable"],
                    "windows_used": int(sum(w.get("used", False) for w in windows)),
                    "identifying_events": int(sum(w["events_in_window"] for w in windows
                                                  if w.get("used")))})
        STACK_WINDOWS.extend(windows)
    return pd.DataFrame(out)


STACK_WINDOWS: list[dict] = []


def shifts_bankruptcy_filers(data) -> pd.DataFrame:
    """Cutoff shifts for coded distress among bankruptcy filers (main specification)."""
    out = []
    g0 = data["Coding, distress (bankruptcy)"]
    g0 = g0[g0.level == "raw"]
    for months in (-6, -3, 3, 6):
        g = g0.copy()
        g["cutoff"] = (pd.to_datetime(g.cutoff) + pd.DateOffset(months=months)).dt.strftime("%Y-%m-%d")
        out.append(row(est(g), spec="Coding, distress (bankruptcy)", shift_months=months))
    return pd.DataFrame(out)


def donut(data, days: int = 182) -> pd.DataFrame:
    """Drop event-model pairs whose event falls within `days` of that model's cutoff."""
    out = []
    for name, d in data.items():
        g = d[d.level == "raw"].copy()
        gap = (pd.to_datetime(g.event_date) - pd.to_datetime(g.cutoff)).dt.days.abs()
        g = g[~((g.outcome == 1) & (gap < days))]
        out.append(row(est(g), spec=name, donut_days=days))
    return pd.DataFrame(out)


def _knowledge_frames(level: str | None = None) -> dict[str, pd.DataFrame]:
    sample = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str})
    kn = pd.read_csv(RESULTS_DIR / "knowledge_scored.csv", dtype={"doc_id": str})
    kb = kn[kn.measure == "bankruptcy"][["doc_id", "model", "says_yes"]]
    pred = pd.read_csv(RESULTS_DIR / "long_predict.csv", dtype={"doc_id": str})
    cons = pd.read_csv(RESULTS_DIR / "long_construct.csv", dtype={"doc_id": str})
    bp = pred[pred.measure == "bankruptcy"].merge(kb, on=["doc_id", "model"], how="left")
    bc = (cons[cons.measure == "financial_distress"]
          .merge(kb, on=["doc_id", "model"], how="left")
          .merge(sample[["doc_id", "bankruptcy_date"]], on="doc_id"))
    bc = bc[bc.bankruptcy_date.notna() | (bc.outcome == 0)].copy()
    bc["outcome"] = bc.bankruptcy_date.notna().astype(int)
    bc["event_date"] = bc.bankruptcy_date
    out = {}
    for name, d in [("prediction", bp), ("coding", bc)]:
        d = d[d.score.notna()].fillna({"says_yes": 0}).copy()
        if level:
            d = d[d.level == level]
        out[name] = d
    return out


def knows_checks(reps: int = 300) -> pd.DataFrame:
    """Falsification and heterogeneity checks for the knowledge-conditional estimate."""
    rows = []
    reid = pd.read_csv(RESULTS_DIR / "reidentify_scored.csv", dtype={"doc_id": str})
    for task, d in _knowledge_frames().items():
        unit = 100 if task == "prediction" else 1
        sd = d[d.level == "raw"].score.std(ddof=0)
        g = d[d.level == "raw"].copy()
        know = add_knowable(g, "outcome", "event_date", "cutoff")
        g["yes_knowable"] = g.says_yes * g.outcome * know
        g["yes_unknowable_event"] = g.says_yes * g.outcome * (1 - know)
        g["yes_control"] = g.says_yes * (1 - g.outcome)
        g, sz = _size_cols(g)
        Xw, yw = _design(g, g.cutoff, sz + ["yes_knowable", "yes_unknowable_event", "yes_control"])
        fit = _ols(Xw, yw, g.cik)
        for c in ["yes_knowable", "yes_unknowable_event", "yes_control"]:
            rows.append({"task": task, "check": f"falsification: {c}",
                         "coef": fit.params[c] * unit, "se": fit.bse[c] * unit,
                         "p": fit.pvalues[c], "coef_sd": fit.params[c] / sd,
                         "n_yes": int(g[c].sum())})
        # Recall minus belief: does a correct "yes" move scores more than a wrong one?
        cov = fit.cov_params()
        diff = fit.params["yes_knowable"] - fit.params["yes_control"]
        dse = float(np.sqrt(cov.loc["yes_knowable", "yes_knowable"]
                            + cov.loc["yes_control", "yes_control"]
                            - 2 * cov.loc["yes_knowable", "yes_control"]))
        from scipy.stats import norm
        rows.append({"task": task, "check": "recall minus belief (knowable yes - control yes)",
                     "coef": diff * unit, "se": dse * unit, "p": float(2 * norm.sf(abs(diff / dse))),
                     "ci_low": (diff - 1.96 * dse) * unit, "ci_high": (diff + 1.96 * dse) * unit})
        # The control falsification without Llama 4 Maverick (highest false-alarm rate).
        h = g[g.model != "llama4"].copy()
        h, sz2 = _size_cols(h.drop(columns=[c for c in h.columns if c.startswith("sz")]))
        Xw2, yw2 = _design(h, h.cutoff, sz2 + ["yes_knowable", "yes_unknowable_event", "yes_control"])
        f2 = _ols(Xw2, yw2, h.cik)
        rows.append({"task": task, "check": "falsification without Llama 4: yes_control",
                     "coef": f2.params["yes_control"] * unit, "se": f2.bse["yes_control"] * unit,
                     "p": f2.pvalues["yes_control"], "n_yes": int(h.yes_control.sum())})
        rows.append({"task": task, "check": "falsification without Llama 4: yes_knowable",
                     "coef": f2.params["yes_knowable"] * unit, "se": f2.bse["yes_knowable"] * unit,
                     "p": f2.pvalues["yes_knowable"], "n_yes": int(h.yes_knowable.sum())})
        # Without Llama 4 Maverick, whose probe says yes to 9% of controls.
        h = d[(d.level == "raw") & (d.model != "llama4")].copy()
        h["knows"] = h.says_yes * h.outcome
        r = est(h, moderator="knows", standardise_moderator=False)
        rows.append({"task": task, "check": "without Llama 4 Maverick",
                     "coef": r.moderator_interaction * unit, "se": r.moderator_se * unit,
                     "p": r.moderator_p, "coef_sd": r.moderator_interaction / r.score_sd})
        # Does knowledge-linked leakage concentrate where the model also re-identifies?
        h = d[d.level == "raw"].merge(reid[reid.level == "raw"][["doc_id", "model", "hit"]],
                                      on=["doc_id", "model"], how="left").fillna({"hit": 0})
        know = add_knowable(h, "outcome", "event_date", "cutoff")
        h["kk"] = h.says_yes * h.outcome * know
        h["kk_hit"] = h.kk * h.hit
        h["know_hit"] = know * h.hit
        h, sz = _size_cols(h)
        Xw, yw = _design(h, h.cutoff, sz + ["kk", "know_hit", "kk_hit"])
        fit = _ols(Xw, yw, h.cik)
        for c in ["kk", "kk_hit", "know_hit"]:
            rows.append({"task": task, "check": f"re-identification split: {c}",
                         "coef": fit.params[c] * unit, "se": fit.bse[c] * unit,
                         "p": fit.pvalues[c], "coef_sd": fit.params[c] / sd,
                         "n_yes": int((h[c] != 0).sum())})
        # Raw against paraphrased: firm bootstrap of the difference in the knowledge effect.
        def lam(frame):
            f = frame.copy()
            f["knows"] = f.says_yes * f.outcome
            r = est(f, moderator="knows", standardise_moderator=False)
            return r.moderator_interaction * unit
        raw, par = d[d.level == "raw"], d[d.level == "paraphrased"]
        point = lam(raw) - lam(par)
        gr = dict(tuple(raw.groupby("cik"))); gp = dict(tuple(par.groupby("cik")))
        firms = raw.cik.unique()
        diffs = []
        for _ in range(reps):
            counts = pd.Series(RNG.choice(firms, len(firms), replace=True)).value_counts()
            fr, fp = [], []
            for cik, c in counts.items():
                for j in range(c):
                    for src, dst in ((gr, fr), (gp, fp)):
                        part = src.get(cik)
                        if part is not None:
                            dst.append(part.assign(unit=part.unit.astype(str) + f"#{j}",
                                                   cik=f"{cik}#{j}"))
            diffs.append(lam(pd.concat(fr)) - lam(pd.concat(fp)))
        diffs = np.array(diffs)
        rows.append({"task": task, "check": "raw minus paraphrased (bootstrap)",
                     "coef": point, "se": diffs.std(),
                     "p": float(2 * min((diffs <= 0).mean(), (diffs >= 0).mean())),
                     "ci_low": float(np.quantile(diffs, 0.025)),
                     "ci_high": float(np.quantile(diffs, 0.975))})
    return pd.DataFrame(rows)


def main() -> None:
    data = load()
    parts = {
        "main": main_estimates(data),
        "windows": windows(data),
        "leave_one_out": leave_one_out(data),
        "horizon": horizon(data),
        "placebo": placebo(data),
        "model_size": model_size(data),
        "stacked": stacked(data),
        "stacked_windows": None,
        "donut": pd.concat([donut(data, 182), donut(data, 365)]),
        "knows_checks": knows_checks(),
        "shifts_bankruptcy_filers": shifts_bankruptcy_filers(data),
        "permutation": permutation(data),
        "first_stage": first_stage(),
        "knows_diff": knows_diff(),
        "signal": signal(),
    }
    lines = ["# Robustness and power checks", ""]
    parts["stacked_windows"] = pd.DataFrame(STACK_WINDOWS)
    for k, df in parts.items():
        df.to_csv(RESULTS_DIR / f"robustness_{k}.csv", index=False)
        lines += [f"## {k}", "", df.round(4).to_markdown(index=False), ""]
    (RESULTS_DIR / "robustness_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
