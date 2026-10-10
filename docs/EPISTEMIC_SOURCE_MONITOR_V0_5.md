# Epistemic Source Monitor v0.5

Status: standalone, deterministic source-monitoring adapter integrated into the Synthetic Ipseity subject-access organ. This is an engineering experiment, not evidence of consciousness, psychologically human source monitoring, or a verified semantic truth detector.

## Role within the organ

The v0.4 renderer interface protects what reaches a simulated subject, but it does not fully describe **how the information was acquired**. A character may see a sentence in a book without having witnessed the reported event; may infer an explanation without knowing it; may imagine a scene without having lived it; or may recognize a face without being certain.

The v0.5 `EpistemicSourceMonitor` accepts independently host-attested claims and emits ordinary, typed `Observation` values that enter the same v0.2 subject-access and v0.3 durable-host pipeline. It therefore adds source attribution **inside the existing organ**, with no separate character brain or identity store.

```text
host-authorized observation / archive / testimony / inference
                          |
                          v
              EpistemicSourceMonitor
              |           |
          typed source    engineer receipts
              |
              v
        SyntheticIpseityOrgan
        source + salience gate
              |
              v
       durable subject-only outbox
              |
              v
       SubjectOnlyRendererPort
```

## Evidence versus experience

`EvidenceKind` distinguishes direct observation, heard testimony, read testimony, verified lived recollection, reconstructed accounts, inference, imagination, dreams and recognition.

Each `EpistemicClaim` carries a protected `source_ref`, a subject, optional visible source name, acquisition and attestation flags, and a priority. The host MUST set acquisition and attestation. Book or tool content cannot attest itself. Hidden `source_ref`, claim identifiers and recognition confidence never appear in the output text.

Examples:

| Protected meaning | Character-facing example |
| --- | --- |
| Report from a named speaker | I hear someone say: "Henry says: The door is locked". |
| Read book passage | I can see written words: "The door was locked". |
| Reconstructed autobiography | I have an account of "the old laboratory", but I do not remember living it. |
| Unverified claimed lived memory | I have an uncertain impression of "the old laboratory". |
| Imagined scene | I imagine "a fox by the window"; this is not a memory. |
| Tentative recognition | I wonder whether that might be "Morgan". |
| High-confidence recognition | I feel fairly sure that is "Morgan". |

These strings are illustrative deterministic projectors, not a claim that introspection has been psychologically validated. A narrator may be mistaken. Source **classification** and fact **truth** are separate axes.

## Lived-memory admission

`EvidenceKind.LIVED_RECALL` becomes `MemoryClass.LIVED` only when a trusted host explicitly sets `lived_verified=True`. Otherwise it is **downgraded to uncertain recollection**, and the engineer receipt says `downgraded_unverified_lived`. Archive material always becomes `MemoryClass.RECONSTRUCTED` even when it quotes vivid first-person autobiography. Perceived testimony remains perceived testimony; it cannot become a lived event by repeating the text.

This module does not independently prove that the historical event occurred. The authoritative memory system must establish provenance according to its own admissibility rules. A compromised host can lie about `lived_verified`; the module is not a trustless verifier.

## Recognition uncertainty

Recognition accepts a numeric host confidence value in [0,1], but the subject sees only qualitative terms. Below 0.30 the identity candidate is not disclosed. Scores in [0.30,0.65) yield a possible identification, [0.65,0.90) yield a tentative positive identification, and at least 0.90 yields a qualified strong impression.

The thresholds are **design parameters for reproducible experimentation**, not measured cognitive calibration. Their effect on correctness and confidence must eventually be tested, including false positives, model swaps and unfamiliar faces. Invalid, missing, NaN, infinite or out-of-range confidence fails closed.

## Contradiction detection and its boundary

A host may supply `claim_key`, a human-readable `topic`, and a signed stance of `AFFIRMS` or `DENIES`. The monitor recognizes an **explicit conflict** only if two independently source-referenced claims with opposing stances are actually acquired and host-attested. A duplicate of one source does not count as independent evidence. Unverified lived recollection, dreams, imagination and unsupported inference cannot create this cross-source conflict.

The derived event says, in effect, that conflicting indications have been encountered and no verdict is available. It never silently prefers the first or most confident report or promotes either to canonical world truth. The derived conflict must itself pass awareness capacity and threshold selection. An arbitrary `claim_key` is protected structural bookkeeping and is never shown to the character.

**Important limitation:** this does not perform language-level natural-language inference that two different propositions conflict. The trusted host must supply an aligned claim key, topic and polarity. A wrongly coded key or polarity yields a wrong diagnostic. This limitation is deliberate, visible, and testable.

## Integration example

```python
from synthetic_ipseity import (
    DurableIpseityHost, EpistemicClaim, EpistemicSourceMonitor,
    EvidenceKind, Stance,
)

monitor = EpistemicSourceMonitor()
evidence = [
    EpistemicClaim("person-a", EvidenceKind.HEARD, "The door is locked",
                   "testimony:henry", acquired=True, attested=True,
                   source_name="Henry", claim_key="door-lock",
                   topic="the western door", stance=Stance.AFFIRMS),
    EpistemicClaim("person-a", EvidenceKind.READ, "The door is unlocked",
                   "record:diary", acquired=True, attested=True,
                   source_name="Diary", claim_key="door-lock",
                   topic="the western door", stance=Stance.DENIES),
]
with DurableIpseityHost(
    "subject.db", subject_id="person-a", epoch_id="lifetime-1"
) as host:
    batch = monitor.project(
        subject_id="person-a", epoch_id="lifetime-1", tick=1,
        start_sequence=host.checkpoint().last_sequence + 1,
        claims=evidence,
    )
    host.process(1, batch.observations)  # cursor and subject text commit atomically
    lease = host.claim_next(now_ms=1000)
    if lease is not None:
        text = host.read_subject_text(lease)
        print(text)
        host.ack_delivery(lease)
    # batch.receipts stay engineer-only.
```

The host must use the correct `start_sequence` and process the complete output batch without arbitrarily dropping conflicting sources. A batch that exceeds monitor or host capacity fails rather than silently truncating evidence.

## Evaluation contract

`tests/test_epistemics.py` covers lived/reconstructed separation, false-lived downgrade, tentative and strong recognition, contradicting testimony, duplicated source controls, unattested source controls, hostile book text, deterministic replay, cross-subject input rejection, numeric non-leakage and durable restart. Tests also check that imagined and dreamed content never automatically becomes lived history.

A full v1.0 assessment must additionally test external source truth, longitudinal source-memory error, contradictions across separate ticks and restarts, model-prompt injection, cognitive biases caused by first-person language, and whether better provenance helps behavior in a controlled A/B/C/D comparison. This is an **evidence gate**, not a behavioral benefit claim.

The module makes no changes to Pretorius, DUCK, Frankenstein Village, Kiki, Calibos or any other character repository. Host adoption is opt-in.
