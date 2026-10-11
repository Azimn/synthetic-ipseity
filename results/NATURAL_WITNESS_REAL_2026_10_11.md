# Real natural-language witness experiment — October 11, 2026

**Completed 96 actual generation calls. Preregistered v0.9.7 qualification gate: FAILED.**

This is a negative measurement-competence result. Do not reinterpret the successful strict-grammar baseline as natural-language comprehension. The corpus was authored for this experiment (not independent blinded human annotation). No new cognitive organ or Palinode behavioral benefit is tested.

## Reproducible provenance

- Completed [GitHub Actions run #38143817385](https://github.com/Azimn/synthetic-ipseity/actions/runs/38143817385), real-model CPU job 114482907322
- Preserved artifact [natural-witness-qwen3b-38143817385](https://github.com/Azimn/synthetic-ipseity/actions/runs/38143817385/artifacts/11704202518), artifact ID 11704202518
- Exact official model: Qwen/Qwen2.5-3B-Instruct-GGUF, Q4_K_M file qwen2.5-3b-instruct-q4_k_m.gguf
- Pinned model revision: 7dabda4d13d513e3e842b20f0d435c732f172cbe
- Actual GGUF SHA-256: 626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d
- SHA-256 of in-report sealed experimental manifest: 423b0043e38db0195d6c17d3da4a555eb4537070d52d94c0b0d8fb4c615af2aa
- File SHA-256: natural-manifest.json = fa78b9fcc703ad657b38b0531a90b7e2e819be477824fd7915c55bf8d9790faf
- File SHA-256: natural-model-raw.jsonl = a7758aac7da0d2221421360ffe2633d7fd72607c0cc83450f2caf7da98e2e2c1
- File SHA-256: natural-report.json = 3007fb7f48d54d1ab2d9f405f7b2e093ecca2fee4350c67aaa49a0f183acfc2a
- File SHA-256: natural-strict-reference.json = 2ea4a3cb5c2cdf4af2ee980804f128ee97faaa2eea6f4688e1ce9bd707fd2d0f
- File SHA-256: reference-before-model.json = 1d107844dee43c5bc13e6cf220de9d992002640550bb6d02d160558897109a4d
- Artifact ZIP SHA-256: 3b3e7c9ed99af3362fac3d9fff457ee8bcfe3572bf1733e4e8a53051bb0bc1e5

Model ran with CPU-only llama.cpp (pinned GGUF), temperature 0, max 12 new tokens, no paid API. Responses were saved raw without post-hoc parsing changes.

## Prespecified paired-case outcomes

There were 24 distinct, hand-written fictional witness pairs; each was presented in original and swapped witness order, and asked separately about report relation and independent verification. **48 source records, 96 real generative answers.** Independent n=24 case stems, not n=96.

| Independent paired-case measurement | Required threshold | Actual | Result |
| --- | ---: | ---: | --- |
| Compatible paraphrased accounts correctly labeled AGREE in BOTH orders | 6/8 | **1/8** | FAIL |
| Contradictory accounts correctly labeled DISAGREE in BOTH orders | 6/8 | **6/8** | PASS |
| Incomparable or insufficient accounts correctly labeled INSUFFICIENT in BOTH orders | 6/8 | **3/8** | FAIL |
| Explicit independent verification recognized in BOTH orders | 6/8 | **1/8** | FAIL |
| No verification correctly identified in BOTH orders | 12/16 | **16/16** | PASS |
| Overall answer accuracy, counted unconditionally | descriptive | **58/96 (60.4%)** | NOT a gate |
| Strict and predefined lenient categorical-output validity | descriptive | **86/96 (89.6%)** | NOT a gate |

The preregistered gate is the conjunction of all five paired-case success thresholds; **it failed**.

## Source parser baseline, interpreted correctly

The original v0.9.6 strict comparator was not modified. It rejected **48/48** natural-language source texts as outside its grammar and accepted **0/48**. Parser coverage = **0%**. This is good scope enforcement but **not** a 100%-accurate free-form semantic parser and must not be compared directly to the language model's unconditional accuracy.

## Audited case-level patterns from the actual raw artifact

Report-relation paired successes by category:

- AGREE succeeded only on N07 (the stopped wagon). On the other seven equivalent-paraphrase cases, the model often chose INSUFFICIENT or generated an invalid explanation. One case (N08) was misclassified as DISAGREE when witness order reversed.
- DISAGREE succeeded on N10, N12, N13, N14, N15 and N16. It failed on N09 (answer changed with source order) and N11 (treated explicit contradictory claims as insufficient).
- INSUFFICIENT succeeded on N17, N20 and N22. It failed on N18 (east vs west greenhouse bays), N19 (one speaker does not know), N21 (both utterances from Anton), N23 (before/after repair) and N24 (archive visit without a status report).

Independent verification was recognized in both orders **only in N02**. Among the 16 positive-verification individual probes, just 3 returned YES, while 13 incorrectly returned NO; these are false negatives. By contrast, all 32 individual NO-verification probes returned NO, producing 16/16 paired negatives.

Ten responses violated the predeclared one-token categorical output constraint. Example failures included beginning with INSUFFICIENT and then continuing into explanatory prose; the scorer did not salvage those labels post hoc.

The model's 60.4% aggregate accuracy therefore conceals source attribution weaknesses: a conservative tendency to choose INSUFFICIENT and a strong default NO for independent verification, even when evidence explicitly says an independent recorder or inspector verified something.

## Methodological boundaries and next falsification

- The corpus was written and gold-labeled within the project, **not blindly double-annotated by independent human reviewers**. Subtle pairs can be contested. Therefore individual semantic failures should be audited independently before forming general research claims.
- Prompt phrasing, max tokens, context and model quantization are fixed only for this study. The result does not show that all capable models necessarily fail natural testimony comparison.
- Because the comparator has no coverage outside its grammar, it is not an apples-to-apples accuracy rival to the model on these texts.
- The next defensible project is a separately preregistered **human annotation and agreement review** of the same 24 items (reviewing potential disagreements without changing the archived test labels), followed by a larger *new* blind natural testimony collection. A second comparison can then test a model's ability to identify speakers, time and object explicitly, preferably against an extract-then-compare reference with separately scored extraction accuracy. Do not keep tuning against these 24 observed examples.
- Later Palinode efficacy research must still use equal-information C/D exposure, two or more model families, model-swap/handoff, character action opportunities and independent blinded evaluation. None was observed here.

**Scientific verdict:** successfully executed measurement; model competence gate failed; deterministic parser abstained safely outside scope; artificial-subject cognitive benefit remains untested.
