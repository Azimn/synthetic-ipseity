# Longitudinal Epistemic Ledger v0.6

Status: opt-in standalone evidence-continuity integration. Does **not** claim autonomous truth discovery, validated autobiographical memory, consciousness, or completed v1.0 host isolation.

## Why a ledger?

v0.5 could compare testimony within a single batch. Real artificial characters may encounter Henry's account on Monday, hear Morgan disagree on Thursday, and see Henry withdraw the account after a restart. This component retains that sequence without editing past experiences or promoting testimony into world truth. It adds a small epistemic bookkeeping layer **inside Synthetic Ipseity**. It does not build another mind or an independent autobiographical database.

The new `LongitudinalEpistemicHost` subclasses the verified durable SQLite reference host. Its `process_evidence(tick, updates)` accepts `EpistemicClaim` and `EvidenceChange`, projects acquired evidence through the v0.5 monitor, computes conservative state transitions, and persists all evidence revisions, the organ cursor and any first-person outbox entry **in one transaction**. The existing v0.1 through v0.5 interfaces remain supported.

## Model of evidence

An eligible active position needs a host-attested, acquired claim with a canonical `claim_key`, stable subject-visible `topic`, stance `AFFIRMS` or `DENIES`, and independent `source_ref`. Recognized evidence kinds: direct observation, speech, reading, reconstructed archive, and specifically host-verified lived recall. Unverified lived recall remains an uncertain experience but is **not** recorded as an eligible proposition. Imagination, dreams, and unverified inference do not become evidence for a factual verdict.

The host chooses claim keys and polarity. The system does **not** semantically infer that arbitrary statements disagree, does not adjudicate which witness is trustworthy, and does not prove an observed assertion true. Source references must correspond to independent evidential origins, not simply new message IDs from the same witness. A single source switching its stance is a revision, not two independent votes. Duplicating the same source never increases independent source count.

The `epistemic_history` table is append-only. Every qualified assertion or correction retains its tick, event sequence, source, claim key, topic, operation, stance, and evidence class. The `epistemic_current` table is a materialized view of the **latest active stance per source per claim key**. `epistemic_topics` binds claim keys to stable labels across time. Engineer-only `status` reports counts and whether conflicting positions remain active. **Neither the ledger nor a one-sided majority is an authoritative truth store.**

## Transitions and first-person access

* When independent active sources first support opposite stances, the derived event says conflicting evidence exists and no verdict is available.
* Subsequent corroborating testimony does not repeatedly emit the same conflict event.
* A previously encountered source may be withdrawn through a separately attested, acquired `EvidenceChange(..., operation=ChangeKind.RETRACT)`. Unknown sources fail closed. History remains unchanged; the current view excludes the withdrawn stance.
* If withdrawing or revising a source ends the conflict, the organ can report that active accounts no longer conflict, **without claiming the surviving report is true**.
* If the same source replaces its previous stance, the organ can report a changed account. It never treats two positions from one source as independent disagreement.
* Unattested or unacquired claims, corrections, and hidden telemetry neither influence active evidence nor enter subject experience.

All derived transition events are typed `Observation` values routed through the same salience, awareness-capacity and subject-only delivery gate. Some transitions may remain unadmitted; the ledger can contain acquired, non-focal evidence. This is not a mandate to narrate every calculation.

## Example

```python
from synthetic_ipseity import (
    LongitudinalEpistemicHost, EpistemicClaim, EvidenceKind, Stance,
    EvidenceChange, ChangeKind, AccessPolicy,
)

with LongitudinalEpistemicHost(
    "subject.db", subject_id="character", epoch_id="life-1",
    policy=AccessPolicy(capacity=8),
) as host:
    host.process_evidence(1, [
        EpistemicClaim(
            "character", EvidenceKind.HEARD, "The door is locked", "henry",
            acquired=True, attested=True, claim_key="door",
            topic="the western door", stance=Stance.AFFIRMS,
        )
    ])
# Restart is harmless; history and cursor have been committed together.
with LongitudinalEpistemicHost(
    "subject.db", subject_id="character", epoch_id="life-1",
    policy=AccessPolicy(capacity=8),
) as host:
    host.process_evidence(2, [
        EpistemicClaim(
            "character", EvidenceKind.READ, "The door is unlocked", "diary",
            acquired=True, attested=True, claim_key="door",
            topic="the western door", stance=Stance.DENIES,
        )
    ])
    assert host.status("door").conflict
    # Source "diary" is explicitly withdrawn, not deleted from history.
    host.process_evidence(3, [
        EvidenceChange(
            "character", "diary", "door", "the western door",
            operation=ChangeKind.RETRACT, acquired=True, attested=True,
        )
    ])
    assert not host.status("door").conflict
    assert host.history_count() == 3
```

For first-person output, drain the inherited committed outbox through `claim_next`, `read_subject_text`, and `ack_delivery`, or an approved renderer adapter. **Never pass LedgerStatus, history rows, topics table, source references, checkpoint, or this host object to the renderer.** Source content is persisted only if it is qualified comparable evidence; the complete raw utterance and engineering audit are not saved in this ledger. The subject-only outbox still stores only admitted experience text.

## Durability and safety

The source host's `BEGIN IMMEDIATE` SQLite transaction protects the append-only history, current source map, organ checkpoint, and subject-only outbox as a unit. A failure after evidence writes but before commit leaves all unchanged. A post-commit crash leaves the history, cursor, and pending subject output recoverable; the caller must query the cursor and drain the outbox instead of replaying a duplicate event. The inherited outbox **does not** guarantee exactly-once model rendering or external actions; lease expiry can cause repeated delivery attempts. Tests cover separate subjects/epochs, restarts, retractions, revisions, batch capacity, rollbacks, and an uncertain post-commit response.

The ledger stores sensitive *provenance metadata* in database tables separate from the renderer outbox. SQLite file access controls and backups remain the host's responsibility. The SHA hashes and schema identifiers are not cryptographic authentication; they do not protect against a malicious database administrator or compromised trusted host. This module remains vulnerable to incorrect host attestation, incorrect claim keys, false source independence, and prompt injection in quoted external material.

The old `DurableIpseityHost.process` is still present for consumers and does not update this evidence ledger. Hosts using longitudinal evidence must route source claims through `process_evidence`; bypassing that method will create gaps in the epistemic record. Production consumers still require end-to-end renderer and tool ingress auditing before claiming a full no-bypass guarantee.

## Verification and next gate

`tests/test_longitudinal.py` checks cross-tick and cross-restart contradictions, duplicate-source independence, retraction and correction history, host failure injections, after-commit replay denial, cross-subject isolation, and frame/source metadata separation. `tools/longitudinal_diagnostic.py` provides a self-contained scenario using only the Python standard library.

Next research gates remain true source identity tracking, contradictory propositions without pre-aligned keys, controlled human/LLM renderer comparisons, source-monitor calibration, and independent end-to-end audit in a real character host. Passing deterministic tests establishes only the narrow software invariant, not behavioral improvement or consciousness.
