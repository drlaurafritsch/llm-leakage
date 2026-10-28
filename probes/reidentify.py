"""Re-identification probe: can the model name the firm at each masking level?

Usage:
    python -m probes.reidentify [--models ...] [--levels ...] [--limit N]

Writes results/reidentify.jsonl (raw model answers) and
results/reidentify_scored.csv (one row per doc, model and level, with a hit flag).
A hit is a ticker match or a fuzzy name match of 85 or more after legal
suffixes are removed.
"""

from __future__ import annotations

import argparse

import pandas as pd
from rapidfuzz import fuzz

from common import RESULTS_DIR, ensure_dirs, read_jsonl
from coding.llm import Job, load_models, render, run_jobs
from coding.run_models import ensure_paraphrases, load_documents, load_entities, masked_texts
from masking.mask import LEVELS, _strip_suffixes

PROMPT = "reidentify_v1"
NAME_THRESHOLD = 85


def is_hit(answer: dict | None, entity: dict) -> bool:
    if not answer:
        return False
    ticker = str(answer.get("ticker", "")).strip().upper()
    if ticker and ticker != "UNKNOWN" and ticker in {t.upper() for t in entity.get("tickers", [])}:
        return True
    guess = _strip_suffixes(str(answer.get("company_name", ""))).lower()
    if not guess or guess == "unknown":
        return False
    names = [entity.get("name") or ""] + list(entity.get("former_names") or [])
    return any(
        fuzz.token_set_ratio(guess, _strip_suffixes(n).lower()) >= NAME_THRESHOLD for n in names if n
    )


def score(entities: dict[int, dict], doc_cik: dict[str, int]) -> pd.DataFrame:
    rows = []
    latest = {r["key"]: r for r in read_jsonl(RESULTS_DIR / "reidentify.jsonl") if r.get("parsed")}
    for r in latest.values():
        entity = entities.get(doc_cik.get(r["doc_id"]), {})
        parsed = r.get("parsed") or {}
        rows.append({
            "doc_id": r["doc_id"], "model": r["model"], "level": r["level"],
            "hit": int(is_hit(parsed, entity)),
            "confidence": pd.to_numeric(parsed.get("confidence"), errors="coerce"),
        })
    return pd.DataFrame(rows)


def main() -> None:
    specs, cfg = load_models()
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=list(specs))
    parser.add_argument("--levels", nargs="*", default=LEVELS)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    ensure_dirs()

    docs = load_documents(args.limit)
    entities = load_entities()
    texts = masked_texts(docs, entities)
    if "paraphrased" in args.levels:
        ensure_paraphrases(docs, texts, cfg["paraphraser"], args.workers)
    jobs = [
        Job(d["doc_id"], m, lvl, "reidentify", PROMPT, render(PROMPT, texts[(d["doc_id"], lvl)]))
        for d in docs for lvl in args.levels if (d["doc_id"], lvl) in texts for m in args.models
    ]
    print(f"{len(jobs)} probe jobs")
    run_jobs(jobs, RESULTS_DIR / "reidentify.jsonl", workers=args.workers)
    scored = score(entities, {d["doc_id"]: d["cik"] for d in docs})
    scored.to_csv(RESULTS_DIR / "reidentify_scored.csv", index=False)
    print(scored.groupby(["model", "level"])["hit"].mean().unstack().round(3))


if __name__ == "__main__":
    main()
