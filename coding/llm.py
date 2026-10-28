"""Model access, prompt rendering, JSON parsing and the cached job runner.

Every call is keyed on (model id, task, prompt version, document, masking
level, generation settings). Results are appended to a JSONL cache, so a run
can be interrupted and resumed, and the cache itself is the replication record.
"""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from common import ROOT, append_jsonl, load_config, read_jsonl, stable_hash

PROMPT_DIR = ROOT / "coding" / "prompts"


@dataclass
class ModelSpec:
    key: str
    model_id: str
    training_cutoff: str
    base_url_env: str
    api_key_env: str
    max_tokens: int | None = None
    extra_body: dict | None = None


def load_models() -> tuple[dict[str, ModelSpec], dict]:
    cfg = load_config("models")
    specs = {}
    for m in cfg["models"]:
        specs[m["key"]] = ModelSpec(
            key=m["key"], model_id=m["model_id"], training_cutoff=str(m["training_cutoff"]),
            base_url_env=m["base_url_env"], api_key_env=m["api_key_env"],
            max_tokens=m.get("max_tokens"), extra_body=m.get("extra_body"),
        )
    return specs, cfg


def render(prompt_name: str, text: str) -> str:
    template = (PROMPT_DIR / f"{prompt_name}.txt").read_text(encoding="utf-8")
    return template.replace("{text}", text)


def parse_json(raw: str) -> dict | None:
    """Return the last JSON object in the reply.

    Models sometimes give an answer, then 'correct' it in the same reply;
    the final object is the intended one. Code fences are ignored.
    """
    if not raw:
        return None
    text = re.sub(r"```(?:json)?", "", raw)
    decoder = json.JSONDecoder()
    found = None
    i = text.find("{")
    while i != -1:
        try:
            value, end = decoder.raw_decode(text, i)
            if isinstance(value, dict):
                found = value
            i = text.find("{", end)
        except json.JSONDecodeError:
            i = text.find("{", i + 1)
    return found


class Client:
    """Thin wrapper over any OpenAI-compatible chat endpoint."""

    def __init__(self, spec: ModelSpec, gen: dict):
        from openai import OpenAI

        base_url = os.environ.get(spec.base_url_env) or None
        api_key = os.environ.get(spec.api_key_env) or "not-needed"
        self.spec = spec
        self.gen = gen
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=gen["request_timeout_s"])

    def complete(self, prompt: str) -> str:
        last_err = None
        for attempt in range(self.gen["max_retries"]):
            try:
                resp = self.client.chat.completions.create(
                    model=self.spec.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.gen["temperature"],
                    max_tokens=self.spec.max_tokens or self.gen["max_tokens"],
                    seed=self.gen["seed"],
                    extra_body=self.spec.extra_body or None,
                )
                return resp.choices[0].message.content or ""
            except Exception as err:  # provider errors vary widely
                last_err = err
                time.sleep(2 ** attempt)
        raise RuntimeError(f"{self.spec.model_id}: {last_err}")


@dataclass
class Job:
    doc_id: str
    model_key: str
    level: str
    task: str
    prompt_version: str
    prompt: str


def job_key(job: Job, spec: ModelSpec, gen: dict) -> str:
    return stable_hash(spec.model_id, job.task, job.prompt_version, job.doc_id, job.level,
                       gen["temperature"], gen["seed"], gen["max_tokens"])


def run_jobs(jobs: list[Job], out_path: Path, workers: int = 8,
             complete_fn: Callable[[ModelSpec, str], str] | None = None) -> int:
    """Run jobs not already in out_path. Returns the number of new results.

    complete_fn lets tests substitute a fake model; by default each model's
    Client is used.
    """
    specs, cfg = load_models()
    gen = cfg["generation"]
    if complete_fn is None and os.environ.get("LEAK_FAKE_MODEL"):
        # Simulation hook: "package.module:function" replaces every model call.
        import importlib

        mod_name, fn_name = os.environ["LEAK_FAKE_MODEL"].split(":")
        complete_fn = getattr(importlib.import_module(mod_name), fn_name)
    # A call counts as done only if it succeeded; failed or unreadable
    # answers are retried on the next run (the latest row wins in analysis).
    def ok(r: dict) -> bool:
        if r.get("error"):
            return False
        return bool(r.get("raw")) if r.get("task") == "paraphrase" else bool(r.get("parsed"))
    done = {r["key"] for r in read_jsonl(out_path) if ok(r)}
    todo = [(j, job_key(j, specs[j.model_key], gen)) for j in jobs]
    todo = [(j, k) for j, k in todo if k not in done]
    if not todo:
        return 0
    clients: dict[str, Client] = {}

    def call(job: Job) -> str:
        spec = specs[job.model_key]
        if complete_fn is not None:
            return complete_fn(spec, job.prompt)
        if job.model_key not in clients:
            clients[job.model_key] = Client(spec, gen)
        return clients[job.model_key].complete(job.prompt)

    written = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(call, j): (j, k) for j, k in todo}
        for fut in as_completed(futures):
            job, key = futures[fut]
            try:
                raw, err = fut.result(), None
            except Exception as exc:
                raw, err = "", str(exc)
            spec = specs[job.model_key]
            append_jsonl(out_path, [{
                "key": key, "doc_id": job.doc_id, "model": job.model_key,
                "model_id": spec.model_id, "training_cutoff": spec.training_cutoff,
                "level": job.level, "task": job.task, "prompt_version": job.prompt_version,
                "raw": raw, "parsed": parse_json(raw), "error": err,
            }])
            written += 1
            if written % 100 == 0:
                print(f"  {written}/{len(todo)} calls")
    return written
