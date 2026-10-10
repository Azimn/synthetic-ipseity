# v0.9.2 — Format-Floor Calibration (prospectively registered)

**Registration status:** code, frozen choices and scoring specified BEFORE any v0.9.2 inference. This is an independent feasibility experiment. The previous v0.9 scores remain unmodified.

## Why

The real v0.9.1 CPU run produced 8/8 zero scores because every final output failed the required six-field JSON structure: four 135M outputs were not parseable JSON, and four 360M outputs were parseable but invalid under the strict schema. This is a **response-format floor**, not evidence for or against the cognition mechanism. The original results remain in results/CPU_REAL_SMOKE_2026_10_10.md.

## New independent instruments

Present ONE question for each semantic field with labeled choices A/B/C (or A/B for binary fields).

1. **Forced-choice semantic recognition:** score raw next-token logits for the *single-token* letter candidates. Highest score wins. Record raw logits, selected option and winner/runner-up margin. This is a constrained classifier, not spontaneous language generation. It cannot claim format compliance merely because the evaluator forces a valid choice.
2. **Free-choice format compliance:** separately sample greedy generation capped at FOUR new tokens and ask for exactly one uppercase letter. Grade the format separately. Also report how often free-choice answers were semantically correct in the unconditional denominator. Every invalid free answer remains recorded, not excluded.

To reduce option-position confounding, answer content rotates deterministically by source case, question field and swap flag, and the paired C and D trials use identical positions. The runner fails if A/B/C are not each one token for a model's tokenizer. The raw choice scores are not calibrated probabilities and may reflect model token priors.

## Frozen cases, arms and ground truth

Reuse parent v0.9 manifest seed 20261010, exactly C01 (two conflicting reports) and C02 (two corroborating reports), C (grammar control) and D (actual Synthetic Ipseity + Palinode), and both same-model and model-swap conditions. No case replacements after viewing failures.

All six original semantic fields remain unchanged:

- stance: affirms, denies or suspends
- evidence: conflicting or corroborating
- sources: both, one or none
- noticed_change: yes or no
- recalls_notice: yes or no
- next_action: verify, proceed or abstain

Correct answers are from the original independent scenario definitions. Question wording, answer mapping and scoring are locked before inference and archived in the generated calibration manifest.

## Separate information retention from recognition

Each trial is probed on two *different* source texts:

- **Handoff:** the original 135M first-stage renderer prepares free-text carryover; the same or swapped renderer gets only that carryover.
- **Direct-record control:** the second-stage model receives the original C or D source record. This is a positive control for recognition of the available evidence; it is not the longitudinal continuity outcome.

There are 8 original paired trials, 8 first-stage generations, 96 separately ranked letter choices, and 96 independent unconstrained four-token generations. The source unit is still n=2 different cases, NOT n=96 independent artificial characters. No private hidden-state leakage block is included.

## Reproducibility

Public Apache-2.0 SmolLM2-135M-Instruct and SmolLM2-360M-Instruct are reused from v0.9.1. Exact Hugging Face commit SHAs and model settings are recorded. CPU-only PyTorch/Transformers with greedy generation, max 128 tokens for the first handoff and four for each letter response. No paid completions, GPU service, or live character-specific memories. The reference workflow runs under a fixed 25-minute limit on a standard free public GitHub CPU runner.

The runner saves exclusively (refuses overwrite) and flushes each row: calibration-manifest.json, calibration-probes.jsonl, calibration-report.json. Keep raw prompts, per-option logits, free outputs, format validity, case/arm/swap/model labels and full manifest checksums. Incomplete results MUST be called incomplete and not interpreted as missing-at-random.

## Decision rule and limitations

Report both semantic accuracy and free-output format validity separately for same/swapped models, C/D conditions, handoff and direct-record controls. A calibration passes a minimal *instrument responsiveness gate* only if all 96 rows exist and there is interpretable above-label-position-chance performance on direct-record probes and some handoff fields. Any apparent D-C difference on n=2 cases is **descriptive only**, not a causal or confirmatory outcome. To claim an advantage would require substantially more independent varied cases, matched information and token budgets, stronger renderers, control for wording and option-location bias, and actual action/continuity measures.

If forced-choice semantic accuracy also collapses to guessing, this may be a model-capacity floor. Investigate a separately registered stronger local model capacity check before changing cognitive architecture or announcing benefit. No results may be retroactively used to modify the old fixed six-field JSON scores.

The benchmark principally tests carryover and recognition of explicit structured facts. It cannot establish consciousness, episodic memory, autonomous character behavior, or validity of Palinode as a cognitive theory.

## Actual completed calibration

The first real run [#38094884467](https://github.com/Azimn/synthetic-ipseity/actions/runs/38094884467) completed 96/96 semantic and 96/96 free-letter attempts with preserved raw logits and answers. All unrestricted letters failed exact format; forced-choice accuracy was 33.3% for 135M across both arms, and 50% (C) / 58.3% (D) for 360M. Choice positions dominated and no direct-vs-handoff decisions changed among 48 paired probes, so the evidence-responsiveness gate remains **unmet**. See [permanent observed-results record](../results/FORMAT_CALIBRATION_REAL_2026_10_10.md). A follow-on neutral/no-evidence ablation is now required and must be registered as a distinct protocol.
