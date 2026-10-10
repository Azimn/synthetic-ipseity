# v0.9.1 actual CPU-model smoke: two paired cases

**Purpose:** test the experimental transport end to end using *real* language-model inference before attempting a resource-intensive 144-trial pilot. This is NOT a powered test of cognitive benefit and does not replace the v0.9 preregistration.

The public repository's standard ubuntu-latest GitHub Actions runners are free under GitHub's public-repository billing policy. The workflow is only triggered when the CPU experiment's runner or workflow changes on a pull request, or by manual dispatch. There is **no** paid API, GPU runner, scheduled monitoring, or background autonomous billing. The model weights are fetched from the public Hugging Face repositories, and no user or Pretorius personal information is sent to the models.

## Fixed setup (before results)

The smoke uses the existing SHA-locked v0.9 manifest, selecting two fixed case stems **C01** (contradiction) and **C02** (corroboration), the grammar-only **C** and complete-organ **D** arms, and same-model and model-swap handoff conditions. This gives **eight paired trials** and **16 actual generation calls**. The full four-arm experiment and boundary-leakage tests are not run in the smoke. The D transcripts are still emitted by the real SQLite/Palinode organ and not written by hand.

The two small Apache-2.0 instruction models are:

- HuggingFaceTB/SmolLM2-135M-Instruct, first-stage renderer and same-model continuation.
- HuggingFaceTB/SmolLM2-360M-Instruct, alternate second-stage renderer when a swap is indicated.

The runner resolves and records immutable Hugging Face repository commit SHAs, tokenizer prompt token counts, generated token counts, generation latencies, full raw first-stage handoffs, full second-stage responses, expected fields, validity and score. Generation is greedy with temperature zero, a 128-new-token maximum, and a fixed case-level seed. CPU inference uses Transformers with PyTorch CPU on a standard Ubuntu hosted runner, no service token or external completion API.

The 16 calls may fail to produce valid JSON because these models are small. Such failures are **real observations, not exclusions**. They score zero according to the existing locked scorer.

## Auditable outputs

Every workflow run attempts to archive:

- micro-manifest.json — selected prompts, model IDs and source parent manifest SHA
- cpu-model-responses.jsonl — each raw model response and per-call metadata
- cpu-smoke-report.json — descriptive scores for paired C/D trials, model revisions and no-inference-claim warning

The artifact retention is seven days. The runner writes with create-only file mode and flushes each row so partial failures leave an inspectable prefix. The job itself must fail if model download or inference fails; no fake result is substituted. Inspect job logs and artifact completeness before reporting a scientific outcome.

## Interpretation

An observed smoke difference of D-C in either direction is **not** evidence of a reliable advantage or disadvantage: two case stems are not statistically representative, the models are too small to serve as broad character benchmarks, and the matched representations differ in wording and token counts. Even the full v0.9 six-field JSON task mainly measures explicit information retrieval across a two-call handoff, rather than spontaneous continuity or agency.

This exercise can establish only that independent model checkpoints receive the intended inputs, execute generation, preserve provenance, and produce scoreable or explicitly invalid results. The next credible study requires full samples, stronger equal-token controls, multi-model counterbalancing, action-level probes and fresh external validation.

## Execution

The workflow is at .github/workflows/cpu-model-smoke.yml. Changing the runner file or workflow in a pull request automatically executes one CPU test (up to 25 minutes); after merge, it may be triggered manually from GitHub Actions.

If using a workstation with offline-cached weights and the required dependencies, run:

~~~sh
python -m pip install -e .
python -m pip install torch transformers==4.57.3 huggingface_hub==0.36.0 safetensors
python tools/cpu_model_smoke.py --outdir real-cpu-smoke
~~~

This script connects only to the public model file repository for downloads and metadata unless the models are already cached. It does not call a paid completion provider. A model-download failure is an infrastructural result, not an experimental failure of Synthetic Ipseity.

Evidence hygiene: no user-sensitive data, no made-up model outputs, no model advantage claim from fixtures, no cherry-picked case exclusion, and no silent change of selected C/D comparison after results have been seen.

## Observed first run

The actual 2026-10-10 workflow completed successfully and archived full raw model outputs. All eight final responses were schema-invalid: four from the 135M model were non-JSON and four from the 360M model were JSON-syntactic but structurally incorrect. This is an output-schema floor, not a meaningful D-versus-C contrast. The [permanent result record](../results/CPU_REAL_SMOKE_2026_10_10.md) pins source and model checksums and interprets the failure without retrospectively changing the preregistered scorer.
