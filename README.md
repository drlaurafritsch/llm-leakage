# leakcheck: look-ahead leakage in LLM-coded text

Large language models have read the future. When researchers use them to code historical documents, such as annual reports, project filings, speeches or court records, the codes can absorb what the model knows about later events rather than what the document says. Any study that treats those codes as measured at the time of writing is then contaminated.

This repository does two things.

1. **A reusable diagnostic** (`diagnostic/leakcheck`) that estimates leakage in any LLM-coded measure of dated text, given documents scored by several models with different training cutoffs.
2. **A demonstration on SEC 10-K filings**: risk factor and MD&A text from 10-Ks filed 2020–2023, with later bankruptcies and accounting restatements taken from EDGAR itself. It measures leakage across a masking ladder and tests whether models re-identify firms after their names are removed.

Every input is public. Every model call is cached, so the cache is the replication record.

## Identification

The same document is scored by models whose training cutoffs differ. An outcome that happened before a model's cutoff is *knowable* to that model. Leakage is the extra shift in a model's score when the outcome is knowable to it, net of document fixed effects and each model's general ability to read outcome-relevant signals from text:

```
score[u,m] = a[u] + b[m] + c[m]·outcome[u] + γ·knowable[u,m] + e
```

γ is identified from outcomes that fall between model cutoffs. Standard errors are clustered by firm. The estimator reports how many units identify γ, so an uninformative design is visible immediately.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# SEC asks for a descriptive User-Agent with a contact address
export SEC_USER_AGENT="Your Name Affiliation you@example.org"

# Any OpenAI-compatible endpoint; OpenRouter shown here
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-..."
```

The simplest way to run the model step is `bash run_models_on_my_mac.sh` (50-document pilot) and then `bash run_models_on_my_mac.sh full`. The script sets up Python, asks for your OpenRouter key without displaying or storing it, and runs models, probe and analysis.

## Models and years

`config/models.yaml` codes every document with six models from four developers. Cutoffs are as stated by each developer; month-level cutoffs are coded as the first day of the following month.

| Key | Model | Weights | Stated cutoff | Source |
|---|---|---|---|---|
| `gpt4omini` | openai/gpt-4o-mini-2024-07-18 | Closed | October 2023 | [Azure OpenAI model list](https://learn.microsoft.com/azure/ai-services/openai/concepts/models) |
| `llama33` | meta-llama/llama-3.3-70b-instruct | Open | December 2023 | [Llama 3.3 model card](https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/MODEL_CARD.md) |
| `gpt41mini` | openai/gpt-4.1-mini | Closed | May 2024 | [Azure OpenAI model list](https://learn.microsoft.com/azure/ai-services/openai/concepts/models) |
| `llama4` | meta-llama/llama-4-maverick | Open | August 2024 | [Llama 4 model card](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md) |
| `gemini25flash` | google/gemini-2.5-flash | Closed | January 2025 | [Gemini API model page](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash) |
| `haiku55` | anthropic/claude-haiku-5.5 | Closed | June 2026 (reliable knowledge cutoff) | [Claude models overview](https://platform.claude.com/docs/en/models/overview) |

γ is identified from outcomes that occur between two models' cutoffs. 10-Ks filed 2020–2023 with a three-year window place outcomes between 2020 and late 2026; the sample prioritises events dated November 2023 to June 2026. The run prints `n_identifying_units`; below a few hundred, widen the years or add models. To swap models, edit the YAML and cite the new cutoff source.

## Data included

`data/interim/` holds the processed EDGAR data, so the model step can run without re-downloading anything:

| File | Contents |
|---|---|
| `universe.csv`, `assets_frames.csv` | 8,748 firms reporting total assets in XBRL, 2019–2023 |
| `firm_years.csv` | 24,798 10-Ks filed 2020–2023, with SIC, log assets and outcome dates |
| `entities.jsonl` | Names, former names and tickers (used for masking and scoring the probe) |
| `sample.csv` | 1,499 matched firm-years: 500 events and 999 controls |
| `documents.jsonl.gz` | Extracted Risk Factors and MD&A text for 1,473 of them |

Outcomes are bankruptcy (8-K Item 1.03) and non-reliance restatement (8-K Item 4.02) within three years. Delistings and deregistrations are excluded because most follow mergers; blank-check companies (SIC 6770) are excluded because their 2021 restatements followed an SEC staff statement. `make edgar sample texts` rebuilds everything from scratch.

## Running the demonstration

```bash
make test        # unit tests (seconds)
make simulate    # full pipeline on a synthetic world with planted leakage (minutes)

