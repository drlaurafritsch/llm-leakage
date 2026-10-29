"""leakcheck: detect look-ahead leakage in LLM-based measures of dated text.

Problem
-------
An LLM that codes historical text (a 10-K, a project filing, a speech) may
already have read about what happened next. Its codes then partly reflect
the future rather than the document, which contaminates any study that treats
those codes as measured at the time of writing.

Design
------
Code the same documents with several models whose training cutoffs differ.
An outcome that happened before a model's cutoff is "knowable" to that model.
Leakage is the extra shift in a model's score when the outcome is knowable to
it, compared with the same outcome scored by models that could not know it,
net of each model's general ability to read outcome-relevant signals from text:

    score[u,m] = a[u] + b[m] + c[m] * outcome[u] + gamma * knowable[u,m] + e

    a[u]          unit fixed effect (absorbs everything about the document)
    b[m]          model fixed effect (scale differences between models)
    c[m]*outcome  model-specific discrimination relative to a reference model
    knowable      outcome[u] == 1 and event_date[u] < cutoff[m]
    gamma         leakage

gamma is identified from outcomes that fall between model cutoffs. Standard
errors are clustered (by firm, by default). The function reports how many
units actually identify gamma, so an uninformative design is visible at once.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score


@dataclass
class LeakageResult:
    gamma: float
    se: float
    p_value: float
    ci_low: float
    ci_high: float
    gamma_std: float            # gamma in standard deviations of the score
    score_sd: float
    n_obs: int
    n_units: int
    n_identifying_units: int    # units whose outcome is knowable to some models only
    mde_std: float = float("nan")  # minimum detectable effect, SD units (80% power, 5% two-sided)
    moderator_interaction: float | None = None
    moderator_se: float | None = None
    moderator_p: float | None = None
    label: dict = field(default_factory=dict)

    def as_row(self) -> dict:
        row = {k: v for k, v in asdict(self).items() if k != "label"}
        row.update(self.label)
        return row


def add_knowable(df: pd.DataFrame, outcome: str, event_date: str, cutoff: str) -> pd.Series:
    ev = pd.to_datetime(df[event_date], errors="coerce")
    cut = pd.to_datetime(df[cutoff], errors="coerce")
    return ((df[outcome] == 1) & ev.notna() & (ev < cut)).astype(float)


def _demean(frame: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    return frame - frame.groupby(groups).transform("mean")


def estimate(
    df: pd.DataFrame,
    *,
    unit: str,
    model: str,
    score: str,
    outcome: str,
    event_date: str,
    cutoff: str,
    cluster: str | None = None,
    moderator: str | None = None,
    standardise_moderator: bool = True,
    model_controls: list[str] | tuple[str, ...] = (),
    label: dict | None = None,
) -> LeakageResult:
    """Estimate gamma on a long frame with one row per (unit, model).

    model_controls: document-level covariates (e.g. log assets) given a separate
    slope for each model. Without them, a later model's different treatment of,
    say, large firms can load onto knowability and onto its interactions.
    """
    keep = {unit, model, score, outcome, event_date, cutoff, cluster, moderator, *model_controls}
    d = df[[c for c in keep if c]].copy()
    d = d[d[score].notna()]
    d["_knowable"] = add_knowable(d, outcome, event_date, cutoff)

    models = sorted(d[model].unique())
    X = pd.DataFrame(index=d.index)
    for m in models[1:]:
        X[f"model[{m}]"] = (d[model] == m).astype(float)
    # The outcome main effect is absorbed by the unit effects, so one model's
    # outcome interaction is the reference; including all would be collinear.
    for m in models[1:]:
        X[f"outcome:model[{m}]"] = ((d[model] == m) & (d[outcome] == 1)).astype(float)
    for c in model_controls:
        zc = d[c].astype(float)
        zc = ((zc - zc.mean()) / zc.std(ddof=0)).fillna(0) if zc.std(ddof=0) > 0 else zc * 0
        for m in models[1:]:
            X[f"{c}:model[{m}]"] = zc * (d[model] == m)
    X["knowable"] = d["_knowable"]
    if moderator:
        z = d[moderator].astype(float)
        if standardise_moderator:
            z = (z - z.mean()) / z.std(ddof=0) if z.std(ddof=0) > 0 else z * 0
        X["knowable:moderator"] = d["_knowable"] * z.fillna(0)

    y = d[score].astype(float)
    Xw = _demean(X, d[unit])
    yw = y - y.groupby(d[unit]).transform("mean")
    Xw = Xw.loc[:, Xw.abs().sum() > 1e-12]  # drop columns absorbed by unit effects
    if "knowable" not in Xw.columns:
        raise ValueError(
            "No unit has an outcome that is knowable to some models and not others; "
            "gamma is not identified. Check cutoffs, event dates and sample years."
        )

    groups = d[cluster] if cluster else d[unit]
    fit = sm.OLS(yw, Xw).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})
    gamma, se = fit.params["knowable"], fit.bse["knowable"]
    ci = fit.conf_int().loc["knowable"]

    k = d.groupby(d[unit])["_knowable"]
    identifying = int(((k.max() - k.min()) > 0).sum())
    result = LeakageResult(
        gamma=float(gamma), se=float(se), p_value=float(fit.pvalues["knowable"]),
        ci_low=float(ci[0]), ci_high=float(ci[1]),
        gamma_std=float(gamma / y.std(ddof=0)) if y.std(ddof=0) > 0 else float("nan"),
        score_sd=float(y.std(ddof=0)),
        n_obs=int(len(d)), n_units=int(d[unit].nunique()), n_identifying_units=identifying,
        mde_std=float(2.8 * se / y.std(ddof=0)) if y.std(ddof=0) > 0 else float("nan"),
        label=label or {},
    )
    if moderator and "knowable:moderator" in Xw.columns:
        result.moderator_interaction = float(fit.params["knowable:moderator"])
        result.moderator_se = float(fit.bse["knowable:moderator"])
        result.moderator_p = float(fit.pvalues["knowable:moderator"])
    return result


def auc_table(
    df: pd.DataFrame, *, model: str, score: str, outcome: str, event_date: str, cutoff: str
) -> pd.DataFrame:
    """Discrimination of each model's score, split by whether the outcome was knowable.

    For each model, outcome units are split into knowable and not-knowable
    events and each group is compared with all non-outcome units. Leakage shows
    up as a higher AUC on knowable events than on unknowable ones.
    """
    d = df[df[score].notna()].copy()
    d["_knowable"] = add_knowable(d, outcome, event_date, cutoff)
    rows = []
    for m, g in d.groupby(model):
        neg = g[g[outcome] == 0]
        for name, pos in (("knowable", g[(g[outcome] == 1) & (g._knowable == 1)]),
                          ("not_knowable", g[(g[outcome] == 1) & (g._knowable == 0)])):
            if len(pos) < 5 or len(neg) < 5:
                auc = np.nan
            else:
                both = pd.concat([pos, neg])
                auc = roc_auc_score((both[outcome] == 1).astype(int), both[score])
            rows.append({"model": m, "events": name, "n_events": len(pos), "auc": auc})
    return pd.DataFrame(rows)


def verdict(r: LeakageResult, threshold_std: float = 0.1) -> str:
    """One-sentence plain-language reading of a result."""
    if r.n_identifying_units < 20:
        return (f"Inconclusive: only {r.n_identifying_units} units have outcomes between model "
                "cutoffs, too few to identify leakage.")
    sig = r.p_value < 0.05
    big = abs(r.gamma_std) >= threshold_std
    if sig and big:
        return (f"Leakage detected: scores shift by {r.gamma_std:+.2f} SD when the outcome is "
                f"knowable to the model (p = {r.p_value:.3g}).")
    if sig:
        return (f"Small but detectable leakage: {r.gamma_std:+.2f} SD (p = {r.p_value:.3g}); "
                "probably negligible for most uses.")
    return (f"No detectable leakage: estimate {r.gamma_std:+.2f} SD, 95% CI "
            f"[{r.ci_low:.3g}, {r.ci_high:.3g}] in score units. The design could detect "
            f"effects of {r.mde_std:.2f} SD or more; smaller leakage cannot be ruled out.")
