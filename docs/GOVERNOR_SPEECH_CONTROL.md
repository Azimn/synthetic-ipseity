# Self-Reference Governor: host-neutral controlled speech v0.1

**Experimental on draft PR #34. Do not merge as production-ready.**

This is one reusable renderer-side component. It does not set speaker identity, select cognitive intentions, retrieve memories or establish evidence. A host supplies `ReferenceBindings` and `ReferenceContext` from trusted authority, then hands an **admitted first-person SubjectFrame string** to the controller. Trusted renderer instructions use an independent configuration lane, not a subject memory.

## Supported contract

- English (`language="en"`) is the **only** implemented linguistic validation language. Unsupported tags reject at binding time, rather than silently using English patterns.
- The host explicitly chooses `discourse_mode="direct" | "narrated" | "quoted"`, speaker ID, addressee ID, aliases and any rhetorical-self-address license. User or model text cannot override these values.
- `SelfReferenceGovernor.renderer_instruction` states the required perspective positively. `SelfReferenceGovernor.check` reports bounded lexical violation IDs for unlicensed self-vocative, in-clause self-name, third-person self narration and known renderer meta-boundary markers.
- `GovernedSpeechControl` runs one model proposal, a second repair proposal **only if needed**, then an optional exact **host-authored** and prevalidated fallback. Both model attempts receive precisely the same admitted first-person text; only trusted renderer instructions differ. A rejected candidate is never re-admitted as experience.
- `SpeechControlReceipt` stores immutable SHA-256 digests, attempt outcomes and violation rule IDs. No raw source frame, speech or secret identity material is placed into the receipt.
- If no attempt or trusted fallback passes, raise `SpeechControlRejected`; a durable `SubjectOnlyRendererPort` must leave its outbox unacknowledged. Successful fallback is a new **authorized speech choice** by the host, not evidence the LLM solved the dialogue problem.
- The standard `LocalOllamaConfiguredRenderer(model)` uses only `127.0.0.1:11434`; `prompt` contains the admitted first-person experience, `system` contains trusted instruction, with no hidden telemetry or memory.

## Host-neutral example

```python
from synthetic_ipseity.self_reference import ReferenceBindings, ReferenceContext
from synthetic_ipseity.speech_control import GovernedSpeechControl
from synthetic_ipseity.local_ollama import LocalOllamaConfiguredRenderer

# Only a TRUSTED host creates these objects. Never infer from chat output.
subject = ReferenceBindings(
    subject_id="subject-a",
    canonical_name="Subject A",
    aliases=("Subject A",),
)
context = ReferenceContext(
    speaker_subject_id="subject-a",
    addressee_subject_id="visitor",
    discourse_mode="direct",
    language="en",
)
render = GovernedSpeechControl(
    bindings=subject,
    context=context,
    trusted_instruction="Answer the visitor in your own words.",
    generate=LocalOllamaConfiguredRenderer("qwen2.5:0.5b"),
    fallback_text="I must consider my words more carefully.",
    max_model_attempts=2,
)
# 'I recall...' must have already crossed the host's subject-access boundary.
speech = render("I recall a disagreement in the laboratory.")
# Inspect render.receipts ONLY as engineer telemetry, never as subject data.
```

## Explicit limitations

This is **not universal speech comprehension or grounding**. The lexical English rules have known blind spots involving ambiguity, quoted or nested language, complex coreference, pronoun substitution and creative syntax. A candidate passing the governor is not proven factually correct or natural. For direct speech, the *controlled port* defaults to rejecting outputs with no visible first-person anchor, even though this may reject legitimate terse responses (for example, "Certainly."). This conservative trade-off must be evaluated with blind human judges before release.

The host-owned fallback cannot automatically preserve arbitrary selected facts. To provide fact-bearing fallbacks, the host must build and separately validate protected constructions using its own typed, provenance-bearing evidence, rather than allowing the language model or governor to choose missing values.

Standalone contract suite `tests/test_self_reference.py`, `tests/test_speech_control.py` and `tests/test_local_ollama.py` tests three independent identity bindings (Calibos, Kiki, Pretorius), narrated/quoted controls, repair, fallback and failure behavior, without depending on those hosts' repositories. Pretorius is the **only genuine three-organ integration host currently exercised**, on separate Doctor Lives PR #60. Calibos/Kiki tests use synthetic host bindings, not a claim of full production integrations.

## Next release gates

1. Freeze versioned host binding schema and validate the authoritative issuer, not merely the Python type.
2. Require all supported renderer delivery paths to pass the governor; private trusted Python callback code can still bypass it.
3. Expand blind false-positive/false-negative corpora across person, tense, dialogue mode, naming ambiguity and legitimate short replies.
4. Validate native multilingual plugins independently; do not treat `language="es"` as supported until it has a verified checker.
5. Blind-judge conversational naturalness and groundedness on held-out dialogues with real model swapping.
6. Verify crash recovery, fallback ACK semantics and engineer receipts under hard-process interruption.