make edgar       # firm universe, filing histories and outcomes (about 1.5 hours; already done, see Data included)
make sample      # event firm-years and matched controls
make texts       # risk factor and MD&A sections for the sample
make models      # construct coding and prediction, all models and masking levels
make probe       # re-identification probe
make analysis    # estimates, knowledge split, identification checks and figures (about 10 minutes, no API keys; run in this order)
```

Each step resumes where it stopped. Start small with `python -m coding.run_models --limit 50` to check costs before a full run.

## Results (full run, 28 October 2026; identification checks 29 October 2026)

1,473 filings × 6 models × 4 masking rungs: 70,704 coding and prediction calls, 35,352 re-identification calls and 8,838 knowledge-probe calls, all cached in `results/*.jsonl.gz`. All estimates include model-specific outcome and size slopes.

- **Masking names does not hide identity.** With names, tickers and URLs removed, models still name the firm behind 45% (GPT-4o mini) to 73% (Claude Haiku 5.5) of filings; generalising dates and amounts barely helps (42% to 74%). Paraphrasing brings identification down to 2% to 13%.
- **No average outcome leakage is detectable, and power is limited.** Minimum detectable effects (80% power) are 0.22 SD for bankruptcy prediction, 0.12 SD for coded distress among bankruptcy filers, 0.11 SD for prediction pooled over both outcomes and 0.07 SD for pooled coded distress (restatements dominate the pooled estimates and are barely known to the models). Clean stacked comparisons that use only not-yet-knowable events as controls, a placebo (controls take their event's date), model × time-to-event slopes, a donut around each cutoff, leave-one-model-out estimates, permutation inference over all 720 cutoff assignments and ±6-month cutoff shifts all agree (`results/robustness_report.md`).
- **Models report knowing many bankruptcies, almost no restatements.** Asked directly (`probes/knowledge.py`), models report 13% to 49% of bankruptcies before their cutoff and 0% to 5% after it (16% for Llama 4 Maverick; Claude Haiku 5.5 has a single post-cutoff bankruptcy); knowability raises reported bankruptcies by 15 points (p < 0.001). Restatements: 0% to 9%, no more than for controls.
- **Belief, not recall, moves predictions.** When a model says a firm went bankrupt, its predicted probability is 2.9 points higher for firms that did fail (p = 0.09) and 2.2 points higher for control firms that did not (p = 0.04), so the shift reflects the model's belief about the firm rather than knowledge of the outcome. It is not detected after paraphrasing (difference 3.5 points, 95% CI 0.0 to 6.5). Coded distress does not move (`results/robustness_knows_checks.csv`).
- **Corrected readings.** An earlier version reported leakage rising with firm size, and the main estimate shows a negative effect on coded distress among bankruptcy filers. The placebo reproduces both; the first disappears with model-specific size slopes and the second in the clean stacked comparisons (`results/robustness_model_size.csv`, `results/robustness_stacked.csv`). Use `--model-controls` for covariates of this kind.

See `results/report.md`, `results/knowledge_report.md`, `results/robustness_report.md` and `results/figures/`.

## Outputs

| File | Contents |
|---|---|
| `results/leakage_estimates.csv` | γ, SE, CI, γ in SD units, minimum detectable effect, size interaction, per task, measure and masking level |
| `results/robustness_*.csv` | Stacked clean comparisons, placebo, permutation, leave-one-model-out, time-to-event, donut, size-slope, knowledge falsification and power checks |
| `results/auc.csv` | Discrimination per model, on knowable versus unknowable events |
| `results/reid_rates.csv` | Share of firms re-identified per model and masking level |
| `results/report.md` | Plain-language verdicts |
| `results/figures/` | Leakage and re-identification across the masking ladder |

## Using the diagnostic on your own corpus

Prepare a long CSV with one row per (document, model): `unit, model, score, outcome, event_date` and optionally a cluster column and a grouping column. Then:

```bash
python -m diagnostic.leakcheck scores.csv --cutoffs cutoffs.yaml --cluster firm --model-controls log_assets --by level
```

`cutoffs.yaml` maps each model name to its training cutoff date. In Python:

```python
from diagnostic.leakcheck import estimate, verdict
r = estimate(df, unit="unit", model="model", score="score", outcome="outcome",
             event_date="event_date", cutoff="cutoff", cluster="firm",
             model_controls=["log_assets"])   # optional: a separate slope per model
print(verdict(r))   # includes the minimum detectable effect
```

## The masking ladder

| Level | What is removed |
|---|---|
| `raw` | nothing |
| `names` | current and former firm names, tickers, URLs and e-mail addresses |
| `generalised` | plus years, dates, money amounts, large numbers and percentages |
| `paraphrased` | plus a rewrite by the earliest-cutoff model, instructed to remove identifying detail |

## Simulation

`simulate/` builds a synthetic corpus with known ground truth and a fake model that leaks when it recognises a firm whose outcome precedes its cutoff. The real masking, model-running, probe and analysis code runs unchanged; only the model is fake. With planted leakage the estimator recovers it and it falls to zero at the paraphrase rung; with no planted leakage every estimate is null. `python -m simulate.run_simulation --firms 1500 --seeds 21 31 41 51 --no-null` repeats the check on further synthetic worlds; across five worlds the average error is 3% to 7% of the planted effect (`python simulate/summarise_seeds.py simulate/runs/leak_s21 .` compares one world's estimates with its realised planted effect).

## Layout

```
config/            sample and model definitions
data/              EDGAR client, section extraction, sample construction
masking/           the masking ladder
coding/            prompts, model client, cached job runner
probes/            re-identification probe
analysis/          long frames, estimates, report, figures
diagnostic/leakcheck/  the reusable estimator and CLI
simulate/          synthetic world and fake model
tests/             unit tests
```

## Citation

Citation details will be added after review.

## Known limitations

- Training cutoffs are often loosely documented; results are only as good as `config/models.yaml`.
- Section extraction is heuristic and fails on some filings; failures are counted and skipped.
- Name masking misses short forms that are not in EDGAR's name history (for example a brand name used in the text). That residual identifiability is itself measured by the probe.
- Event counts for individual outcome types are small; the pooled estimate is the primary result.

## Licence

Code is released under the MIT licence (see `LICENSE`). EDGAR filings are public records of the US Securities and Exchange Commission.
