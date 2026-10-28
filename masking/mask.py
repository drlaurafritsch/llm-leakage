"""The masking ladder.

Rungs, each applied on top of the previous one:
    raw          original text
    names        firm names (current and former, with and without legal
                 suffixes), tickers, URLs and e-mail addresses removed
    generalised  plus years, dates, money amounts, large numbers and
                 percentages replaced with coarse placeholders
    paraphrased  plus a paraphrase by the earliest-cutoff model
                 (produced in coding/run_models.py, which owns model calls)

The re-identification probe (probes/reidentify.py) measures how much identity
survives each rung. The research question is whether leakage falls to zero once
names are gone, or whether models still recognise firms from context.
"""

from __future__ import annotations

import re

LEVELS = ["raw", "names", "generalised", "paraphrased"]
RULE_BASED_LEVELS = LEVELS[:3]

LEGAL_SUFFIXES = re.compile(
    r"[,\s]+(inc|incorporated|corp|corporation|co|company|ltd|limited|llc|l\.l\.c|lp|l\.p|"
    r"plc|holdings?|group|trust|n\.v|s\.a|ag|se|bancorp|/de|/md|/nv)\.?$",
    re.I,
)

URL = re.compile(r"\b(?:https?://|www\.)\S+", re.I)
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
MONEY = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d+)?\s*(?:thousand|million|billion|trillion|[mbk]n?)?\b", re.I
)
PCT = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|percent\b)", re.I)
FULL_DATE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
    r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s+\d{1,2},?\s+(?:19|20)\d{2}\b",
    re.I,
)
NUM_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/(?:19|20)?\d{2}\b")
YEAR = re.compile(r"\b(?:19[5-9]\d|20[0-4]\d)\b")
BIG_NUMBER = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d{4,}(?:\.\d+)?\b")


def _strip_suffixes(name: str) -> str:
    prev = None
    name = name.strip()
    while prev != name:
        prev = name
        name = LEGAL_SUFFIXES.sub("", name).strip(" ,.")
    return name


def name_variants(entity: dict) -> list[str]:
    """All surface forms of a firm's name, longest first."""
    names = [entity.get("name") or ""] + list(entity.get("former_names") or [])
    variants: set[str] = set()
    for n in names:
        n = (n or "").strip()
        if not n:
            continue
        variants.add(n)
        core = _strip_suffixes(n)
        if len(core) >= 3:
            variants.add(core)
        # EDGAR names are often upper case; add a title-case form.
        variants.add(core.title())
    return sorted({v for v in variants if len(v) >= 3}, key=len, reverse=True)


def mask_names(text: str, entity: dict) -> str:
    out = URL.sub("[URL]", text)
    out = EMAIL.sub("[EMAIL]", out)
    for variant in name_variants(entity):
        pattern = re.compile(r"(?<!\w)" + re.escape(variant) + r"(?:['’]s)?(?!\w)", re.I)
        out = pattern.sub("the Company", out)
    for ticker in entity.get("tickers") or []:
        if len(ticker) >= 2:
            out = re.sub(r"(?<![\w$])" + re.escape(ticker) + r"(?!\w)", "[TICKER]", out)
    return out


def generalise(text: str) -> str:
    out = FULL_DATE.sub("[DATE]", text)
    out = NUM_DATE.sub("[DATE]", out)
    out = MONEY.sub("[AMOUNT]", out)
    out = PCT.sub("[PERCENT]", out)
    out = YEAR.sub("[YEAR]", out)
    out = BIG_NUMBER.sub("[NUMBER]", out)
    return out


def mask_text(text: str, entity: dict, level: str) -> str:
    if level == "raw":
        return text
    if level == "names":
        return mask_names(text, entity)
    if level == "generalised":
        return generalise(mask_names(text, entity))
    raise ValueError(
        f"Level {level!r} is not rule-based; 'paraphrased' is produced by coding/run_models.py"
    )


PARAPHRASE_PROMPT = (
    "Rewrite the following excerpt from a company's annual report in plain, neutral "
    "English. Keep every substantive fact about risks, operations and finances. "
    "Remove or neutralise anything that could identify the company, its industry niche, "
    "its locations, its products, its executives or the time period. Do not add facts. "
    "Return only the rewritten text.\n\n---\n{text}"
)
