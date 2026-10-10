# Palinode v0.8: The Second-Thought Gate

Palinode is a literary term for retracting or reconsidering an earlier position. In Synthetic Ipseity, it is an opt-in **metacognitive access mechanism**, not another complete cognitive architecture.

The canonical v0.7 epistemic ledger can record a revised working belief without producing an inner monologue. Palinode adds two separately attested opportunities: **NOTICE**, in which a character may become aware their view changed, and **RECALL**, in which a character may remember having noticed a change of mind at an earlier tick.

A belief revision alone does not create either event. NOTICE requires a previously committed revision from a nonempty earlier position. It passes the organ's usual acquisition, host attestation, attention threshold and capacity gates. RECALL requires the earlier NOTICE to have been admitted AND its durable subject-only outbox frame acknowledged as delivered. Merely recording a proposed reflection or calling a model that fails is insufficient.

**Delivery acknowledgement is an engineering proxy for exposure, not evidence of consciousness or successful psychological memory encoding.**

## Interface

PalinodeHost inherits from the already merged LongitudinalEpistemicHost. It reuses that canonical source and belief history, plus the v0.3 outbox and v0.4 renderer. Its only new durable tables are palinode_meta and palinode_tickets; neither table duplicates world or autobiography.

Every ReflectionRequest identifies the subject, continuity epoch, an existing revision ID, mode, acquisition and attestation flags and bounded salience. The topic is loaded from the source ledger. Protected revision IDs, salience, source names and belief revision reasons cannot enter the first-person projector. A working belief revision is **never** automatically converted into a subject memory.

When a reconsideration results in SUSPENDS, the admitted first-person notice says:

> I realize I am no longer certain about "the western door". I had thought otherwise before.

Only a later attested, acquired recall following acknowledged NOTICE can say:

> I can recall having noticed my change of mind about "the western door". That memory does not settle the facts.

The latter describes a **record of model-facing exposure**, not proof of true phenomenal recollection. No attempt is made to adjudicate world truth or to overwrite the original belief history.

## Reference integration

~~~python
from synthetic_ipseity import (
    AccessPolicy, DurableIpseityHost, PalinodeHost,
    ReflectionMode, ReflectionRequest, SubjectOnlyRendererPort,
)

policy = AccessPolicy(capacity=5)

# Assume an earlier host transaction made two provisional positions
# for the same evidence claim, with a genuine change of view.
with PalinodeHost("subject.db", subject_id="subject", epoch_id="life-1",
                  policy=policy) as host:
    revision_id = host.reconsideration_ids("door")[-1]
    host.process_reflections(3, [
        ReflectionRequest("subject", "life-1", revision_id,
                          ReflectionMode.NOTICE, acquired=True, attested=True)
    ])

# The established renderer reference path uses a concrete durable host
# and passes the model only derived first-person text.
with DurableIpseityHost("subject.db", subject_id="subject",
                        epoch_id="life-1", policy=policy) as safe:
    port = SubjectOnlyRendererPort(safe, lambda context: "I will investigate.")
    while safe.pending_count():
        port.deliver_next(now_ms=1000)

# A later cognition/memory adapter may attest a recall event.
with PalinodeHost("subject.db", subject_id="subject", epoch_id="life-1",
                  policy=policy) as host:
    assert host.reflection_status(revision_id).notice_delivered
    host.process_reflections(4, [
        ReflectionRequest("subject", "life-1", revision_id,
                          ReflectionMode.RECALL, acquired=True, attested=True)
    ])
~~~

A proposed reflection that is hidden, unattested, not acquired, crowded out by salience, or below threshold consumes an event sequence but produces NO admitted ticket and is not retrospectively remembered. A renderer exception means the frame remains pending for retry and does not enable RECALL. Every revision may generate at most one admitted notice and one admitted recall per lifetime; duplicated and foreign-subject identifiers fail closed.

## Durability and integrity

Palinode runs its reflection projection, cursor advance, outbox write and admitted ticket persistence inside one SQLite BEGIN IMMEDIATE transaction. Fault simulation covers after-preview, before-commit and after-commit uncertainty. Following a post-commit uncertain result, the caller must reopen storage and inspect the event cursor and notice ticket instead of replaying the same source sequence. Delivery remains at-least-once.

This is an additive schema; no migration of existing v0.7 source or belief history is required. Existing consumer APIs and the v0.1 compatibility facade remain unchanged. Authoritative memory consolidation, secure renderer wiring and prompt-injection resistance remain responsibilities of downstream hosts. This does not create a full artificial mind.

## Validation and negative claims

Run the standard unittest suite and tools/palinode_diagnostic.py. Independent regression tests cover unavailable or foreign revisions, denied access, capacity suppression, recalled-before-delivered rejection, success/failed rendering, FIFO retry, duplicate event prevention, crash/restart, and separation of source facts, current belief, and experienced reconsideration.

No result of these software tests establishes a psychological continuity benefit, consciousness or authentic subjective memory. Controlled comparisons with matched information, model swaps and honest null reporting are still required. Pretorius and other consumers remain unchanged until an explicit opt-in integration.
