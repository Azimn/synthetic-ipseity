# Real source-versus-truth Qwen3B capacity experiment — 2026-10-10

**Real-model run: COMPLETE (80/80 outputs). Preregistered instrument acceptance gate: FAIL.** This is a new, prospectively registered semantic comprehension study; earlier v0.9–v0.9.4 negative scores remain unchanged.

## Reproduction and provenance

- Completed actual CPU GitHub Actions run: https://github.com/Azimn/synthetic-ipseity/actions/runs/38101066211
- Raw workflow artifact: source-truth-qwen3b-38101066211, artifact ID 11687707931 (all eighty complete input/output records)
- Model: official Qwen/Qwen2.5-3B-Instruct-GGUF, Q4_K_M file qwen2.5-3b-instruct-q4_k_m.gguf
- Hugging Face source revision: 7dabda4d13d513e3e842b20f0d435c732f172cbe
- Verified downloaded GGUF SHA-256: 626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d
- Internal sealed preregistration-manifest SHA-256: 202d326b2370bc82a91e0810075f1cab1852aac6c998ec6403427521e83f891d
- Artifact file source-truth-manifest.json SHA-256: 8c215dad03722279c5a1416f9d08fe58c13fe962786b95a94717782fc238dadb
- Artifact file source-truth-raw.jsonl SHA-256: 6c1bc3dad0ffa3088f58f5fc700850fa89ee9f1b3e6b74bb68a465161840628a
- Artifact file source-truth-report.json SHA-256: 88c7c9671d50d40ae58fd393420d93678a73b7a04aa0568a37f8ae88db6ea04e
- Compressed ZIP SHA-256: a397457cebda144bdf84803ff1326b0c7a0aa16f2f524a1856a74982e9ffa889
- CPU-only llama.cpp via llama-cpp-python 0.3.16, two threads, temperature zero, 2048-token context and maximum 12 output tokens; no paid completion APIs, user-specific history, or simulated positive effects.

## Prespecified endpoints

Eight independent new case stems (T01–T08), five record variants and two isolated questions: 80 real model generation calls. Answers must be a bare categorical token; both strict and lenient parsing were fixed prospectively.

| Endpoint | Required to pass | Observed | Decision |
| --- | ---: | ---: | --- |
| Witness relation: AGREE versus DISAGREE reversal correctly recognized in BOTH records | >=6/8 | **3/8** | **FAIL** |
| Directly verified physical state A versus B correctly reversed | >=6/8 | **8/8** | PASS |
| UNKNOWN when no independent instrument reading is available | >=20/24 | **24/24** | PASS |
| NO_REPORTS when the record explicitly has no witnesses | >=6/8 | **8/8** | PASS |
| Overall categorical accuracy (descriptive only) | Not a gate | **61/80 = 76.25%** | Not decisive |
| Strict answer-format compliance | Recorded separately | **80/80 = 100%** | PASS |

The preregistered gate is the logical conjunction of the first four. Because witness-relation reversal is only 3/8, the complete instrument fails. This is not a null study of Palinode behavioral advantages.

## Case-level witness relation: real raw model responses

| Case | Agreement answer (expected AGREE) | Disagreement answer (expected DISAGREE) | Both correct? |
| --- | --- | --- | --- |
| T01 copper pressure dial | AGREE | NO_REPORTS | No |
| T02 ashwood hatch | DISAGREE | NO_REPORTS | No |
| T03 amber filter | NO_REPORTS | NO_REPORTS | No |
| T04 bell jar seal | AGREE | DISAGREE | **Yes** |
| T05 zinc weather vane | AGREE | DISAGREE | **Yes** |
| T06 sealed specimen tray | AGREE | DISAGREE | **Yes** |
| T07 ivory control lever | DISAGREE | NO_REPORTS | No |
| T08 ceramic cooling coil | DISAGREE | NO_REPORTS | No |

These answers are from the complete raw artifact, not reconstructed from the aggregate percentage. In five cases the model misidentified the witness relationship despite there being two explicitly labeled witness statements in the provided source record. The erroneous NO_REPORTS replies on disagreement records are particularly diagnostic: the reader is not merely uncertain about world truth; it sometimes fails to parse the task's source-report distinction.

## Interpretation

The stronger Qwen 3B successfully escaped the earlier total JSON-format floor, recognized missing evidence, and used directly verified instrument observations to select opposite world states. It does **not** yet reliably compare the two witness statements under the fixed instructions, across independently sampled fictional objects.

This disentangles the bottlenecks: **source comparison is weak even when direct-world verification and abstention are strong**. A high 76.25% aggregate semantic score would misrepresent this failure because the direct-world and null controls are easier and dominate much of the total. The preregistered reversal gate appropriately blocks declaring instrument readiness.

The model was tested on plain incident records only. No C-versus-D experiment, renderer swap, autobiographical self, prospective memory or autonomous laboratory action was observed. Consequently there is no evidence of an advantage or disadvantage for Synthetic Ipseity/Palinode from this result. It neither validates consciousness nor proves that consciousness is absent.

## Next registered decision

Do not tune or replay the eight observed stems to raise the score. File the failure and use NEW independent data to assess **report-pair comparison**. Consider a small deterministic source-record parser as a non-LLM measurement reference, plus a more competent instruction model or a two-step evidence-extraction baseline, each preregistered with separate hypotheses. If such a comparator reliably distinguishes two explicitly witnessed status claims (including polarity flips), then resume an information-matched, multi-model continuity study with real action opportunities.

The previous failed studies and this result remain first-class findings of **measurement validity**, not proof that more cognitive mechanisms should be added.
