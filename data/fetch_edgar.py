"""Build the EDGAR firm-year frame, detect outcomes, and fetch 10-K text.

Usage (run from the repository root):
    python -m data.fetch_edgar index    # firm universe from XBRL frames (data.sec.gov)
    python -m data.fetch_edgar events   # 10-Ks, outcomes, SIC and assets per firm
    python -m data.fetch_edgar texts    # sections for the sampled firm-years
                                        # (run after python -m data.build_sample)

Outputs (data/interim):
    universe.csv         every firm reporting total assets in the sample years
    assets_frames.csv    total assets by firm and calendar year
    firm_years.csv       10-K filings with outcome dates, SIC and log assets
    entities.jsonl       names, former names and tickers per firm (for masking)
    documents.jsonl      extracted sections for sampled firm-years
"""

from __future__ import annotations

import argparse
import math
from datetime import date  # noqa: F401  (used in type hints)

import pandas as pd

from common import INTERIM_DIR, append_jsonl, ensure_dirs, load_config, read_jsonl
from data.edgar import Edgar
from data.sections import extract_sections

def cmd_index(edgar: Edgar, cfg: dict) -> None:
    """Firm universe: every XBRL filer reporting total assets in the sample years.

    Uses the XBRL frames API on data.sec.gov, which includes firms that later
    went bankrupt or deregistered, so the universe is not survivorship-biased.
    """
    years = range(min(cfg["filing_years"]) - 1, max(cfg["filing_years"]) + 1)
    rows = []
    for year in years:
        frame = edgar.assets_frame(year) or {}
        for r in frame.get("data", []):
            rows.append({"cik": int(r["cik"]), "entity": r.get("entityName"),
                         "year": year, "assets": r.get("val")})
        print(f"assets frame CY{year}: {len(frame.get('data', []))} filers")
    uni = pd.DataFrame(rows)
    uni.to_csv(INTERIM_DIR / "assets_frames.csv", index=False)
    ciks = uni[["cik", "entity"]].drop_duplicates("cik")
    ciks.to_csv(INTERIM_DIR / "universe.csv", index=False)
    print(f"universe: {len(ciks)} firms")


def first_event_after(history: pd.DataFrame, rule: dict, start: date, end: date):
    mask = history["form"].isin(rule["forms"])
    if "items" in rule:
        wanted = set(rule["items"])
        mask &= history["items"].fillna("").map(
            lambda s: bool(wanted & {i.strip() for i in s.split(",")})
        )
    hits = history.loc[mask & (history["filingDate"] > start) & (history["filingDate"] <= end)]
    return None if hits.empty else hits["filingDate"].min()


def cmd_events(edgar: Edgar, cfg: dict) -> None:
    uni = pd.read_csv(INTERIM_DIR / "universe.csv")
    frames = pd.read_csv(INTERIM_DIR / "assets_frames.csv")
    assets = {(int(r.cik), int(r.year)): r.assets for r in frames.itertuples()}
    years = set(cfg["filing_years"])
    horizon = cfg["horizon_years"]

    entities_path = INTERIM_DIR / "entities.jsonl"
    done = {e["cik"] for e in read_jsonl(entities_path)}
    rows, n = [], len(uni)
    for i, cik in enumerate(uni["cik"].astype(int), 1):
        if i % 250 == 0:
            print(f"events: {i}/{n} firms, {len(rows)} 10-Ks so far", flush=True)
        sub = edgar.submissions(cik)
        if sub is None:
            continue
        hist = pd.DataFrame(sub["filings_all"])
        if hist.empty:
            continue
        hist["filingDate"] = pd.to_datetime(hist["filingDate"]).dt.date
        tenks = hist[(hist["form"] == "10-K") & hist["filingDate"].map(lambda d: d.year in years)]
        if tenks.empty:
            continue
        if cik not in done:
            append_jsonl(entities_path, [{
                "cik": cik,
                "name": sub.get("name"),
                "former_names": [f.get("name") for f in sub.get("formerNames", [])],
                "tickers": sub.get("tickers", []),
                "exchanges": sub.get("exchanges", []),
            }])
        for rec in tenks.itertuples():
            start = rec.filingDate
            try:
                end = start.replace(year=start.year + horizon)
            except ValueError:  # 29 February
                end = start.replace(year=start.year + horizon, day=28)
            row = {
                "cik": cik, "accession": rec.accessionNumber, "filing_date": start,
                "primary_document": rec.primaryDocument, "sic": sub.get("sic"),
                "log_assets": None,
            }
            val = assets.get((cik, start.year - 1))
            if val and val > 0:
                row["log_assets"] = math.log(val)
            for name, rule in cfg["outcomes"].items():
                row[f"{name}_date"] = first_event_after(hist, rule, start, end)
            rows.append(row)
    out = pd.DataFrame(rows)
    date_cols = [c for c in out.columns if c.endswith("_date") and c != "filing_date"]
    out["any_event"] = out[date_cols].notna().any(axis=1).astype(int)
    out.to_csv(INTERIM_DIR / "firm_years.csv", index=False)
    print(f"wrote {len(out)} firm-years; {out.any_event.sum()} with an outcome in window")


def cmd_texts(edgar: Edgar, cfg: dict) -> None:
    sample = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str, "accession": str})
    out_path = INTERIM_DIR / "documents.jsonl"
    done = {d["doc_id"] for d in read_jsonl(out_path)}
    missing = 0
    for rec in sample.itertuples():
        if rec.doc_id in done or not isinstance(rec.primary_document, str):
            continue
        html = edgar.filing_document(int(rec.cik), rec.accession, rec.primary_document)
        sections = extract_sections(html or "", cfg["sections"], cfg["max_chars"])
        if not sections:
            missing += 1
            continue
        append_jsonl(out_path, [{
            "doc_id": rec.doc_id, "cik": int(rec.cik), "accession": rec.accession,
            "filing_date": rec.filing_date, "sections": sections,
        }])
    print(f"texts done; {missing} filings had no extractable sections")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["index", "events", "texts"])
    args = parser.parse_args()
    ensure_dirs()
    cfg = load_config("sample")
    edgar = Edgar()
    {"index": cmd_index, "events": cmd_events, "texts": cmd_texts}[args.step](edgar, cfg)


if __name__ == "__main__":
    main()
