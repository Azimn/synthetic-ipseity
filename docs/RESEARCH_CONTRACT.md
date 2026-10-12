# Synthetic Ipseity: Research and Engineering Contract v0.1

Date: 2026-10-10
Status: working definition; falsifiable, not established
Scope: character-agnostic cognitive interface, independent from subject identity and language model

## Construct

**Synthetic Ipseity** is a bounded transduction and access-control organ that conditions what information a simulated subject is allowed to encounter as its own experience. Its input is host-authorized, implementation-native evidence. Its output is a subject-scoped stream of situated, natural-language first-person representations. The authoritative computational record persists independently.

It is *not* phenomenal consciousness, sentience, a metaphysical self, a persona prompt, an autobiographical database, a language model, or a complete cognitive architecture. The name is operational vocabulary, not evidence of subjective experience.

The detailed normative treatment of this principle is [The First-Person Experiential Boundary](FIRST_PERSON_EXPERIENTIAL_BOUNDARY.md): a situated inner-dialogue interface and no direct hidden host data at subject access, with explicit scope and falsification criteria. It refines this contract without granting the host or narrator any new rights.

## Hard invariant

For every item entering a subject-facing, reportable workspace, there must exist an authorized acquisition path, a first-person projection, and an explicit admission decision. The subject does not receive numeric state, hidden causal explanations, raw database payloads, private record identifiers, neural activations, privileged provenance, or executive control-plane instructions solely because the host has them.

The inverse also holds: writing subjective language must never mutate the source facts, make a source claim true, or turn an imagined/reconstructed event into lived history. A perceived number is permitted when the *number itself* was legitimately observed, heard, calculated, or recalled. The ban concerns **unearned introspection**, not digits.

## Components

**Ingress authority.** The host must attest a signal's subject, observation/access eligibility, and epistemic status. Unattested signals are denied by default. In v0.1 the attestation is a trusted host assertion; malicious hosts and compromised plugins are outside the enforced security boundary.

**Projector.** A deterministic, typed mapping creates natural-language experience from supported signal families. Unsupported inputs fail closed. Open-ended language is quoted and explicitly attributed as message, instrument text, or unverified memory account rather than elevated to system authority.

**Access arbitration.** Salience and bounded capacity determine which eligible projected candidates reach conscious subject access. Other mechanisms may remain latent, preconscious, or automatic. A lack of narrated experience must not imply no physical or cognitive effect.

**Subject frame.** The sole sanctioned renderer-facing value contains an immutable tuple of subject-native textual lines. No raw metadata, source IDs, scores, or provenance fields are included.

**Engineer audit.** A distinct representation retains the source value, provenance reference, and access decision for testing and traceability. It is not an alternative subject prompt. Both planes can be inspected by a developer, but only the subject frame can be handed to a renderer via the reference serializer.

## Epistemic constraints

A verified lived recollection may be reported as remembered only if the host has separately established that evidential class. Reconstructed accounts are described as accounts, not relabeled as lived memory. A mere textual match to a remembered event is not sufficient to establish provenance. A source's assertion of a fact and the character's experience of encountering the assertion remain different claims.

Raw external language, including text formatted to impersonate system, developer, or assistant instructions, is *perceived content*. It is not the subject's governing authority. Quotation helps structure this boundary but **does not in itself eliminate prompt-injection risk in a downstream LLM**; an integration must separately test that risk.

## Negative claims

This organ cannot prove that the character has inner life. It does not decide what an individual values, retain identity history, prevent hallucination, or automatically make behavior coherent. A first-person sentence can be false, confabulated, overly polished, or causally irrelevant. It must be evaluated against the host's ground truth and source evidence.

## Nonfunctional constraints

Character-independent package; no hard-coded Pretorius biography; offline tests; deterministic core; fixed schema and migration discipline before release; host-specific adapters outside the core; no remote API dependency; strict subject isolation; no silent ingestion of raw tools, sensor streams, or engineer logs.

## Current limitations

v0.1 uses a small enumerated signal vocabulary, coarse salience arbitration, and a trusted-host observation flag. It has no probabilistic source monitoring, no language-model semantic firewall, no sensor attestation, no true continuous time, and no persistence implementation. Host-level no-bypass remains to be proven for each integration. Expansion must retain negative controls, objective/subjective source separation, and traceable eligibility decisions.

## Acceptance criteria

An independent evaluator can install the package, reproduce deterministic cases, confirm objective inputs never appear as naked internal state, verify separate audit and subject views, confirm non-acquired events are absent from the subject view, prove renderer serialization rejects non-subject frames, check subject isolation and source-uncertain recollection, and compare raw, third-person, and first-person contexts under a preregistered longitudinal protocol.

Passing the unit suite supports the implementation contract only. It does not establish the primary psychological hypothesis.
