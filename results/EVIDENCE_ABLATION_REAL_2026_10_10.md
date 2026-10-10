# Real v0.9.3 Evidence Ablation: completed 2026-10-10

**Verdict: evidence-responsiveness gate FAILED for the tested 135M/360M SmolLM2 checkpoints.** This is a negative *measurement feasibility* result, NOT a scientific result about synthetic consciousness, character continuity or Palinode's value.

## Immutable provenance

- Successful real CPU [GitHub Actions run #38095345440](https://github.com/Azimn/synthetic-ipseity/actions/runs/38095345440).
- Artifact: evidence-ablation-38095345440, artifact ID 11685453261.
- Recorded internal sealed manifest SHA-256: 09d2545f78b6f3fbb4ceeaa9c423291418b123c0850ce47335a2a77d99f5b91b
- Raw ablation-raw.jsonl SHA-256: ed14e09d73f78c706e1307976909f3900f93470cd655aea7ffb81b56f4676933
- ablation-manifest.json SHA-256: f6e546c8bb28373ef4a7c313448dabf9dad95348dbf919314cff1748c60a5483
- ablation-report.json SHA-256: 71daf2a487e1e70bcafca9c3cac401fd9844e8aedfa127dd35c859b306540921
- ZIP SHA-256: ece49d5e0c708dac779aa5a45ba235c0f4807730f406defec34a4f49aacbcef1
- SmolLM2-135M-Instruct model commit: 12fd25f77366fa6b3b4b768ec3050bf629380bac
- SmolLM2-360M-Instruct model commit: a10cc1512eabd3dde888204e902eca88bddb4951
- 144 authentic next-token logit choices, no simulator, no paid inference API, two fixed independent case stems, two representation arms, and matched options held fixed across original, reversed and no-evidence conditions.

## Locked measurement results

All rows use 12 field probes (2 cases × 6 fields). Ten per row have a genuinely reversed correct answer (all except sources).

| Arm | Model | Original accuracy | Reverse accuracy | Selected option flips (among 10) | **Correct reversals (among 10)** | Changed vs neutral (among 12) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| C | 135M | 4/12 (33.3%) | 4/12 (33.3%) | 1/10 | **0/10** | 2/12 |
| D | 135M | 4/12 (33.3%) | 4/12 (33.3%) | 3/10 | **1/10** | 2/12 |
| C | 360M | 6/12 (50.0%) | 4/12 (33.3%) | 0/10 | **0/10** | 0/12 |
| D | 360M | 7/12 (58.3%) | 4/12 (33.3%) | 0/10 | **0/10** | 1/12 |

Observed complete-choice distributions confirm near-pure option position preferences:

- C/135M original: B 10/12, A 2/12; neutral: B 12/12.
- D/135M original: B 10/12, A 2/12; neutral: B 12/12.
- C/360M original: B 7/12, C 5/12; neutral: B 7/12, C 5/12.
- D/360M original: B 8/12, C 4/12; neutral: B 7/12, C 5/12.

The neutral baseline changed essentially nothing; the counterfactual that reversed witness evidence also rarely changed the chosen letter. The evidence-responsiveness gate correctly **rejects** these models.

## Interpretation and stopping rule

Even a model that scores 58.3% on the original two cases cannot be trusted as a semantic instrument if it gives the same answer after the source facts reverse. More probes of the same two cases would not solve this problem. The result says **these tiny models, with this forced-next-token letter interface**, do not provide a meaningful downstream outcome signal.

No claim follows that Palinode is better, worse, equivalent or conscious. The organ's deterministic first-person safety/access contract remains an independent engineering result, not affected by this instrument's scientific failure.

**Do not optimize the option templates on these same failed examples.** A new preregistration should add a stronger, reputable instruction-following model (about 1B–2B parameters with reasonable CPU quantization), independent case stems and polarity/source-role counterbalancing. First show that semantic selection is sensitive to changed evidence under BOTH direct and neutral controls; only then attempt a long-term C/D model-handoff study.

The v0.9 locked strict-six-field JSON results and the real v0.9.2 format-floor calibration and their raw-output hashes are preserved unchanged. This negative result belongs in the research journal as a measurement-validity finding.
