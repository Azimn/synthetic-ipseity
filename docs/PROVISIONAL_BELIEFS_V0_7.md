# Provisional Belief Revisions v0.7

Status: additive, character-agnostic extension of the existing v0.6 LongitudinalEpistemicHost. Do not confuse the character's provisional opinion with verified world truth.

## Why this is distinct from source revision

The v0.6 ledger already records where evidence came from, maintains current source positions, and retains retractions. A source's change of story is **not** the same as a character changing their mind.

v0.7 adds a separate append-only record for the character's *working position*. There are three supported positions:

- AFFIRMS: the character tentatively endorses the proposition on cited, active evidence.
- DENIES: the character tentatively rejects the proposition on cited, active evidence.
- SUSPENDS: the character withholds judgment pending clearer evidence.

The host must explicitly attest a ProvisionalBeliefRevision. No revision is generated automatically because one witness spoke or a confidence score rose. Every revision cites one or more active source references under the same claim key. Affirming or denying must cite at least one still-active source with the corresponding stance. Hidden, unattested, nonacquired, wrong-subject or retracted sources cannot support a new revision.

These are structural evidence eligibility checks, **not** fact checking. An individual can legitimately hold a mistaken provisional view. Contrary accounts can remain active even when the working position is AFFIRMS or DENIES. No source history is overwritten.

## Atomicity and memory separation

The normal LongitudinalEpistemicHost.process_evidence call now takes an optional belief_revisions tuple. The SQLite BEGIN IMMEDIATE transaction that commits evidence history, active source state, subject event cursor and subject-only outbox **also** commits those working-position revisions. If the batch, revision, source provenance or simulated commit fails, everything rolls back. A post-commit uncertain caller response is handled as in v0.6: reopen, check the stored cursor, and drain the outbox.

The belief revision record is engineer-only. It does not automatically become a newly experienced thought, lived memory, world fact, or imperative instruction. If a character becomes consciously aware of their changed view, its host must separately attest and route that introspection through Synthetic Ipseity's ordinary cognitive ingress.

## Example

~~~python
from synthetic_ipseity import (
    BeliefPosition, ProvisionalBeliefRevision,
    LongitudinalEpistemicHost, EpistemicClaim, EvidenceKind, Stance,
)

def heard(source, words, stance):
    return EpistemicClaim(
        "subject-a", EvidenceKind.HEARD, words, source,
        acquired=True, attested=True,
        claim_key="door-lock", topic="the western door",
        stance=stance,
    )

with LongitudinalEpistemicHost(
    "character.db", subject_id="subject-a", epoch_id="life-1",
) as host:
    host.process_evidence(
        1, [heard("henry", "The door is locked", Stance.AFFIRMS)],
        belief_revisions=[
            ProvisionalBeliefRevision(
                "door-lock", BeliefPosition.AFFIRMS,
                "tentative first report", ("henry",), attested=True,
            )
        ],
    )
    host.process_evidence(
        2, [heard("morgan", "The door is unlocked", Stance.DENIES)],
        belief_revisions=[
            ProvisionalBeliefRevision(
                "door-lock", BeliefPosition.SUSPENDS,
                "contradictory independent reports",
                ("henry", "morgan"), attested=True,
            )
        ],
    )
    assert host.status("door-lock").conflict
    assert host.belief_position("door-lock") is BeliefPosition.SUSPENDS
    assert len(host.belief_revisions("door-lock")) == 2
~~~

The two history types remain distinct: the v0.6 epistemic_history is evidence history, and v0.7 epistemic_belief_history is the append-only working-position trace.

## Schema migration policy

v0.7 bumps LEDGER_SCHEMA_VERSION from 1 to 2 and adds an epistemic_belief_history table. When an existing v0.6 database (ledger version 1) is opened through the new LongitudinalEpistemicHost, it creates the new table if absent and atomically upgrades that subject and epoch's metadata version to 2. Existing source history and the world-state cursor remain unchanged.

Unknown future schema versions fail closed. **Back up the SQLite database before upgrading**. The older v0.6 implementation is not guaranteed to reopen a database after the metadata version has advanced. Treat database upgrades as an operational migration and keep a rollback snapshot.

## Remaining negative claims

The library has no independent capacity to determine whether a testimony is true, what the character should believe, or whether a renderer has phenomenal experience. The trusted host still owns epistemic source alignment, explicit authorization, model prompts, action policy and factual world history. The reference renderer may receive only subject-facing outbox text, not BeliefPosition, ProvisionalBeliefRecord, revision reason, source metadata or host objects.

See tests/test_belief_revisions.py for crash faults, subject isolation, incorrect support, retractions, and migration. The earlier v0.6 evidence retraction/correction code is retained, not replaced. Pretorius and other character repositories remain unchanged.
