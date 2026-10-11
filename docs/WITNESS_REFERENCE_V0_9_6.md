# v0.9.6 — Deterministic witness comparator reference

**Engineer-only instrument, not a cognitive organ.** Frozen scope: a strict machine-formatted incident record grammar. This is NOT a natural-language understanding benchmark, a general scientific null or proof that Synthetic Ipseity improves character behavior.

## The measurement problem

In the actual v0.9.5 Qwen 3B trial, all 80 outputs were formatted correctly and 61 were accurate, but only 3 of 8 witness relation reversal pairs were jointly correct. Direct verified state reversal was 8/8 and no-direct-reading abstention 24/24. Those historical results remain unchanged.

A basic deterministic comparator should have no difficulty identifying agreement among two explicitly attributed categorical observations. We test this *within a restricted grammar*, not as a claim of broad machine cognition.

## Grammar and provenance boundary

The parser receives the source text only, without case identifier, expected value or existing Qwen model score. It requires:

- A single incident header naming the object/topic
- Exactly two distinct named witnesses, each giving a simple uppercase categorical status for that same topic, OR the explicit no-witness/no-reading three-line marker
- Exactly one independently verified reading of the same topic, OR an explicit absence-of-reading marker

Witness order does not matter. A direct reading can disagree with witness testimony. Agreement among two witnesses is NOT converted into direct world verification. No source trust or hidden psychological claim is inferred.

Out-of-grammar inputs, extra or duplicate witnesses, topic mismatches, injected instructions, unknown grammar, invalid negations, malformed records and unexpected direct readings must explicitly ABSTAIN (without exporting partial conclusions). Source parsing results carry validation status, witness relation, verified state if any, and an internal reason code. These internal codes are *not* character experiences and must not bypass the existing subject-admission boundary. If one day integrated into a character host, the engineer's verdict must be independently attested and translated into an allowed first-person experience, never passed in raw database or tool state.

## Fixed reproducible cohorts

1. **Original v0.9.5 input grammar**: eight historical cases, five evidence variants, two questions = **80** expected choices, independently parsed from raw incident records.
2. **Fresh heldout input grammar**: sixteen new U01–U16 laboratory topics, five variants, two questions and both witness statement orders = **320** expected choices. The heldout fixture renderer is separate from the reference parser. This is fresh grammar vocabulary, not an external blind study.
3. **Malformation/adversarial controls**: **21** distinct schema violations including extra instructions, witnesses, malformed statuses and conflicting source attribution, all of which must abstain and expose no inferred verified truth.

Test nulls for repeated witness identities, contradictions to a direct reading, unregistered categorical states, CRLF, free-form language, missing sources and unauthorized subject access. The report prints per-cohort counts and exits nonzero if any known test is wrong.

Reproduction:

    python -m pip install -e .
    python -m unittest discover -s tests -p 'test_witness_reference.py' -v
    python tools/witness_reference_diagnostic.py --report /tmp/witness-reference.json

The main GitHub CI runs tests across Python 3.11, 3.12 and 3.13. This requires zero model downloads or inference.

## Acceptance and scientific limits

The predeclared reference gate is **80/80** historical correct choices, **320/320** heldout choices, **21/21** out-of-grammar explicit abstentions. There is no opportunity to invent missing data. Correctness under this input schema is a unit-level engineering result, NOT evidence of semantic comprehension of arbitrary language. It is also not a causal test of Palinode, character identity, subjective experience, or autonomous activity.

For a legitimate future study, use balanced free-form human-authored testimony and independently annotated relations, explicitly measuring coverage and abstention rates for the strict parser. Separately evaluate language model interpretations with source attribution and action-based character continuity. Do not mistake perfect machine-grammar parsing for general artificial cognition.

The original v0.9-v0.9.5 empirical data and all negative observations remain intact.
