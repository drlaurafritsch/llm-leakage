"""Knowledge probe: does each model know what later happened to each firm?

The leakage design asks whether outcomes the model could know shift its codes.
A null is only informative if the models actually knew those outcomes. This
probe asks each model directly, by name and ticker, whether the firm filed for
bankruptcy or announced a restatement in the three years after its 10-K.

Usage:
    python -m probes.knowledge [--models ...] [--limit N] [--workers 8]

Writes results/knowledge.jsonl (raw answers) and results/knowledge_scored.csv
(one row per document, model and outcome).
"""

from __future__ import annotations

import argparse

import pandas as pd

from common import INTERIM_DIR, RESULTS_DIR, ensure_dirs, load_config, read_jsonl
from coding.llm import Job, load_models, run_jobs

PROMPT = "knowledge_v1"
OUTCOMES = ["bankruptcy", "restatement"]


def render(company: str, ticker: str, start: str, end: str) -> str:
    from coding.llm import PROMPT_DIR

    text = (PROMPT_DIR / f"{PROMPT}.txt").read_text(encoding="utf-8")
    return (text.replace("{company}", company).replace("{ticker}", ticker or "none")
                .replace("{start}", start).replace("{end}", end))


def windows(sample: pd.DataFrame, horizon: int) -> pd.DataFrame:
    s = sample.copy()
    start = pd.to_datetime(s["filing_date"])
    s["start"] = start.dt.strftime("%B %Y")
    s["end"] = (start + pd.DateOffset(years=horizon)).dt.strftime("%B %Y")
    return s


def build_jobs(models: list[str], limit: int | None) -> list[Job]:
    cfg = load_config("sample")
    docs = {d["doc_id"] for d in read_jsonl(INTERIM_DIR / "documents.jsonl")}
    sample = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str})
    sample = windows(sample[sample["doc_id"].isin(docs)], cfg["horizon_years"])
    if limit:
        sample = sample.head(limit)
    entities = {e["cik"]: e for e in read_jsonl(INTERIM_DIR / "entities.jsonl")}
    jobs = []
    for r in sample.itertuples():
        e = entities.get(int(r.cik), {})
        tickers = e.get("tickers") or []
        prompt = render(e.get("name") or "", tickers[0] if tickers else "", r.start, r.end)
        for m in models:
            jobs.append(Job(r.doc_id, m, "raw", "knowledge", PROMPT, prompt))
    return jobs


def yes(value) -> int | None:
    v = str(value or "").strip().lower()
    if v.startswith("y"):
        return 1
    if v.startswith("n") and not v.startswith("unk"):
        return 0
    return None  # unknown or unreadable


def score() -> pd.DataFrame:
    sample = pd.read_csv(INTERIM_DIR / "sample.csv", dtype={"doc_id": str})
    sample = sample.set_index("doc_id")
    latest = {r["key"]: r for r in read_jsonl(RESULTS_DIR / "knowledge.jsonl") if r.get("parsed")}
    rows = []
    for r in latest.values():
        p = r["parsed"]
        s = sample.loc[r["doc_id"]]
        for o in OUTCOMES:
            ans = yes(p.get(o))
            rows.append({
                "doc_id": r["doc_id"], "cik": int(s["cik"]), "model": r["model"],
                "cutoff": r["training_cutoff"], "measure": o,
                "outcome": int(pd.notna(s[f"{o}_date"])), "event_date": s[f"{o}_date"],
                "answer": ans, "says_yes": int(ans == 1), "says_unknown": int(ans is None),
                "confidence": pd.to_numeric(p.get(f"{o}_confidence"), errors="coerce"),
            })
    return pd.DataFrame(rows)


def main() -> None:
    specs, _ = load_models()
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=list(specs))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    ensure_dirs()
    jobs = build_jobs(args.models, args.limit)
    print(f"{len(jobs)} knowledge jobs")
    run_jobs(jobs, RESULTS_DIR / "knowledge.jsonl", workers=args.workers)
    scored = score()
    scored.to_csv(RESULTS_DIR / "knowledge_scored.csv", index=False)
    print(scored.groupby(["model", "measure", "outcome"])["says_yes"].mean().unstack().round(3))


if __name__ == "__main__":
    main()
