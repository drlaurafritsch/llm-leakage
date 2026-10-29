"""Fast unit tests. Run with:  python -m pytest -q"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.build_sample import build_sample
from data.sections import extract_sections
from diagnostic.leakcheck import estimate, verdict
from masking.mask import mask_text, name_variants

CUTOFFS = {"a": "2021-01-01", "b": "2023-01-01", "c": "2025-01-01"}


def panel(gamma: float, n: int = 800, seed: int = 0) -> pd.DataFrame:
    """Units scored by three models; capability differs; leakage = gamma."""
    rng = np.random.default_rng(seed)
    rows = []
    for u in range(n):
        signal = rng.normal()
        outcome = int(rng.random() < 1 / (1 + np.exp(-(signal - 0.5))))
        event = pd.Timestamp("2019-06-01") + pd.Timedelta(days=int(rng.integers(0, 6 * 365)))
        for m, slope in (("a", 0.5), ("b", 0.8), ("c", 1.1)):
            knowable = outcome and event < pd.Timestamp(CUTOFFS[m])
            score = slope * signal + 0.4 * outcome * slope + gamma * knowable + rng.normal(0, 0.5)
            rows.append({"unit": u, "model": m, "score": score, "outcome": outcome,
                         "event_date": event if outcome else pd.NaT, "cutoff": CUTOFFS[m],
                         "firm": u // 2})
    return pd.DataFrame(rows)


@pytest.mark.parametrize("gamma", [0.0, 0.4])
def test_estimate_recovers_planted_gamma(gamma):
    r = estimate(panel(gamma), unit="unit", model="model", score="score", outcome="outcome",
                 event_date="event_date", cutoff="cutoff", cluster="firm")
    assert abs(r.gamma - gamma) < 3 * r.se + 0.02
    assert np.isfinite(r.se) and r.se < 0.1
    if gamma == 0:
        assert "No detectable" in verdict(r) or r.p_value > 0.01
    else:
        assert r.p_value < 1e-4


def test_model_controls_remove_size_confound():
    """A later model that scores large firms higher must not look like leakage."""
    rng = np.random.default_rng(3)
    rows = []
    for u in range(1500):
        size = rng.normal()
        outcome = int(rng.random() < 0.4)
        # Large firms' events come sooner, so they are knowable to more models.
        days = int(np.clip(rng.normal(3 * 365 - 400 * size, 300), 0, 6 * 365))
        event = pd.Timestamp("2019-06-01") + pd.Timedelta(days=days)
        for m, size_slope in (("a", 0.0), ("b", 0.0), ("c", 0.6)):
            score = 0.5 * outcome + size_slope * size + rng.normal(0, 0.5)
            rows.append({"unit": u, "model": m, "score": score, "outcome": outcome,
                         "event_date": event if outcome else pd.NaT, "cutoff": CUTOFFS[m],
                         "size": size})
    df = pd.DataFrame(rows)
    kw = dict(unit="unit", model="model", score="score", outcome="outcome",
              event_date="event_date", cutoff="cutoff")
    naive = estimate(df, **kw)
    fixed = estimate(df, model_controls=["size"], **kw)
    assert naive.p_value < 0.01          # spurious "leakage" without the control
    assert abs(fixed.gamma) < 3 * fixed.se + 0.02
    assert np.isfinite(fixed.mde_std) and fixed.mde_std > 0


def test_unidentified_design_raises():
    df = panel(0.3)
    df["cutoff"] = "2030-01-01"  # every outcome knowable to every model
    with pytest.raises(ValueError, match="not identified"):
        estimate(df, unit="unit", model="model", score="score", outcome="outcome",
                 event_date="event_date", cutoff="cutoff")


ENTITY = {"name": "ACME WIDGETS HOLDINGS, INC.", "former_names": ["Acme Tools Corp"],
          "tickers": ["ACMW"]}


def test_name_masking_covers_variants():
    text = ("Acme Widgets Holdings, Inc. (ACMW) reported results. Acme Widgets grew. "
            "Formerly Acme Tools, the company sells widgets. Visit www.acme.com.")
    out = mask_text(text, ENTITY, "names")
    assert "Acme" not in out and "ACMW" not in out and "www." not in out
    assert out.count("the Company") >= 3
    assert "Acme Widgets" in name_variants(ENTITY) or "ACME WIDGETS" in name_variants(ENTITY)


def test_generalise_removes_dates_and_amounts():
    text = "On March 3, 2020 revenue was $1,234.5 million, up 12.5% from 2019; 4,500 staff."
    out = mask_text(text, ENTITY, "generalised")
    for token in ("2020", "2019", "1,234", "12.5", "4,500"):
        assert token not in out
    assert "[DATE]" in out and "[AMOUNT]" in out and "[PERCENT]" in out


def test_section_extraction_skips_table_of_contents():
    body = "We face many risks. " * 60
    html = (
        "<html><body><p>Item 1A. Risk Factors 12</p><p>Item 1B. Unresolved Staff Comments 20</p>"
        f"<p>ITEM 1A. RISK FACTORS</p><p>{body}</p><p>ITEM 1B. UNRESOLVED STAFF COMMENTS</p>"
        "<p>None.</p></body></html>"
    )
    out = extract_sections(html, ["risk_factors"], max_chars=10_000)
    assert "We face many risks" in out["risk_factors"]
    assert "Unresolved" not in out["risk_factors"]


def test_matched_controls_share_industry_and_year():
    rng = np.random.default_rng(1)
    rows = []
    for i in range(200):
        rows.append({"cik": i, "accession": f"0000-{i:02d}-00000{i}", "primary_document": "a.htm",
                     "filing_date": f"{2018 + i % 3}-03-01", "sic": 3500 + (i % 4) * 100,
                     "log_assets": rng.normal(20, 2), "any_event": int(i % 10 == 0)})
    cfg = {"random_seed": 1, "match_on_sic_digits": 2, "controls_per_event": 2,
           "max_event_firm_years": 100}
    s = build_sample(pd.DataFrame(rows), cfg)
    s["year"] = pd.to_datetime(s["filing_date"]).dt.year
    s["sic2"] = s["sic"].astype(str).str[:2]
    for _, g in s.groupby("match_set"):
        assert g["year"].nunique() == 1 and g["sic2"].nunique() == 1
        assert (g["role"] == "event").sum() == 1
