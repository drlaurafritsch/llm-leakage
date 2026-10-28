"""Minimal, polite SEC EDGAR client with an on-disk cache.

SEC fair-access rules: identify yourself in the User-Agent and stay under
10 requests per second. Every response is cached under data/raw/http so
reruns are free and the exact inputs can be archived with the results.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from common import RAW_DIR, env_required, load_config, stable_hash

ARCHIVES = "https://www.sec.gov/Archives/edgar"
DATA_API = "https://data.sec.gov"
MIN_INTERVAL_S = 0.12  # about 8 requests per second


class Edgar:
    def __init__(self, user_agent: str | None = None, cache_dir: Path | None = None):
        cfg = load_config("sample")
        self.user_agent = user_agent or env_required(cfg["sec_user_agent_env"])
        self.cache_dir = cache_dir or (RAW_DIR / "http")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}
        )
        self._last = 0.0

    # -- transport -------------------------------------------------------
    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{stable_hash(url)}.bin"

    def get_bytes(self, url: str, retries: int = 4) -> bytes | None:
        path = self._cache_path(url)
        if path.exists():
            return path.read_bytes()
        for attempt in range(retries):
            wait = MIN_INTERVAL_S - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                resp = self.session.get(url, timeout=60)
            except requests.RequestException:
                time.sleep(2 ** attempt)
                continue
            if resp.status_code == 404:
                return None
            if resp.status_code in (403, 429, 500, 502, 503):
                time.sleep(2 ** (attempt + 1))
                continue
            resp.raise_for_status()
            path.write_bytes(resp.content)
            return resp.content
        raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")

    def get_text(self, url: str) -> str | None:
        raw = self.get_bytes(url)
        return None if raw is None else raw.decode("utf-8", errors="replace")

    def get_json(self, url: str) -> dict | None:
        raw = self.get_bytes(url)
        return None if raw is None else json.loads(raw)

    # -- endpoints -------------------------------------------------------
    def form_index(self, year: int, quarter: int) -> str | None:
        """Quarterly full index of all filings, one line per filing."""
        return self.get_text(f"{ARCHIVES}/full-index/{year}/QTR{quarter}/form.idx")

    def submissions(self, cik: int) -> dict | None:
        """Company metadata plus filing history, merging paginated files."""
        main = self.get_json(f"{DATA_API}/submissions/CIK{cik:010d}.json")
        if main is None:
            return None
        recent = main.get("filings", {}).get("recent", {})
        frames = [recent]
        for extra in main.get("filings", {}).get("files", []):
            page = self.get_json(f"{DATA_API}/submissions/{extra['name']}")
            if page:
                frames.append(page)
        import pandas as pd  # local import keeps the client light

        merged = pd.concat([pd.DataFrame(f) for f in frames if f], ignore_index=True)
        merged = merged.to_dict("list") if not merged.empty else {}
        main["filings_all"] = merged
        return main

    def assets_frame(self, year: int) -> dict | None:
        """Total assets for every XBRL filer at a calendar year end."""
        return self.get_json(
            f"{DATA_API}/api/xbrl/frames/us-gaap/Assets/USD/CY{year}Q4I.json"
        )

    def filing_document(self, cik: int, accession: str, document: str) -> str | None:
        acc = accession.replace("-", "")
        return self.get_text(f"{ARCHIVES}/data/{cik}/{acc}/{document}")
