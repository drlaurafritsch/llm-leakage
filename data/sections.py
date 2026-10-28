"""Extract Item 1A (Risk Factors) and Item 7 (MD&A) from a 10-K document.

10-K layouts vary widely. The heuristic: convert HTML to text, find every
heading at the start of a line that could start the section (which rules out
in-text cross-references such as "see Item 1A, Risk Factors"), and keep the candidate that yields the
longest span before the next item heading. That skips the table of contents,
where the same headings appear with almost nothing between them.
"""

from __future__ import annotations

import re
import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

_SEP = r"[\s\.\-–—:]*"

PATTERNS = {
    "risk_factors": (
        re.compile(rf"(?:^|\n)[ \t]*item{_SEP}1a{_SEP}risk\s+factors", re.I),
        re.compile(rf"\n[ \t]*(?:item{_SEP}1b{_SEP}|item{_SEP}2{_SEP}properties)", re.I),
    ),
    "mdna": (
        re.compile(rf"(?:^|\n)[ \t]*item{_SEP}7{_SEP}management[’'`s\s]*discussion", re.I),
        re.compile(rf"\n[ \t]*(?:item{_SEP}7a{_SEP}|item{_SEP}8{_SEP}financial\s+statements)", re.I),
    ),
}

MIN_SECTION_CHARS = 500


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "ix:header"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_section(text: str, section: str) -> str | None:
    start_re, end_re = PATTERNS[section]
    best = ""
    for start in start_re.finditer(text):
        end = end_re.search(text, start.end())
        stop = end.start() if end else len(text)
        candidate = text[start.end():stop].strip()
        if len(candidate) > len(best):
            best = candidate
    return best if len(best) >= MIN_SECTION_CHARS else None


def extract_sections(html: str, sections: list[str], max_chars: int) -> dict[str, str]:
    text = html_to_text(html)
    out = {}
    for name in sections:
        body = extract_section(text, name)
        if body:
            out[name] = body[:max_chars]
    return out
