# Longitudinal Epistemic Ledger v0.6

Status: deterministic append-only reference implementation with tests. This extends the existing Synthetic Ipseity organ, not a new cognitive architecture. Passing software tests does not establish improved identity continuity or consciousness.

## Distinguish history from provisional belief

The ledger remembers where attested evidence came from across ticks, restarts and renderer changes. It is character agnostic. An acquired witnessed statement and an archival report can disagree without either automatically becoming verified world truth.

The system maintains three distinct planes:

- **Source history:** append-only, host-attested acquired evidence metadata. The database records subject and epoch, tick, event sequence, protected source identifier, source kind, structured claim key and topic, stance, lived verification flag and content digest. It does NOT store raw source text in the ledger. The existing subject-only outbox does contain legitimately perceived first-person content. Digests are not encryption.
- **Working position:** an optional, revisable AFFIRMS, DENIES or SUSPENDS stance selected by host cognition with cited eligible evidence. The working position is an explicitly provisional opinion, not a world fact. Changes append a new revision record and never overwrite prior history.
- **Subject access:** only evidence actually acquired and attested may be projected as first-person experience; a conflict must also clear attention capacity. Neither the metadata ledger nor the revision reason is ever presented as implementation-native context.

## Transaction boundary

The LongitudinalEpistemicHost.process_claims method loads the current durable organ cursor, projects evidence through the existing v0.5 source monitor, adds novel cross-tick conflicts, and validates revisions. It then commits cursor, derived first-person outbox, append-only evidence rows, admitted conflict markers and belief revisions together in ONE SQLite BEGIN IMMEDIATE transaction.

Failed validation, after_preview and before_commit fault simulation roll back the complete transaction. A crash after durable commit leaves the cursor and outbox recoverable; retries must check the cursor and drain unacknowledged outbox frames. External renderer delivery remains at least once, not exactly once.

The additive SQLite schema maintains a dedicated version row and the tables epistemic_evidence, epistemic_conflict_projection and epistemic_revisions. The original durable host API remains backward compatible. However, direct legacy process calls do NOT write epistemic evidence. Consumers that require a complete source history must route relevant claims via process_claims and audit all other access paths.

## Example: belief revision across days

~~~python
from synthetic_ipseity import (
    LongitudinalEpistemicHost, EpistemicClaim,
    EvidenceKind, Stance, BeliefRevision, Position,
)

with LongitudinalEpistemicHost(
    "character.db", subject_id="character-a", epoch_id="life-a",
) as host:
    host.process_claims(1, [
        EpistemicClaim(
            "character-a", EvidenceKind.HEARD, "The western door is locked",
            "henry:1", acquired=True, attested=True,
            source_name="Henry", claim_key="door",
            topic="the western door", stance=Stance.AFFIRMS,
        )
    ], revisions=[
        BeliefRevision("door", Position.AFFIRMS, "first report",
                       ("henry:1",), attested=True)
    ])

    host.process_claims(2, [
        EpistemicClaim(
            "character-a", EvidenceKind.HEARD, "The western door is unlocked",
            "morgan:2", acquired=True, attested=True,
            source_name="Morgan", claim_key="door",
            topic="the western door", stance=Stance.DENIES,
        )
    ], revisions=[
        BeliefRevision("door", Position.SUSPENDS, "reports conflict",
                       ("henry:1", "morgan:2"), attested=True)
    ])

    # Engineer-only status. Do NOT send the object to the renderer.
    state = host.epistemic_state("door")
    assert state.unresolved_conflict
    assert state.provisional_position is Position.SUSPENDS
~~~

A belief revision requires explicit trusted host attestation and at least one existing acquired, attested, eligible source with the same canonical claim key. A positive or negative stance also requires a cited source that supports the selected stance. Unknown or inaccessible evidence, unsupported confidence assertions and duplicate positions fail closed.

The chosen position does not rewrite authoritative world events, lived memory, or past testimony. It also does not automatically generate a private thought or conscious experience; a host wishing to express that inference must create a separately acquired cognitive event. In particular, SUSPENDS leaves earlier conflict evidence untouched.

## Contradiction handling

A contradiction requires two differently source-referenced, attested and acquired assertions with opposing host-coded stances under the same claim key/topic, even if they arrive on separate ticks. One witness contradicting themselves is not independent evidence. Unverified lived recollections, dreams and imagination do not act as verified testimony.

The first noticed conflict is projected as uncertainty, never as an unearned verdict. More identical contradicting material does not repeat the notice forever. If the conflict fails the awareness gate, it remains recorded but can surface at a later relevant source encounter.

This is STRUCTURED source comparison, not independent semantic contradiction detection, fact checking or lie detection. The host supplies keys, topics, polarity and source authenticity. Those labels could be mistaken; this module does not verify their truth.

## Verification and limits

Run python -m unittest discover -s tests -v and python tools/longitudinal_diagnostic.py. Tests must cover persisted cross-tick conflict, audit isolation, reconstruction boundaries, multiple subjects/epochs, source independence, immutable revision trail, failed transactions and uncertain-commit recovery.

The ledger is engineer metadata in a trusted SQLite environment. Its protected source references and topics require storage access controls. The subject-only renderer port consumes the existing durable outbox through the base host. This code does not prevent an untrusted host from bypassing the organ, forge provenance, supply inaccurate attestation, or directly call an LLM with raw state.

No changes are made to Pretorius, DUCK, Frankenstein Village, Kiki or Calibos. The v1.0 completion tracker remains open for whole-host integration audits, adversarial validation, versioned migrations, performance trials and controlled tests of longitudinal character behavior.
