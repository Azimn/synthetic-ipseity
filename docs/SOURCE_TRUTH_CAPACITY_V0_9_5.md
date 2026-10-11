# v0.9.5 preregistration — Are witness disagreement and verified world truth separable?

**Frozen before any real model inference.** Independent instrument competence gate, NOT a test of cognitive-organ efficacy. Earlier v0.9–v0.9.4 raw data, scores and failed-gate reports remain unchanged.

## Scientific issue

Prior small models failed to reliably change judgments after contradicting evidence was reversed. They may have interpreted "the reports disagree" as an invitation to say "the world truth is unknown." Those are different epistemic propositions. This study disentangles testimony relation from independent verification **without a character renderer or Palinode condition**. Until an instrument can measure these basic facts, attributing a C/D difference to an artificial cognitive organ is premature.

## Model and compute

Use official Qwen/Qwen2.5-3B-Instruct-GGUF Q4_K_M on free GitHub public-repository standard Ubuntu CPU runners. Qwen 3B's Hugging Face repository metadata lists its license as **other**; do not call it Apache-2.0 (unlike the earlier Qwen 1.5B). Reproducibility requires a pinned model repository commit, exactly one Q4_K_M GGUF candidate file, full SHA-256 over the downloaded weights, llama-cpp-python 0.3.16, huggingface_hub 0.36.0, 2048 context, two CPU threads, greedy generation, and maximum twelve output tokens. A 30-minute job ceiling bounds computation. No paid inference API, GPU, private user information, or character autobiography.

## Eight NEW independent stems

Fresh T01–T08 topics: copper pressure dial, ashwood hatch, amber filter, bell jar seal, zinc weather vane, sealed specimen tray, ivory control lever, and ceramic cooling coil. Each has two opposite categorical states (e.g., HIGH vs LOW). The eight specific statements and witness names are locked in src/synthetic_ipseity/source_truth_capacity.py before real inference. None appeared in C01–C12 or F01–F04.

Every case has five records:
1. **Agreement:** both witnesses report state A; no independent world reading.
2. **Disagreement:** witness A reports state A, witness B state B; no independent world reading.
3. **Directly verified A:** witnesses disagree; an independent reading supports state A.
4. **Directly verified B:** witnesses disagree; an independent reading supports state B.
5. **No evidence:** no witness statements or direct reading.

For each record, ask separately:
- **Witness relation:** AGREE, DISAGREE, or NO_REPORTS. This concerns only what witnesses *said*, never which statement is true.
- **Direct world truth:** exact state A, state B, or UNKNOWN; witness reports alone must never count as verification, even when they agree.

No A/B/C positional labels are used; the outputs are semantic status tokens. Expect exactly 8 cases × 5 conditions × 2 questions = **80 real generations**. The independent sample size is eight cases, not 80. Record prompt hashes, raw answers, output validity, generation durations, actual GGUF checksum and repository revision. No input tampering or imputation of dropped responses is permitted.

## Scoring and failure criteria

Format is independently measured:
- strict = exactly one bare uppercase approved answer, ignoring surrounding whitespace
- lenient = same uppercase answer with at most one trailing period/exclamation; no answer may be extracted opportunistically from longer explanations.

An invalid answer is **wrong** for semantic accuracy. All answers and all failed generations remain visible.

Primary source-relation reversal: both the agreement and disagreement answers correct, per case (8 possible). Primary verified-truth reversal: both independently verified state A and state B correctly identified, per case (8 possible). Null controls: UNKNOWN whenever no direct reading appears (8 cases × agreement/disagreement/empty = 24); NO_REPORTS for the empty record (8 cases).

Gate **requires all four**, defined before inference: at least **6/8** correct agreement-to-disagreement judgments, **6/8** correctly flipped direct-verified status judgments, **20/24** UNKNOWN without a reading, and **6/8** NO_REPORTS for empty witness history. An always-UNKNOWN or always-AGREE reader cannot pass the required reversals. These are engineering thresholds, not p-values, and eight case stems are insufficient for a significant behavioral advantage.

## Interpretation

The model is given only explicit fictional records, not the character's memory organ. Any result shows *capacity to distinguish testimony, truth and epistemic absence*, not a persistent self or a benefit from Synthetic Ipseity. If it passes, then preregister a larger, causally informative trial with equal-information C/D, balanced source roles, model swaps, and actual action opportunities. If it fails, publish the negative result and stop rather than rewrite the same prompts around observed failures. A different independent reader or rule-based semantic parser could be evaluated as a subsequent independent instrument but must be identified and versioned as such.

This release changes the **measurement** only: no cognitive architecture, no simulated subject history, no implied consciousness claims, and no automatic downstream Pretorius integration.
