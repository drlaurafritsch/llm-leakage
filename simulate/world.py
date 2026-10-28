"""A synthetic corpus with known ground truth, and a fake model that leaks.

The point is to check that the pipeline recovers leakage when it exists, and
reports none when it does not, before any money is spent on real model calls.

World
-----
Each synthetic firm has latent distress, a fame level (log assets), a name, a
ticker, and a distinctive product line. Its 10-K text contains distress cues
in proportion to latent distress, its name and ticker, its product line, and
some years and money amounts. Outcomes (bankruptcy and
restatement) are more likely for distressed firms and land at dates spread
across the model cutoffs.

Fake model
----------
Reads the distress cues in the prompt, with noise that shrinks for later
models (capability differences). It recognises a firm from its name or
ticker, or, less reliably, from its product line, with recall rising in
fame. If it recognises the firm and the firm's outcome occurred before the
model's cutoff, it shifts its answer towards the outcome by LEAK_STRENGTH.
Paraphrasing strips the product line, so leakage should vanish at that rung.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import date, timedelta

import numpy as np
import pandas as pd

from common import INTERIM_DIR

OUTCOMES = ["bankruptcy", "restatement"]
SYLLABLES = ["kar", "vel", "dor", "mia", "sun", "tor", "lex", "bri", "nov", "qua", "ren",
             "zel", "pha", "gor", "lin", "mar", "ost", "ula", "ves", "cor", "dal", "ery"]
SUFFIXES = ["Inc.", "Corp.", "Holdings, Inc.", "Group, Inc.", "Industries Inc."]
BIRDS = ["Kestrel", "Osprey", "Heron", "Plover", "Merlin", "Petrel", "Shrike", "Tern",
         "Avocet", "Dunlin", "Gannet", "Lapwing", "Siskin", "Wigeon", "Bittern"]

DISTRESS = [
    "Our recurring losses raise substantial doubt about our ability to continue as a going concern.",
    "We were not in compliance with certain financial covenants under our credit facility.",
    "Our liquidity is constrained and we may be unable to meet obligations as they come due.",
    "We may need to seek protection from creditors if refinancing is not available.",
    "Our auditors have identified a material weakness in internal control over financial reporting.",
    "We received a notice from the exchange regarding non-compliance with listing standards.",
]
NEUTRAL = [
    "We face competition from larger companies with greater resources.",
    "Changes in laws and regulations could affect our operations.",
    "We depend on key personnel and the loss of any of them could harm our business.",
    "Cybersecurity incidents could disrupt our systems and damage our reputation.",
    "Our results may fluctuate from quarter to quarter.",
    "We rely on third-party suppliers for certain components.",
]


def _h(*parts) -> float:
    """Deterministic uniform(0,1) from arbitrary parts."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(digest[:12], 16) / 16 ** 12


def build_world(n_firms: int = 600, seed: int = 11) -> dict:
    rng = np.random.default_rng(seed)
    firms, used_names = [], set()
    for i in range(n_firms):
        while True:
            stem = "".join(rng.choice(SYLLABLES, size=3)).capitalize()
            if stem not in used_names:
                used_names.add(stem)
                break
        name = f"{stem} {rng.choice(['Dynamics', 'Systems', 'Energy', 'Health', 'Retail', 'Materials'])}"
        legal = f"{name} {rng.choice(SUFFIXES)}"
        ticker = (stem[:3] + name.split()[1][0]).upper()
        product = f"{rng.choice(BIRDS)}-{rng.integers(2, 99)} {rng.choice(['platform', 'line', 'series'])}"
        distress = float(rng.normal())
        fame = float(rng.normal(20, 2))
        filing = date(int(rng.integers(2018, 2023)), int(rng.integers(1, 13)), int(rng.integers(1, 28)))
        p_event = 1 / (1 + math.exp(-(-1.4 + 1.3 * distress)))
        event_type, event_date = None, None
        if rng.random() < p_event:
            event_type = str(rng.choice(OUTCOMES))
            event_date = filing + timedelta(days=int(rng.integers(60, 3 * 365)))
        firms.append({
            "cik": 900000 + i, "name": legal, "short": name, "ticker": ticker,
            "product": product, "distress": distress, "fame": fame,
            "filing_date": filing.isoformat(), "event_type": event_type,
            "event_date": event_date.isoformat() if event_date else None,
        })
    return {"firms": firms}


def firm_text(f: dict, rng: np.random.Generator) -> str:
    n_distress = int(np.clip(round((f["distress"] + 0.8) * 2.2), 0, len(DISTRESS)))
    sentences = list(rng.choice(DISTRESS, size=n_distress, replace=False)) + list(NEUTRAL)
    rng.shuffle(sentences)
    year = int(f["filing_date"][:4]) - 1
    intro = (f"{f['name']} (NASDAQ: {f['ticker']}) designs and sells the {f['product']}. "
             f"In fiscal {year}, {f['short']} generated revenue of ${rng.integers(20, 900)} million, "
             f"up {rng.integers(1, 30)}% from {year - 1}. ")
    outro = (f" Demand for the {f['product']} remains central to {f['short']}'s results, "
             f"and {f['short']} expects to invest $"
             f"{rng.integers(5, 90)} million in the {f['product']} during {year + 1}.")
    return intro + " ".join(sentences) + outro


