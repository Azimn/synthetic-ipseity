# v0.9.9 — Reference-host First-Person Experiential Boundary gate

**Date:** 2026-10-11  
**Scope:** Runnable end-to-end engineering conformance in the trusted reference host; **not yet** a whole-platform security guarantee or demonstrated advantage in artificial-character cognition.  
**Relationship:** Implements a high-priority negative-control item from [The First-Person Experiential Boundary](FIRST_PERSON_EXPERIENTIAL_BOUNDARY.md) without adding another cognitive organ.

## What has to be finished before v1.0

The core organ, source-provenance distinctions, Palinode, durable SQLite outbox and subject-only renderer already exist. The missing integration-level requirement is showing that they produce the same renderer input when *only hidden private host details* change.

The reference-host experiment makes that check executable rather than rhetorical:

1. Record **legitimately acquired** instrument text (“8 degrees”), a spoken claim attributed to Henry, and a reconstructed account that must not become autobiographical lived memory.
2. In the same host tick stream, insert **unacquired** secret tool results, **unattested** commands pretending to be SYSTEM instructions, secret engineer source references, unacquired body-score changes, and optionally another high-salience hidden world event.
3. Commit organ progression and admitted subject-only frames in the real SQLite host, then **close the process's host object**.
4. Reopen the same durable database as that subject and deliver subject-only outbox frames through the existing renderer callback. Different callbacks impersonate different renderer model families, but receive exactly one admitted text argument.
5. Compare model input strings **byte for byte** over independently constructed world states. The hidden values vary, including source IDs, numerical values and count of unobserved events; the authorized acquired text and witness wording do not change.
6. Require the same renderer text and no private canary despite different committed event cursor positions and model response strings. A tick with no admitted signal must not create an artificial inner monologue.
7. Confirm positive controls: observed numbers are **not** censored, heard claims remain heard claims, and reconstructed accounts are **not** lived memories. A system that blocks all speech would fail.
8. Inject separate bad subject IDs, untrusted text formatted as directives, and rendering crashes. Ensure bad events cannot commit or leak and leased first-person output remains recoverable after expiry.

The driver is [tools/fpeb_integration_gate.py](../tools/fpeb_integration_gate.py). The test suite is [tests/test_fpeb_integration.py](../tests/test_fpeb_integration.py). No model runtime, Hugging Face download, remote API or background scheduler is involved.

## Reproduction

    python -m pip install -e .
    python tools/fpeb_integration_gate.py --cases 32 --out /tmp/ipseity-fpeb-reference.json
    python -m unittest discover -s tests -p 'test_fpeb_integration.py' -v

The default trial has one reference execution and **32 independently varied private-state executions**, each with three process ticks, one true restart and two actual renderer callback deliveries. Every differential trial must match the reference's admitted subject text **exactly**. The result file reports non-sensitive frame digests and passed negative/positive controls, never the private canary itself. Deterministic RNG seed is pinned for reproducibility.

The GitHub contract suite runs this gate independently on Python 3.11, 3.12 and 3.13. Failures cause nonzero exit and should block merging; the report is not labeled a real-LLM behavior experiment.

## What would count as a failure?

- Any hidden tool value, private reference, debug-derived fact, unobserved numeric diagnostic or non-acquired event appears in renderer input.
- More than the two authorized admitted frames reach the renderer, including for empty ticks.
- Changes in source ID or unperceived world state alter the renderer text despite equal authorized exposure.
- An extra hidden event does **not** advance the authoritative cursor, or advances subject awareness without acquisition.
- Crash/restart changes subject wording, loses already committed frames or treats reconstructed source accounts as firsthand experience.
- An unauthorized cross-subject event commits or produces an output.
- A successful test is achieved only by discarding legitimate visual numerical readings or spoken claims.

## Remaining important limitations

This is a **local conformance check**: the renderer callback only receives the subject-only text through the trusted SubjectOnlyRendererPort. Other code in the same Python process could simply call a different model API, access its own database or capture logs. A malicious compromised host is not sandboxed. The device may contain unrelated data, and this code has no authority over how an arbitrary real agent connects Ollama, external memories or action tools. A real integration must enumerate and constrain all model ingress routes before claiming *whole-host* no-bypass.

It also tests an **identical authorized exposure tape**, not equal but differently worded semantic inputs. It is not a blinded action-level C-vs-D comparison; the fake renderers make canned decisions and demonstrate no psychological competence or evidence of consciousness.

It does not validate source trust itself: host attestations remain privileged assertions. No sensory provenance is cryptographically proven. Quote-formatted hostile text can still induce a downstream model prompt-injection mistake; the reference test proves only that an unread **unattested** hostile instruction is denied and that an honestly observed hostile phrase stays attributed as content.

Finally, persistence currently guarantees committed subject frames plus cursor integrity and at-least-once renderer delivery; it **does not** guarantee exactly-once model effects or later remembered experience.

## Engineering versus scientific completion

- **Engineering completion to pursue:** reference-path access control; durable host semantics; first-person-only ingress; source/recollection distinctions; differential hidden-state invariance; hostile input and source scope; predictable failure handling; one genuinely deployable adapter with audited prompt/tool/action ingress.
- **Still scientific research:** whether this gate improves real memory or character decisions over information-matched first-person prompting; genuine natural-language source comprehension; independent human annotation; multiple renderer families and swap; successful authorized experience retention.
- **Not a claim:** synthetic sentience, conscious inner life, universal no-bypass proof, first-in-field priority.

**Release recommendation:** keep v1.0 gated until at least one real host integration has no unmanaged model input path and there is a reproducible end-to-end demonstration under actual renderer swap. Do not wait for a statistically positive consciousness/behavior claim to describe the reference library as engineering-capable, but do not market it as an empirically validated cognitive breakthrough.
