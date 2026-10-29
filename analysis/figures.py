"""Core figures for the proposal and technical appendix.

Usage:  python -m analysis.figures

Writes to results/figures/:
    leakage_by_level.png   leakage (in SD of the score) across the masking ladder
    reid_by_level.png      re-identification rate across the masking ladder
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from common import RESULTS_DIR  # noqa: E402
from masking.mask import LEVELS  # noqa: E402

INK = "#1f2933"
LABELS = {"gpt4omini": "GPT-4o mini", "llama33": "Llama 3.3 70B", "gpt41mini": "GPT-4.1 mini",
          "llama4": "Llama 4 Maverick", "gemini25flash": "Gemini 2.5 Flash", "haiku55": "Claude Haiku 5.5"}
MUTED = "#7b8794"
SERIES = {"predict / all_outcomes": "#2f6fb0", "construct / financial_distress": "#c2541c"}


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.yaxis.grid(True, color="#e4e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def leakage_by_level(est: pd.DataFrame, out) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
    order = [lvl for lvl in LEVELS if lvl in set(est["level"])]
    x = range(len(order))
    for i, (name, colour) in enumerate(SERIES.items()):
        task, measure = name.split(" / ")
        g = est[(est.task == task) & (est.measure == measure)].set_index("level").reindex(order)
        if g["gamma_std"].isna().all():
            continue
        lo = (g["gamma"] - g["ci_low"]) / g["score_sd"]
        hi = (g["ci_high"] - g["gamma"]) / g["score_sd"]
        xs = [v + (i - 0.5) * 0.12 for v in x]
        ax.errorbar(xs, g["gamma_std"], yerr=[lo, hi], fmt="o-", color=colour, capsize=3,
                    linewidth=1.6, markersize=5, label=name.replace(" / ", ": ").replace("_", " "))
    ax.axhline(0, color=MUTED, linewidth=0.9)
    ax.set_xticks(list(x), [lvl.capitalize() for lvl in order])
    ax.set_ylabel("Leakage (SD of score)", color=INK, fontsize=9)
    ax.set_xlabel("Masking level", color=INK, fontsize=9)
    ax.set_title("Average leakage is indistinguishable from zero at every rung (95% CI)", color=INK, fontsize=10, loc="left")
    _style(ax)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def reid_by_level(rates: pd.DataFrame, out) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 3.4), dpi=200)
    order = [lvl for lvl in LEVELS if lvl in set(rates["level"])]
    palette = ["#2f6fb0", "#c2541c", "#3d8b5a", "#7a4fa3", "#b8860b", "#5f6b7a"]
    try:
        from coding.llm import load_models
        model_order = list(load_models()[0])
    except Exception:
        model_order = sorted(rates["model"].unique())
    model_order = [m for m in model_order if m in set(rates["model"])]
    for i, model in enumerate(model_order):
        g = rates[rates["model"] == model].set_index("level").reindex(order)
        ax.plot(range(len(order)), g["hit"], "o-", color=palette[i % len(palette)],
                linewidth=1.6, markersize=5, label=LABELS.get(model, model))
    ax.set_xticks(range(len(order)), [lvl.capitalize() for lvl in order])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of firms re-identified", color=INK, fontsize=9)
    ax.set_xlabel("Masking level", color=INK, fontsize=9)
    ax.set_title("Removing names leaves half to three-quarters of firms identifiable", color=INK, fontsize=10, loc="left")
    _style(ax)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main() -> None:
    fig_dir = RESULTS_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    est = pd.read_csv(RESULTS_DIR / "leakage_estimates.csv")
    leakage_by_level(est, fig_dir / "leakage_by_level.png")
    rates_path = RESULTS_DIR / "reid_rates.csv"
    if rates_path.exists():
        reid_by_level(pd.read_csv(rates_path), fig_dir / "reid_by_level.png")
    print(f"figures written to {fig_dir}")


if __name__ == "__main__":
    main()
