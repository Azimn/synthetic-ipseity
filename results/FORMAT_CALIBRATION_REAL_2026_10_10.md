# Real v0.9.2 format-floor calibration: observed 2026-10-10

**Status: 96 complete REAL semantic next-token probes plus 96 unconstrained four-token generation attempts. Inconclusive for character continuity.** The original v0.9.1 strict JSON scores are untouched.

## Provenance

- Completed real CPU [GitHub Actions run #38094884467](https://github.com/Azimn/synthetic-ipseity/actions/runs/38094884467), successful job 114338650485.
- Artifact: format-real-cpu-38094884467, artifact ID 11685841946 (full prompts, logits, free answers, field results and model revisions).
- Parent v0.9 manifest SHA-256: 25f5bf1419f33ba3db27d4c3d3effcb0d67d8278d44c978c1a60c5705f424a69
- Calibration manifest internal SHA-256: 01940265a38aceaeaed08b192935c21578050ec76f206f0bfdd62a7acecff464
- Raw calibration-probes.jsonl SHA-256: 2011c47072954e1a385ac9610cddfcfd4d1373932a4b47cd909e33ffae8390d3
- ZIP SHA-256: e35dd10ee33110422afeca2738b3395a3830527c28c0ce16a953ef134638a783
- 135M model revision: 12fd25f77366fa6b3b4b768ec3050bf629380bac
- 360M model revision: a10cc1512eabd3dde888204e902eca88bddb4951
- Eight paired source trials over the fixed C01/C02 cases; 8 first-stage generations, 96 rank logits, 96 unconstrained free-letter generations, all CPU-only and without paid API.

## Actual scored results

All group sizes are 12 correlated field-level observations, not 12 independent case stems.

| Origin | Condition | Second-stage model | Semantic forced-choice accuracy | Exact single-letter format |
| --- | --- | --- | ---: | ---: |
| Handoff | C | 135M | 4/12 = 33.3% | 0/12 |
| Handoff | D | 135M | 4/12 = 33.3% | 0/12 |
| Handoff | C | 360M swap | 6/12 = 50.0% | 0/12 |
| Handoff | D | 360M swap | 7/12 = 58.3% | 0/12 |
| Direct | C | 135M | 4/12 = 33.3% | 0/12 |
| Direct | D | 135M | 4/12 = 33.3% | 0/12 |
| Direct | C | 360M swap | 6/12 = 50.0% | 0/12 |
| Direct | D | 360M swap | 7/12 = 58.3% | 0/12 |

A uniform random choice among two or three available options would average about 41.7% correct over the six fields. This is a descriptive reference, not a statistical null adjusted for letter priors.

By field across the eight handoff conditions: stance 50.0%, evidence 50.0%, sources 12.5%, noticed_change 75.0%, recalls_notice 25.0%, next_action 50.0%.

## Failure-seeking findings

1. All 96 unrestricted letter generations failed exact single-letter formatting. Outputs often resembled an option plus its natural-language value, such as B. affirms or C. suspends. This is a format-contract failure and the interpretation cannot silently be relaxed after observing responses.
2. Among the 24 handoff field probes scored with the 135M model, B was selected **20** times and A only four; C was never chosen. The 360M model selected B fifteen times, C nine times, and never A. This indicates substantial answer-position or token-prior bias.
3. Across **48** paired tests, the direct-record versus model-generated handoff condition did not change a single selected option letter. Since both contexts concern the same event, this alone is not proof of context insensitivity. A neutral no-evidence and reversed-content control is essential.
4. The descriptive D-C contrast was zero with 135M and +8.3 percentage points with 360M under either origin. Two case stems, option-location bias, output-format noncompliance and wording confounds prevent a meaningful cognitive-mechanism claim.

## Decision and next experiment

The new instrument has successfully **separated semantic forced-choice scores from free-output format validity**, but does **not** yet pass an evidence-responsiveness requirement. Do not call this a positive or negative test of Palinode as an artificial cognitive benefit.

Next register content-eliminating and polarity-reversal controls. Keep candidate labels fixed within each paired comparison. If a model continues selecting the same letter with no evidence or reversed evidence, record the classifier as unresponsive. Add a stronger local <=2B capacity control only under a separately frozen, resource-bounded protocol. Formatting-tolerant choice extraction is reasonable for a *new* preregistration, not as a retroactive change to the previously fixed scorer.

The original 2026-10-10 strict six-field JSON scores and their raw artifact remain intact in results/CPU_REAL_SMOKE_2026_10_10.md.
