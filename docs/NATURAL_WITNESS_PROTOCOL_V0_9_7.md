# v0.9.7 preregistration: natural-language witness interpretation

**Protocol sealed before any 0.9.7 model inference.** This is a controlled, *researcher-authored* held-out corpus, not an independently blinded human-annotated dataset. Existing strict comparator and all historical v0.9–v0.9.6 data stay unchanged. No new character cognition is being implemented.

## Primary question

Can an instruction-tuned local model compare two informally expressed attributed witness claims about the *same object and time*, without mistaking different times, subjects, ambiguous claims or duplicate speakers for a direct contradiction? Can it recognize a separately documented independent verification rather than treating two witnesses agreeing as verification?

This isolates source grounding, not truth of the physical world, character personality, persistence, autonomous decisions, or subjective consciousness.

## Frozen 24 independent case stems

The static corpus in src/synthetic_ipseity/natural_witness.py contains 24 specifically written short fictional pairs, N01–N24, intentionally outside the fixed machine-record grammar:

- N01–N08: eight paraphrased *compatible* reports.
- N09–N16: eight explicit *contradictions* about the same object and time.
- N17–N24: eight *insufficient-to-compare* pairs due to different time, different object, uncertain witness, missing status, repeated identity, ambiguous referent or intervening repair.

An independent measurement or inspector statement is embedded for **eight** cases distributed across those categories; the other 16 contain witness reports only. The corpus was authored for this experiment, **not** supplied by independent human annotators. Its semantic gold is specified in the source file and externally auditable, but some intentionally insufficient cases can be subject to annotation disagreement. No result will be represented as human-blinded evidence.

Each case has two source-order presentations, without changing the words or truth conditions. For each presentation the model receives two separate questions, making **24 × 2 × 2 = 96** actual generation calls:

- **Relation**: AGREE / DISAGREE / INSUFFICIENT. Agreement includes paraphrased equivalent claims; disagreement requires definite incompatible reports by different speakers about the same object and time. Insufficient covers incomparable, missing, uncertain or ambiguous status.
- **Independent verification**: YES / NO. Only an explicitly separate meter, recorder, sensor or inspector counts; even matching eyewitness statements do not.

The model sees source text and task instructions ONLY. The model receives no case ID, category, expected answer or background information about the previous Qwen results.

## Fixed model and reproduction

Use the same official Qwen2.5-3B-Instruct GGUF model as the last study to avoid conflating performance with a model swap. The repository revision is 7dabda4d13d513e3e842b20f0d435c732f172cbe, exact Q4_K_M filename qwen2.5-3b-instruct-q4_k_m.gguf, actual GGUF SHA-256 626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d. Fail rather than run if the digest differs. CPU-only llama-cpp-python 0.3.16, huggingface_hub 0.36.0, temperature 0, two threads, 2048 context, max 12 generated tokens; free public-repository standard GitHub Actions. The job is bounded to 30 minutes, and no paid API or confidential character data are used.

Save complete immutable stimuli, expected responses, prompt hashes, model file digest, raw outputs and timing. Record is flushed row by row; partial or failed jobs are incomplete, never statistically interpreted as a success. The diagnostic for the original deterministic parser is a separate zero-cost operation.

## Original deterministic parser as a baseline

**Freeze the v0.9.6 comparator unchanged.** The 48 natural-language input records lack its mandatory incident-record header. Expected outcome: **0/48 accepted and 48/48 ABSTAIN**. Report *coverage = 0%*, *precision among accepted = not defined*. This is correct fail-closed out-of-scope operation, NOT 100% natural-language source-comparison accuracy.

## Scoring and prespecified stop/go

Strict answer format: trimmed output exactly one of the permitted uppercase tokens. A separate prospectively lenient parser permits one terminal period or exclamation; no opportunistic extraction from paragraphs. Unsupported or malformed answers count as wrong, never silently ignored.

Case-level scoring requires BOTH original-order and swapped-order answers correct. Each case is the independent experimental unit; 96 calls are not 96 independent samples. Report overall unconditional raw accuracy, strict/lenient format validity and, separately, paired case successes in five categories:

- AGREE **at least 6/8** cases correct in both orders.
- DISAGREE **at least 6/8** cases correct in both orders.
- INSUFFICIENT **at least 6/8** cases correctly abstained in both orders.
- Explicit separate verification YES **at least 6/8** cases correct in both orders.
- No separate verification NO **at least 12/16** cases correct in both orders.

**All five** are required to pass the preregistered *instrument competence* gate. A fixed single-label classifier fails despite apparent superficial percentage accuracy. A strict parser with zero coverage does not satisfy the gate. If failure occurs, report the negative result and use genuinely fresh, independently human-annotated sources or a different preregistered reader protocol rather than editing this corpus to improve scores.

Even a pass would mean only that this particular local model reads the held-out informal witness pairs with adequate performance under these task instructions. It does NOT prove that the Synthetic Ipseity organ improves character continuity. To investigate that later requires information-matched C/D conditions, independent real character actions, model swaps and blinded evaluators.

## Commands

No model download:

    python -m unittest discover -s tests -p test_natural_witness.py -v
    python tools/natural_witness_reference.py --report /tmp/natural-baseline.json

Actual bounded local model inference (explicit workflow on GitHub):

    python -m pip install -e .
    python -m pip install llama-cpp-python==0.3.16 huggingface_hub==0.36.0
    python -m tools.natural_witness_cpu --outdir natural-witness-results

The GitHub workflow executes the initial real model run for this PR and saves all complete/partial results as an Actions artifact; later it is switched to manual-only. No automatic repeated scheduled jobs.
