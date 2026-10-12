# Real reference-host first-person boundary conformance — 2026-10-11

**Result:** PASS across the full trusted reference-host integration. **Not** a universal security theorem or a language-model behavioral improvement.

## Verified execution

- Pull request: https://github.com/Azimn/synthetic-ipseity/pull/29
- Python 3.11/3.12/3.13 GitHub Actions run: https://github.com/Azimn/synthetic-ipseity/actions/runs/38205046467
- Reproducible executable: tools/fpeb_integration_gate.py
- Regression suite: tests/test_fpeb_integration.py
- Exact engineering contract: docs/FPEB_END_TO_END_GATE_V0_9_9.md

The three-version CI completed successfully. On Python 3.11, the main unittest discover executed **306 tests** (all passing). The separate explicit integration CLI executed a control subject plus **32 differentiated private host-state variants**, each with a real three-tick SQLite durable progression, complete reference-host restart, and two subject-only text deliveries through the real SubjectOnlyRendererPort. Diagnostic output contained n_differential_variants = 32, n_callback_deliveries_per_trial = 2, status = PASS.

## What was actually held invariant

Every variant included the same explicitly acquired instrument reading (eight degrees), heard claim by Henry about a locked cabinet, and reconstructed childhood account. That was the **authorized subject exposure**. Source reference identifiers, unattested tool content, unacquired tool content, unacquired bodily intensity, and sometimes an additional unperceived high-salience world event were independently varied.

The test compared actual text delivered through the renderer callback, not just a projected Python object. All 32 variants produced identical subject-visible input strings. Adding a hidden event correctly advanced its host cursor without producing a new frame; a silent third tick correctly produced no fabricated inner monologue. A different fake renderer family did not change its inbound subject experience, though a real checkpoint-swap experiment remains unperformed.

## Positive and negative controls passed

- Legitimately observed numeric instrument text survived: no indiscriminate numeric censorship.
- Attributed heard testimony reached the subject; it was not promoted to independently verified world truth.
- The reconstructed childhood account was explicitly not represented as lived memory.
- Nonacquired tool content and unattested pseudo-SYSTEM tool instructions never reached the model callback.
- Changing hidden body intensity, privileged source IDs, or unperceived world events did not change model input.
- An unauthorized other-subject event rolled back with no cursor or outbox progression.
- A renderer exception left a leased subject frame pending; on lease expiry and restart, the same permitted text could be delivered and acknowledged.
- A truly observed hostile phrase remained framed as perceived source text rather than a new governing instruction. **This does not guarantee downstream prompt-injection resistance.**

## Scope limitation

The test used the existing SQLite-backed trusted host and a deterministic fake model callback, **not an LLM**. The host could have other model ingress paths not covered by this test; no Python-process or operating-system isolation stops privileged host code from bypassing the port. Host attestations are assumed truthful. First-person projection quality is not measured here. Exactly-once external actions remain unsupported; outbox delivery is at-least-once.

Therefore the justified result is **reference integration conformance to an observational-equivalence invariant**, not a proven global noninterference theorem, reliable free-form semantic competence, character consciousness, or an advantage over equally informative first-person prompts.

## Next engineering release gate

Finish an **auditable real-host integration profile**: enumerate every way a production consumer constructs model messages, obtains memory/retrieval/tool context, handles prompts and action results, and restarts or swaps renderer models. Fail the integration if any other channel passes privileged raw host data to character cognition. Then exercise actual Ollama-backed renderer(s) with no privileged credentials or direct state access, preserve separately authorized action feedback, and compare behavior against an information-matched first-person narration baseline.

The remaining v1.0 scientific instrument gates and independent source annotation stay open. This result should neither substitute for human validity review nor justify additional cognitive architecture.
