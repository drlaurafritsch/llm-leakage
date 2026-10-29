"""Run the full pipeline on the synthetic world, with and without planted leakage.

Usage:
    python -m simulate.run_simulation                    # leak = 0.3 and null
    python -m simulate.run_simulation --leak 0.3 --firms 600

Each scenario runs in its own directory under simulate/runs/<name>, using the
real masking, model-running, probe and analysis code. Only the model is fake.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

SIM_MODELS = {
    "models": [
        {"key": "early", "model_id": "fake/early", "training_cutoff": "2021-06-01",
         "cutoff_source": "simulation", "base_url_env": "X", "api_key_env": "X"},
        {"key": "middle", "model_id": "fake/middle", "training_cutoff": "2023-01-01",
         "cutoff_source": "simulation", "base_url_env": "X", "api_key_env": "X"},
        {"key": "late", "model_id": "fake/late", "training_cutoff": "2025-06-01",
         "cutoff_source": "simulation", "base_url_env": "X", "api_key_env": "X"},
    ],
    "paraphraser": "early",
    "generation": {"temperature": 0, "seed": 7, "max_tokens": 400,
                   "request_timeout_s": 10, "max_retries": 1},
}


def run_scenario(name: str, leak: float, firms: int, seed: int = 11) -> Path:
    workdir = ROOT / "simulate" / "runs" / name
    if workdir.exists():
        shutil.rmtree(workdir)
    cfg_dir = workdir / "config"
    cfg_dir.mkdir(parents=True)
    shutil.copy(ROOT / "config" / "sample.yaml", cfg_dir / "sample.yaml")
    (cfg_dir / "models.yaml").write_text(yaml.safe_dump(SIM_MODELS))

    env = {**os.environ, "LEAK_WORKDIR": str(workdir), "LEAK_CONFIG_DIR": str(cfg_dir),
           "LEAK_FAKE_MODEL": "simulate.world:fake_complete", "LEAK_STRENGTH": str(leak),
           "PYTHONPATH": str(ROOT)}

    def step(*args: str) -> None:
        print(f"[{name}] python -m {' '.join(args)}", flush=True)
        subprocess.run([sys.executable, "-m", *args], cwd=ROOT, env=env, check=True)

    gen = (f"from simulate.world import build_world, write_inputs; "
           f"write_inputs(build_world(n_firms={firms}, seed={seed}))")
    subprocess.run([sys.executable, "-c", gen], cwd=ROOT, env=env, check=True)
    step("coding.run_models", "--workers", "1")
    step("probes.reidentify", "--workers", "1")
    step("analysis.leakage_index")
    step("analysis.figures")
    return workdir


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--leak", type=float, default=0.3)
    p.add_argument("--firms", type=int, default=600)
    p.add_argument("--seeds", type=int, nargs="*", default=[11],
                   help="world seeds; more than one gives a Monte Carlo check of bias")
    p.add_argument("--no-null", action="store_true")
    a = p.parse_args()
    for seed in a.seeds:
        tag = "" if seed == 11 else f"_s{seed}"
        run_scenario(f"leak{tag}", a.leak, a.firms, seed)
        if not a.no_null:
            run_scenario(f"null{tag}", 0.0, a.firms, seed)


if __name__ == "__main__":
    main()
