# Deterministic witness comparator — measured reference v0.9.6

**Observed October 11, 2026. Engineering instrumentation result, not a behavioral cognitive benefit.**

## Audit trail

- CI run: https://github.com/Azimn/synthetic-ipseity/actions/runs/38142093965
- Python versions: 3.11, 3.12 and 3.13, **all successful**; standard unittest discover: **280 tests**.
- Additional executable reference diagnostic: tools/witness_reference_diagnostic.py, invoked automatically by CI, no local or paid LLM calls.
- Parser: src/synthetic_ipseity/witness_reference.py, version ipseity-witness-reference/0.9.6.
- Protocol and limitations: docs/WITNESS_REFERENCE_V0_9_6.md.

| Fixed testing population | Observed | Expected | Outcome |
| --- | ---: | ---: | --- |
| Original v0.9.5 formatted inputs (8 sources × 5 conditions × 2 questions) | 80/80 correct | 80 | Passed |
| Newly specified U01–U16 formatted source records (16 × 5 conditions × 2 witness orders × 2 questions) | 320/320 correct | 320 | Passed |
| Adversarial/out-of-format input variants, explicitly abstaining | 21/21 rejected | 21 | Passed |

All 80 historical source records were parsed without consulting the source-case metadata or original expected answer; the scoring harness separately computed the gold answers. The fresh heldout corpus uses 16 different laboratory topics and a separately authored fixture generator; swap of witness order does not change agreement. The adversarial corpus deliberately alters syntax, attributions or introduces extra text: the parser returned ABSTAIN and no verified fact in every such case.

## Meaningful comparison to the earlier real model

The independently measured Qwen2.5-3B-Instruct v0.9.5 experiment on **the same documented structured grammar** produced 61/80 valid-and-correct answer fields, 3/8 correct agreement/disagreement reversals, 8/8 verified-state reversals, 24/24 direct-reading-absence abstentions, and 8/8 absence-of-witness detections. Source: results/SOURCE_TRUTH_REAL_QWEN3B_2026_10_10.md; real model Actions run 38101066211.

The reference parser correctly handled the analogous 80 source/answer items and 8/8 agreement/disagreement reversals, but this is NOT a broad apples-to-apples language understanding comparison: the parser is intentionally restricted to a machine-created grammar that precisely encodes categorical witness statements. That is why it works. It cannot read general prose, infer trust or credibility, update a subject's autobiographical state or select character actions. It must reject unsupported natural language.

The useful engineering result is a **ground-truthable reference instrument** for strict-format witness records, with a measurable coverage boundary and safe abstention. It may later serve as a private engineering oracle for measuring a separate model's source comprehension; it must NOT be inserted into a character's first-person thoughts as an unverified verdict.

## Interpretation and next falsification step

The v0.9.5 language-model inference failure can no longer be explained by ambiguous *record-format gold labels* alone: under the strict specification, all source claims and report relations are determinate. The model's correct-reversal deficit may still result from prompt interpretation, model capability or task framing.

For publishable conclusions, the next study needs truly independent free-form testimony with blinded gold source-pair relations, report source identity, safety and coverage rates for the deterministic comparator, and a qualified language-model reader. Do not use the reference's 100% on an explicitly specified grammar as evidence of broader cognitive efficacy or artificial consciousness.

The original v0.9–v0.9.5 empirical negative results and v1.0 release gates remain unchanged. No new artificial cognitive architecture or renderer bypass was introduced.