def write_inputs(world: dict, seed: int = 12) -> None:
    rng = np.random.default_rng(seed)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    docs, ents, sample = [], [], []
    for f in world["firms"]:
        doc_id = f"sim{f['cik']}"
        text = firm_text(f, rng)
        half = len(text) // 2
        docs.append({"doc_id": doc_id, "cik": f["cik"], "accession": doc_id,
                     "filing_date": f["filing_date"],
                     "sections": {"risk_factors": text[:half] + " " * 0, "mdna": text[half:]}})
        ents.append({"cik": f["cik"], "name": f["name"], "former_names": [],
                     "tickers": [f["ticker"]], "exchanges": ["Nasdaq"]})
        row = {"doc_id": doc_id, "cik": f["cik"], "accession": doc_id,
               "filing_date": f["filing_date"], "log_assets": f["fame"],
               "role": "event" if f["event_type"] else "control", "match_set": 0}
        for o in OUTCOMES:
            row[f"{o}_date"] = f["event_date"] if f["event_type"] == o else None
        row["any_event"] = int(f["event_type"] is not None)
        sample.append(row)
    with open(INTERIM_DIR / "documents.jsonl", "w") as fh:
        fh.writelines(json.dumps(d) + "\n" for d in docs)
    with open(INTERIM_DIR / "entities.jsonl", "w") as fh:
        fh.writelines(json.dumps(e) + "\n" for e in ents)
    pd.DataFrame(sample).to_csv(INTERIM_DIR / "sample.csv", index=False)
    with open(INTERIM_DIR / "sim_truth.json", "w") as fh:
        json.dump(world, fh)


# ---------------------------------------------------------------------------
# Fake model
# ---------------------------------------------------------------------------
_WORLD = None
_INDEX = None


def _world() -> list[dict]:
    global _WORLD
    if _WORLD is None:
        _WORLD = json.loads((INTERIM_DIR / "sim_truth.json").read_text())["firms"]
    return _WORLD


def _index():
    """Compiled lookups so recognition is fast on large synthetic worlds."""
    global _INDEX
    if _INDEX is None:
        firms = _world()
        by_name = {f["short"]: f for f in firms}
        by_ticker = {f["ticker"]: f for f in firms}
        by_product = {f["product"]: f for f in firms}
        name_re = re.compile("|".join(re.escape(n) for n in sorted(by_name, key=len, reverse=True)))
        ticker_re = re.compile(r"\b(" + "|".join(map(re.escape, by_ticker)) + r")\b")
        product_re = re.compile("|".join(re.escape(p) for p in sorted(by_product, key=len, reverse=True)))
        _INDEX = (by_name, by_ticker, by_product, name_re, ticker_re, product_re)
    return _INDEX


def _recognise(prompt: str, model_key: str):
    """Return the firm the model recognises in the prompt, or None."""
    by_name, by_ticker, by_product, name_re, ticker_re, product_re = _index()
    m = name_re.search(prompt) or ticker_re.search(prompt)
    if m:
        f = by_name.get(m.group(0)) or by_ticker.get(m.group(0))
        recall = 1 / (1 + math.exp(-(f["fame"] - 18.5)))
        return f if _h("name", f["cik"], model_key) < recall else None
    m = product_re.search(prompt)
    if m:
        f = by_product[m.group(0)]
        recall = 0.6 / (1 + math.exp(-(f["fame"] - 19.5)))
        return f if _h("product", f["cik"], model_key) < recall else None
    return None


def fake_complete(spec, prompt: str) -> str:
    leak = float(os.environ.get("LEAK_STRENGTH", "0.3"))
    cutoff = date.fromisoformat(spec.training_cutoff[:10])
    capability = {"early": 0.9, "middle": 0.7, "late": 0.5}.get(spec.key, 0.7)

    if prompt.startswith("Rewrite the following"):
        body = prompt.split("---\n", 1)[1]
        # A competent paraphraser removes residual names and the product line.
        by_name, _, _, name_re, _, product_re = _index()
        body = product_re.sub("its main product", body)
        return name_re.sub("the Company", body)

    cues = sum(prompt.count(s[:40]) for s in DISTRESS)
    noise = np.random.default_rng(int(_h(prompt[-200:], spec.key) * 1e9)).normal(0, capability)
    firm = _recognise(prompt, spec.key)
    knows = bool(firm and firm["event_date"] and date.fromisoformat(firm["event_date"]) < cutoff)

    if "Which company wrote it" in prompt:
        if firm:
            return json.dumps({"company_name": firm["name"], "ticker": firm["ticker"], "confidence": 0.8})
        return json.dumps({"company_name": "UNKNOWN", "ticker": "UNKNOWN", "confidence": 0.1})

    if "Estimate the probability" in prompt:
        base = 1 / (1 + math.exp(-(-2.6 + 0.55 * cues + 0.3 * noise)))
        probs = {o: round(base / 2, 3) for o in OUTCOMES}
        if knows:
            probs[firm["event_type"]] = round(min(1.0, probs[firm["event_type"]] + leak), 3)
        return json.dumps(probs)

    if "Rate the excerpt" in prompt:
        distress = float(np.clip(1.5 + 0.9 * cues + noise + (4 * leak if knows else 0), 1, 7))
        return json.dumps({"financial_distress": round(distress, 1),
                           "managerial_optimism": round(float(np.clip(5 - 0.5 * cues + noise, 1, 7)), 1),
                           "risk_candour": round(float(np.clip(3 + 0.3 * cues + noise, 1, 7)), 1)})
    return "{}"
