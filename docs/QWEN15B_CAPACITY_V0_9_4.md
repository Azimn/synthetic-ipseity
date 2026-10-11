# v0.9.4 — Qwen 1.5B fresh-stem evidence-capacity preregistration

**Protocol frozen before real model inference.** The real 135M and 360M studies failed semantic-evidence responsiveness under the old letter-choice interface. Their scores and raw reports remain unchanged.

## Model and compute

Official Apache-2.0 Qwen/Qwen2.5-1.5B-Instruct-GGUF Q4_K_M quantization from Qwen's own Hugging Face repository, file qwen2.5-1.5b-instruct-q4_k_m.gguf (~1.12 GB). CPU-only llama-cpp-python 0.3.16 plus huggingface_hub 0.36.0, two threads, 2048 token context, temperature zero, max 8 new tokens, 30-minute free public-repository GitHub Actions limit. Actual model repository SHA, downloaded GGUF SHA-256, prompt hashes and generation outputs are saved. No paid API and no Pretorius autobiography.

## Four new frozen case stems

F01 mercury barometer; F02 oak specimen chest; F03 laboratory water pump; F04 glass observatory roof. Each has two named witnesses with matching or opposite reports. These four topics and speakers have never appeared in the earlier two observed C01/C02 experiments. Two stems start contradictory, two start corroborating.

Two representation arms: C (grammatical first-person control) and D (real PalinodeHost SQLite organ output after acknowledgement). Three exposure conditions for each arm and stem: original witness accounts; second-witness polarity reversed; a neutral no-witness/no-belief/no-recollection record. The four questions independently ask whether witnesses disagreed, whether there were two different speakers, whether the subject noticed a changed belief, and whether the subject subsequently recalled noticing.

There are exactly **4 × 2 × 3 × 4 = 96** real generations. Answers are YES, NO or UNKNOWN. The prompt contains NO A/B/C positional options. All choices, expected responses and source text are fixed in src/synthetic_ipseity/qwen_capacity.py before inference.

## Independent format and semantic measures

Strict format: the trimmed output is literally YES/NO/UNKNOWN. A prospectively specified lenient parser also accepts a bare uppercase value with exactly one optional terminal full stop or exclamation mark; longer explanations cannot be opportunistically parsed. Each invalid answer scores zero for semantic accuracy.

Primary outcome: **correct disagreement reversal**, requiring BOTH the original and polarity-reversed witness question answered correctly per case. A model that always chooses the same word fails regardless of its apparent 50% ordinary accuracy.

Separate controls: neutral question should be UNKNOWN, source-count answer remains YES for original/reversed, and noticed/recall fields are exploratory because C and D expose the same intended facts in lexically different ways. Report prompt word lengths and latency; do not equate differently worded arms with a strong causal identity test.

## Stop or go

The prespecified minimal instrument gate is at least **two correct conflict reversals of four stems and 50% neutral UNKNOWN, separately in each C and D arm**. That threshold tests reading/counterfactual responsiveness only. Four stems are too few for efficacy inference. No model swap or autonomous action occurs in this experiment.

If the model fails, preserve the complete real negative result and do not tune the current stems. If it passes, proceed toward a future independently registered 30+ stem continuity and real action study, including transfer between distinct model families and blinded outcome measures. Passing alone does not validate a subjective organ or consciousness.

## Reproduction

Run the model-free contract tests with Python unittest. Local real inference: pip install -e . then pip install llama-cpp-python==0.3.16 huggingface_hub==0.36.0, then python -m tools.qwen_capacity_cpu --outdir capacity-results. The independent CPU workflow archives raw outputs. No model-free mock counts as an actual scientific result.

## Completed real inference and frozen gate decision

The first full 96-generation Qwen CPU run [#38100242123](https://github.com/Azimn/synthetic-ipseity/actions/runs/38100242123) completed with no model download or inference failure. Both arms passed 4/4 no-evidence UNKNOWN conflict controls but both failed the prespecified 2/4 correct-reversal threshold: C 0/4, D 0/4. Overall answer accuracy was 66.7% C and 72.9% D, inflated by consistently correct neutral and witness-count questions; never interpret that difference as a cognitive advantage. Four actual free-form outputs violated even the prospectively lenient one-word parser. The [permanent empirical results record](../results/QWEN15B_REAL_CAPACITY_2026_10_10.md) includes raw ZIP, model repository, exact GGUF digest and all source checksums. Subsequent runs are manual-only. Original failure reports remain unchanged.
