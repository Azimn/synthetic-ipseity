# Real Qwen2.5-1.5B evidence-capacity pilot — 2026-10-10

**Completed real CPU inference, 96/96 generations. Preregistered responsiveness gate: FAIL.**

This report does not revise the earlier v0.9, v0.9.2 or v0.9.3 negative results. It is an independent fresh-stem study, not proof for/against artificial character continuity, and not evidence that Palinode is conscious or behaviorally effective.

## Full provenance

- GitHub Actions real-model execution: https://github.com/Azimn/synthetic-ipseity/actions/runs/38100242123
- Archived artifact: qwen-evidence-38100242123, artifact ID 11687501544
- Model: official Qwen/Qwen2.5-1.5B-Instruct-GGUF, qwen2.5-1.5b-instruct-q4_k_m.gguf (~1.12 GB Q4_K_M), Apache-2.0
- HF source revision: 91cad51170dc346986eccefdc2dd33a9da36ead9
- Downloaded actual GGUF SHA-256: 6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e
- capacity-manifest.json SHA-256: 360163f3fb1654ac373a12b3d70827beb3f974efbd9303d6ff1a012ba739b004
- capacity-raw.jsonl SHA-256: df252466b56acf930566e9c72e7996787feef854f92bb29d0496117b97b744eb
- capacity-report.json SHA-256: fa930620b51b2dfecd66545d16f1fbeea4bb16a1f82a2f2024e7311afc5e2b38
- GitHub Actions ZIP SHA-256: 157184df41c73474052ac676c3645ca981a1c9aa1760faa3e8a6077199453086
- Python 3.11 CPU runtime, llama-cpp-python 0.3.16; source prompt from real v0.8 PalinodeHost for D; source-only first-person C without active organ; no paid API or private persona data

## Preregistered metrics

Four independent fresh stems (F01–F04), four yes/no/unknown questions, two C/D arms, original/reversed/no-evidence contexts: 96 authentic generations. Number of observations is *not* the effective independent sample size; only four case stems exist.

| Measurement | C (first-person prompt) | D (real Palinode organ) |
| --- | ---: | ---: |
| Generation outputs | 48/48 | 48/48 |
| Lenient single-answer format | 47/48 = 97.9% | 45/48 = 93.8% |
| Strict single-answer format | 47/48 = 97.9% | 43/48 = 89.6% |
| Unconditional semantic answer accuracy | 32/48 = 66.7% | 35/48 = 72.9% |
| **Correct original AND reversed conflict judgment** | **0/4 = 0%** | **0/4 = 0%** |
| Any choice change on conflict reversal | 1/4 | 3/4 |
| Neutral UNKNOWN, conflict question | 4/4 | 4/4 |

The prespecified engineering gate required at least 2/4 **correct** contradiction reversals plus >=50% neutral UNKNOWN, separately for C and D. Neutral controls passed; **reversal requirement FAILED in both arms**.

The raw witness-disagreement decisions were:

| Stem | C original → reversed | D original → reversed | True original → reversed |
| --- | --- | --- | --- |
| F01 (conflict) | UNKNOWN → UNKNOWN | UNKNOWN → UNKNOWN | YES → NO |
| F02 (agreement) | invalid → UNKNOWN | invalid → YES | NO → YES |
| F03 (conflict) | UNKNOWN → UNKNOWN | YES → invalid | YES → NO |
| F04 (agreement) | UNKNOWN → UNKNOWN | invalid → YES | NO → YES |

These results are taken directly from the archived 96-row artifact, **not** inferred from total accuracy. Four answers exceeded the permitted one-label form by adding explanatory prose; those are invalid under the prospectively defined parser and remain in denominators.

## Why 73% is not an organ win

Every neutral-case answer was UNKNOWN for all four semantic questions in both arms (8 neutral-case conflict answers total). Across original and reversed cases, each model correctly noted two separate witnesses. Those easy fields account for much of the high aggregate score. The model nonetheless frequently chose UNKNOWN when the actual witnesses' statements made their *agreement or disagreement* determinate, even when asked about their reports rather than the objective truth.

C and D differ in wording and in how the organ narrates uncertainty. With four stems, no model swap, no actual character actions and zero correct paired reversals, the nominal 6.25-point aggregate D-over-C difference is **not** interpretable as evidence of a cognitive effect. It may reflect more explicit prose or chance, and these fields are correlated.

The stronger model did remove the worst strict-format problem seen in the 135M/360M runs, but **output formatting and evidence-sensitive semantic interpretation remain distinct**. The predeclared gate usefully refused a false-positive continuation study.

## Engineering decision and next scientific gate

Do not repeat or edit these four prompts until scores rise. Publish the negative result and preserve the original artefacts. The immediate research bottleneck is now **evidence-interpretation competency, not JSON syntax**. A new capacity test should distinguish "the witnesses disagree" from "which witness is telling the truth", and verify a larger model with independently written, balanced stories before attempting longitudinal handoffs. It should also explicitly compare if a direct, neutral semantic classifier can track report contradictions without a model generating character language.

A broader Palinode efficacy trial should remain stopped until an independently verified evidence-responsive instrument exists; keep the v1.0 host integration, stress, adversarial and renderer validation work separate.

**Scientific verdict:** successful end-to-end deployment and preserved negative data; cognitive hypothesis not tested decisively. Failed gate is the reported result.
