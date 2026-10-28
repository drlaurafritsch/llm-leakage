"""Draw event firm-years and matched controls.

Usage:  python -m data.build_sample

Reads data/interim/firm_years.csv and writes data/interim/sample.csv with one
row per sampled firm-year, a stable doc_id, the matched-set id, and the outcome
dates. Controls share the 2-digit SIC code and filing year of their event
firm-year, are nearest in log total assets, and have no outcome in the window.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import INTERIM_DIR, load_config


def build_sample(firm_years: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    rng = np.random.default_rng(cfg["random_seed"])
    fy = firm_years.copy()
    fy = fy[fy["primary_document"].notna()]
    fy["filing_date"] = pd.to_datetime(fy["filing_date"])
    fy["year"] = fy["filing_date"].dt.year
    digits = cfg["match_on_sic_digits"]
    fy["sic_group"] = (
        pd.to_numeric(fy["sic"], errors="coerce").fillna(-1).astype(int).astype(str).str[:digits]
    )

    # Blank-check companies (SIC 6770) are excluded: the 2021 wave of SPAC
    # warrant restatements was triggered by an SEC staff statement, not by
    # anything in the firms' own disclosures.
    fy = fy[pd.to_numeric(fy["sic"], errors="coerce") != 6770]

    events = fy[fy["any_event"] == 1].copy()
    cap = cfg["max_event_firm_years"]
    window = cfg.get("prioritise_event_window")
    if window and len(events) > cap:
        # Events between the earliest and latest model cutoffs identify leakage,
        # so they fill most slots; the rest are drawn from outside the window,
        # which anchors each model's baseline discrimination.
        date_cols = [f"{o}_date" for o in cfg["outcomes"]]
        first = events[date_cols].apply(pd.to_datetime, errors="coerce").min(axis=1)
        inside = (first >= pd.Timestamp(window[0])) & (first < pd.Timestamp(window[1]))
        core = events[inside]
        core_cap = int(cap * cfg.get("prioritise_share", 0.7))
        if len(core) > core_cap:
            core = core.sample(core_cap, random_state=cfg["random_seed"])
        rest = events[~inside]
        fill = rest.sample(min(cap - len(core), len(rest)), random_state=cfg["random_seed"])
        events = pd.concat([core, fill])
    elif len(events) > cap:
        events = events.sample(cap, random_state=cfg["random_seed"])
    pool = fy[fy["any_event"] == 0].copy()
    used: set[int] = set()

    chosen = []
    for set_id, ev in enumerate(events.itertuples()):
        chosen.append((ev.Index, set_id, "event"))
        cands = pool[(pool["sic_group"] == ev.sic_group) & (pool["year"] == ev.year)]
        cands = cands[~cands.index.isin(used) & (cands["cik"] != ev.cik)]
        if cands.empty:
            continue
        if pd.notna(ev.log_assets) and cands["log_assets"].notna().any():
            dist = (cands["log_assets"] - ev.log_assets).abs().fillna(np.inf)
            picks = dist.nsmallest(cfg["controls_per_event"]).index
        else:
            k = min(cfg["controls_per_event"], len(cands))
            picks = rng.choice(cands.index, size=k, replace=False)
        for p in picks:
            used.add(p)
            chosen.append((p, set_id, "control"))

    idx, set_ids, roles = zip(*chosen)
    sample = fy.loc[list(idx)].copy()
    sample["match_set"] = set_ids
    sample["role"] = roles
    # Prefixed so that no CSV reader ever turns the id into a number.
    sample["doc_id"] = "acc" + sample["accession"].str.replace("-", "", regex=False)
    sample = sample.drop_duplicates("doc_id")
    return sample.drop(columns=["year"])


def main() -> None:
    cfg = load_config("sample")
    fy = pd.read_csv(INTERIM_DIR / "firm_years.csv")
    sample = build_sample(fy, cfg)
    sample.to_csv(INTERIM_DIR / "sample.csv", index=False)
    print(
        f"sample: {len(sample)} firm-years "
        f"({(sample.role == 'event').sum()} events, {(sample.role == 'control').sum()} controls)"
    )


if __name__ == "__main__":
    main()
