# RLHF-Eval

> **Evaluation framework for Reinforcement Learning from Human Feedback**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/bihari-bhau/rlhf-eval/pulls)
[![GitHub Issues](https://img.shields.io/github/issues/bihari-bhau/rlhf-eval)](https://github.com/bihari-bhau/rlhf-eval/issues)

**RLHF-Eval** is a lightweight, extensible evaluation suite for RLHF-trained language models. It provides standardised metrics and tools to assess reward model accuracy, policy alignment, generalisation, and training stability — all in one place.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Reward Model Evaluation](#1-evaluate-a-reward-model)
  - [Policy Evaluation](#2-evaluate-a-policy-rlhf-tuned-model)
  - [CLI Usage](#3-command-line-interface)
  - [LLM-as-a-Judge](#4-llm-as-a-judge)
  - [Full Pipeline](#5-full-evaluation-pipeline)
- [Configuration](#configuration)
- [Metrics Reference](#metrics-reference)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Citation](#citation)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Overview

Training RLHF models is only half the battle — knowing whether they're actually aligned, helpful, and robust is the other. **RLHF-Eval** bridges that gap with:

| What you want to measure | What RLHF-Eval provides |
|---|---|
| Does my reward model rank preferences correctly? | Accuracy, AUC, rank correlation on preference pairs |
| Is my policy generating aligned outputs? | BLEU, ROUGE, BERTScore, SimCSE embedding distances |
| How stable was training? | KL divergence, reward variance, policy entropy tracking |
| How does it perform on new tasks? | Out-of-distribution generalisation benchmarks |
| Is an LLM-judge scoring it fairly? | GPT-4 / Claude / open-source judge integration |

Designed to plug into popular pipelines like [TRL](https://github.com/huggingface/trl) and [DeepSpeed Chat](https://github.com/microsoft/DeepSpeedExamples/tree/master/applications/DeepSpeed-Chat) with minimal configuration.

---

## Features

- 📊 **Offline evaluation** — evaluate reward models and policies directly from saved checkpoints, no re-training needed
- 🤖 **LLM-as-a-judge** — use GPT-4, Claude, or open-source models (Llama 3, Mistral) to score responses across custom criteria
- 📝 **Preference accuracy** — compute rank correlation, pairwise accuracy, and AUC for reward models on preference datasets
- 📈 **Alignment metrics** — BLEU, ROUGE, BERTScore, and learned embedding distances via SimCSE
- 🔁 **Reproducible pipelines** — YAML-based configuration with CSV/JSON results export for full reproducibility
- ⚡ **Batch inference** — supports Hugging Face `transformers` and `vLLM` for fast, large-scale scoring
- 🧩 **Extensible** — plug in custom evaluators, judges, or metrics with a simple interface

---

## Architecture

```
rlhf-eval/
├── rlhf_eval/
│   ├── evaluators/
│   │   ├── reward_model.py      # RewardModelEvaluator
│   │   ├── policy.py            # PolicyEvaluator
│   │   └── judge.py             # LLM-as-a-judge
│   ├── metrics/
│   │   ├── preference.py        # Accuracy, AUC, rank correlation
│   │   ├── alignment.py         # BLEU, ROUGE, BERTScore, SimCSE
│   │   └── stability.py         # KL divergence, entropy, variance
│   ├── pipeline.py              # Pipeline orchestrator
│   └── config.py                # YAML config loader
├── configs/
│   └── eval_config.yaml         # Example config
├── data/
│   └── preference_pairs.json    # Example test data format
├── tests/
└── README.md
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/bihari-bhau/rlhf-eval.git
cd rlhf-eval

# Install core package
pip install -e .
```

**Optional extras:**

```bash
# For LLM-as-a-judge (GPT-4, Claude, open-source judges)
pip install -e ".[llm_judge]"

# For development (testing, linting, pre-commit hooks)
pip install -e ".[dev]"
pre-commit install
```

**Requirements:** Python 3.9+, PyTorch ≥ 2.0, Hugging Face `transformers` ≥ 4.35

---

## Quick Start

```python
from rlhf_eval import Pipeline

pipeline = Pipeline.from_config("configs/eval_config.yaml")
results = pipeline.run(
    reward_model="my_reward_model",
    policy="my_rlhf_policy",
    baseline="sft_baseline",
    test_dataset="data/test.json",
)
results.save("results.json")
pipeline.report()
```

```
╔══════════════════════════════════════════╗
║         RLHF-Eval Summary Report         ║
╠══════════════════════════════════════════╣
║  Reward Model Accuracy   :  78.4%        ║
║  Reward Model AUC        :  0.841        ║
║  Policy Alignment (mean) :  0.73         ║
║  KL Divergence           :  0.12         ║
╚══════════════════════════════════════════╝
```

---

## Usage

### 1. Evaluate a Reward Model

```python
from rlhf_eval import RewardModelEvaluator

evaluator = RewardModelEvaluator(
    reward_model_path="path/to/reward_model",
    test_data="data/preference_pairs.json",
)

results = evaluator.run()
print(f"Accuracy : {results.accuracy:.2%}")
print(f"AUC      : {results.auc:.3f}")
print(f"Spearman : {results.rank_correlation:.3f}")
```

**Expected data format** (`preference_pairs.json`):

```json
[
  {
    "prompt": "Explain quantum entanglement.",
    "chosen": "Quantum entanglement is a phenomenon where...",
    "rejected": "Entanglement is when two particles are connected..."
  }
]
```

---

### 2. Evaluate a Policy (RLHF-tuned model)

```python
from rlhf_eval import PolicyEvaluator

policy = PolicyEvaluator(model_path="path/to/policy_model")
metrics = policy.evaluate(
    prompts=["Explain quantum computing", "Write a poem about autumn"],
    reference_answers=["...", "..."],
)

print(metrics.alignment_scores)   # per-prompt alignment
print(metrics.reward_mean)        # mean reward across prompts
print(metrics.reward_std)         # reward variance
```

---

### 3. Command Line Interface

```bash
# Evaluate a reward model
rlhf-eval reward --model ./reward_model --data data/test.json

# Evaluate a policy
rlhf-eval policy --model ./policy --prompts prompts.txt --references refs.txt

# Run LLM-as-a-judge from config
rlhf-eval judge --config config.yaml --responses model_outputs.jsonl

# Run full pipeline
rlhf-eval run --config configs/eval_config.yaml
```

---

### 4. LLM-as-a-Judge

Configure your judge in a YAML file:

```yaml
# config.yaml
judge:
  model: "gpt-4"               # or "claude-3-opus", "meta-llama/Llama-3-70b-chat"
  api_key: ${OPENAI_API_KEY}   # loaded from environment
  criteria:
    - helpfulness
    - honesty
    - harmlessness
  score_range: [1, 10]
  output_format: json
```

Then run:

```bash
rlhf-eval judge --config config.yaml --responses model_outputs.jsonl
```

**Supported judges:**

| Provider | Models |
|---|---|
| OpenAI | `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` |
| Anthropic | `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku` |
| Open-source (vLLM) | `meta-llama/Llama-3-70b`, `mistralai/Mistral-7b-Instruct`, any HF model |

---

### 5. Full Evaluation Pipeline

```python
from rlhf_eval import Pipeline

pipeline = Pipeline.from_config("configs/eval_config.yaml")
results = pipeline.run(
    reward_model="my_reward_model",
    policy="my_rlhf_policy",
    baseline="sft_baseline",
    test_dataset="data/test.json",
)

results.save("results.json")   # machine-readable
pipeline.report()              # human-readable summary
```

---

## Configuration

Full reference for `eval_config.yaml`:

```yaml
# configs/eval_config.yaml

reward_model:
  path: "./checkpoints/reward_model"
  batch_size: 32
  device: "cuda"

policy:
  path: "./checkpoints/policy"
  max_new_tokens: 256
  temperature: 0.7

baseline:
  path: "./checkpoints/sft_baseline"

dataset:
  path: "data/test.json"
  max_samples: 1000
  seed: 42

metrics:
  preference: [accuracy, auc, rank_correlation]
  alignment: [bleu, rouge, bertscore, simcse]
  stability: [kl_divergence, reward_variance, policy_entropy]

judge:
  model: "gpt-4"
  api_key: ${OPENAI_API_KEY}
  criteria: [helpfulness, honesty, harmlessness]

output:
  path: "results/"
  formats: [json, csv]
```

---

## Metrics Reference

### Preference Metrics (Reward Model)

| Metric | Description | Range |
|---|---|---|
| `accuracy` | Fraction of preference pairs correctly ranked | 0–1 |
| `auc` | Area under ROC curve for reward scores | 0–1 |
| `rank_correlation` | Spearman rank correlation with human labels | -1 to 1 |

### Alignment Metrics (Policy)

| Metric | Description |
|---|---|
| `bleu` | N-gram overlap with reference responses |
| `rouge` | Recall-oriented overlap (ROUGE-1, -2, -L) |
| `bertscore` | Contextual embedding similarity (F1) |
| `simcse` | SimCSE-based embedding distance to reference |

### Stability Metrics (Training)

| Metric | Description |
|---|---|
| `kl_divergence` | KL(policy ‖ reference) — deviation from base model |
| `reward_variance` | Variance in reward scores across the test set |
| `policy_entropy` | Token-level entropy of policy outputs |

---

## Roadmap

- [ ] Multi-turn conversation evaluation
- [ ] Safety / red-teaming evaluation suite
- [ ] Direct Preference Optimisation (DPO) policy support
- [ ] Weights & Biases / MLflow logging integration
- [ ] Leaderboard export format (compatible with Open LLM Leaderboard)
- [ ] Web dashboard for visualising results

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

For major changes, open an issue first to discuss what you'd like to improve.

**Development setup:**

```bash
pip install -e ".[dev]"
pre-commit install
pytest tests/
```

**Adding a custom metric:**

```python
from rlhf_eval.metrics import BaseMetric

class MyCustomMetric(BaseMetric):
    def compute(self, predictions, references):
        # your logic here
        return {"my_metric": score}
```

Then register it in `configs/eval_config.yaml` under `metrics.custom`.

---

## Citation

If you use RLHF-Eval in your research, please cite:

```bibtex
@software{rlhf_eval_2024,
  author  = {Bihari Bhau},
  title   = {RLHF-Eval: Evaluation Framework for Reinforcement Learning from Human Feedback},
  url     = {https://github.com/bihari-bhau/rlhf-eval},
  year    = {2024},
}
```

---

## Acknowledgements

- [TRL](https://github.com/huggingface/trl) — Transformer Reinforcement Learning library
- [DeepSpeed Chat](https://github.com/microsoft/DeepSpeedExamples/tree/master/applications/DeepSpeed-Chat) — scalable RLHF training
- [Anthropic's HH-RLHF dataset](https://github.com/anthropics/hh-rlhf) — human preference data and evaluation protocols
- [BERTScore](https://github.com/Tiiiger/bert_score) and [SimCSE](https://github.com/princeton-nlp/SimCSE) — alignment metric implementations

---

## License

Distributed under the [MIT License](LICENSE).