"""Run the construct-coding and prediction tasks across models and masking levels.

Usage:
    python -m coding.run_models                       # everything in config
    python -m coding.run_models --models early late --levels raw names --limit 50
    python -m coding.run_models --tasks construct     # one task only

Outputs:
    data/interim/paraphrases.jsonl   cached paraphrases (top masking rung)
    results/model_outputs.jsonl      one row per (doc, model, level, task)
"""

from __future__ import annotations

import argparse

from common import INTERIM_DIR, RESULTS_DIR, ensure_dirs, read_jsonl
from coding.llm import Job, load_models, render, run_jobs
from masking.mask import LEVELS, PARAPHRASE_PROMPT, RULE_BASED_LEVELS, mask_text

TASKS = {"construct": "construct_v1", "predict": "predict_v2"}
DOC_CHAR_BUDGET = 12000  # per document, across sections; keeps calls affordable


def load_documents(limit: int | None = None) -> list[dict]:
    docs = list(read_jsonl(INTERIM_DIR / "documents.jsonl"))
    return docs[:limit] if limit else docs


def load_entities() -> dict[int, dict]:
    return {e["cik"]: e for e in read_jsonl(INTERIM_DIR / "entities.jsonl")}


def document_text(doc: dict) -> str:
    parts = []
    for name in ("risk_factors", "mdna"):
        body = doc["sections"].get(name)
        if body:
            parts.append(body[: DOC_CHAR_BUDGET // 2])
    return "\n\n".join(parts)


def masked_texts(docs: list[dict], entities: dict[int, dict]) -> dict[tuple[str, str], str]:
    out = {}
    for doc in docs:
        entity = entities.get(doc["cik"], {})
        base = document_text(doc)
        for level in RULE_BASED_LEVELS:
            out[(doc["doc_id"], level)] = mask_text(base, entity, level)
    return out


def ensure_paraphrases(docs, texts, paraphraser: str, workers: int) -> None:
    path = INTERIM_DIR / "paraphrases.jsonl"
    jobs = [
        Job(doc_id=d["doc_id"], model_key=paraphraser, level="generalised", task="paraphrase",
            prompt_version="paraphrase_v1",
            prompt=PARAPHRASE_PROMPT.replace("{text}", texts[(d["doc_id"], "generalised")]))
        for d in docs
    ]
    n = run_jobs(jobs, path, workers=workers)
    print(f"paraphrases: {n} new")
    for row in read_jsonl(path):
        if row["raw"]:
            texts[(row["doc_id"], "paraphrased")] = row["raw"]


def main() -> None:
    specs, cfg = load_models()
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=list(specs))
    parser.add_argument("--levels", nargs="*", default=LEVELS)
    parser.add_argument("--tasks", nargs="*", default=list(TASKS))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    ensure_dirs()

    docs = load_documents(args.limit)
    texts = masked_texts(docs, load_entities())
    if "paraphrased" in args.levels:
        ensure_paraphrases(docs, texts, cfg["paraphraser"], args.workers)

    jobs = []
    for doc in docs:
        for level in args.levels:
            text = texts.get((doc["doc_id"], level))
            if not text:
                continue
            for model in args.models:
                for task in args.tasks:
                    jobs.append(Job(doc["doc_id"], model, level, task, TASKS[task],
                                    render(TASKS[task], text)))
    print(f"{len(jobs)} jobs across {len(docs)} documents")
    n = run_jobs(jobs, RESULTS_DIR / "model_outputs.jsonl", workers=args.workers)
    print(f"done: {n} new results")


if __name__ == "__main__":
    main()
