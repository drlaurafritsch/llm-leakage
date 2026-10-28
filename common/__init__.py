"""Shared helpers: configuration loading, paths and JSONL caching."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

ROOT = Path(__file__).resolve().parent.parent
# LEAK_WORKDIR redirects all data and results (used by the simulation so that
# synthetic runs never mix with real ones); LEAK_CONFIG_DIR redirects configs.
WORKDIR = Path(os.environ.get("LEAK_WORKDIR", ROOT))
CONFIG_DIR = Path(os.environ.get("LEAK_CONFIG_DIR", ROOT / "config"))
DATA_DIR = WORKDIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
RESULTS_DIR = WORKDIR / "results"


def load_config(name: str) -> dict:
    """Load config/<name>.yaml."""
    with open(CONFIG_DIR / f"{name}.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ensure_dirs() -> None:
    for d in (RAW_DIR, INTERIM_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def stable_hash(*parts: Any) -> str:
    """Deterministic short hash of arbitrary JSON-serialisable parts."""
    blob = json.dumps(parts, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:24]


def read_jsonl(path: Path) -> Iterator[dict]:
    """Read a JSONL file, falling back to a gzipped copy (path + '.gz')."""
    gz = path.with_name(path.name + ".gz")
    if not path.exists() and not gz.exists():
        return iter(())
    def _gen():
        import gzip
        opener = (lambda: open(path, encoding="utf-8")) if path.exists() else (
            lambda: gzip.open(gz, "rt", encoding="utf-8"))
        with opener() as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
    return _gen()


def append_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(
            f"Environment variable {name} is not set. See README, 'Setup'."
        )
    return value
