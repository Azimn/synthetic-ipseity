# Durable Reference Host v0.3

Status: working standalone SQLite reference host. This milestone addresses the first durability gate in Issue #8, subject to the reproducible tests and CI results. It does not claim psychological validity, a cryptographic trust boundary, or exactly-once external effects.

## Why it exists

The v0.2 organ can prepare a subject-native frame and next checkpoint, but the calling program must atomically persist progress and output. A process crash between those operations could leave character experience inconsistent with the recorded event cursor. The v0.3 reference host owns those two operations as one SQLite transaction.

The host remains strictly character-agnostic. There is no Pretorius-specific memory, personality, motive, or world state in its database schema or API.

## Minimal application

```python
from synthetic_ipseity import (
    DurableIpseityHost, Channel, Kind, Observation, SourceSignal,
)

with DurableIpseityHost("subject.db", subject_id="subject-a", epoch_id="life-1") as host:
    observed = Observation(
        sequence=1, tick=1, epoch_id="life-1", channel=Channel.BODY,
        signal=SourceSignal(
            "subject-a", Kind.COLD, 0.84,
            source_ref="engineer-only-body-reading", acquired=True,
        ),
        attested=True,  # set ONLY by a trusted perception adapter
    )
    receipt = host.process(1, [observed])
    # If the process crashes here, both the cursor and first-person
    # output have already committed to SQLite.
    lease = host.claim_next(now_ms=1_000_000)
    if lease is not None:
        subject_text = host.read_subject_text(lease)
        # Pass subject_text to the character renderer, not the host or
        # the audit/checkpoint data. Record external idempotency separately.
        print(subject_text)
        host.ack_delivery(lease)  # only after successful rendering
```

No remote provider, agent shell, model subscription, or external storage library is needed. Python standard library SQLite supplies transactions.

## Persistence guarantee and limits

`host.process(tick, observations)` begins a write transaction and reloads the currently committed organ checkpoint. It runs v0.2 `preview`, atomically writes the next checkpoint and any admitted first-person frame into the FIFO outbox, then commits before returning. A failed validation or crash before commit leaves neither cursor nor outbox advanced. A crash after commit leaves both advanced, and the outbox remains available after restart. Empty frames advance the cursor without creating a spurious renderer message.

The SQLite settings enable WAL, foreign keys, busy timeout and `synchronous=FULL`. A single database file hosts separate subject and epoch namespaces. Writers serialize through `BEGIN IMMEDIATE`, reload current state and reject stale or duplicate source sequences. Each event sequence is contiguous and starts at 1 in an epoch. Input source events must come from an independently durable, replayable upstream feed: this host intentionally **does not** persist original raw tool responses, biographies, body telemetry, or engineer audit payloads.

The outbox stores only derived first-person lines and an integrity checksum. Oldest undelivered content must be acknowledged before the next frame can be leased. A lease can expire and its frame may be issued again. The exact delivery semantics are **at least once after lease expiry**, assuming a functioning worker repeatedly polls and acknowledges the queue. Rendering, speech, messages, or physical actions can be duplicated following a crash after an effect but before acknowledgement. Consumers must use an idempotency key derived from `DeliveryLease.outbox_id` or their own durable effects ledger if they need stronger downstream guarantees. The host is not an exactly-once messaging system.

A `DeliveryLease` holds an opaque random token and an outbox ID. `read_subject_text(lease)` is the reference renderer handoff; it validates the subject, epoch, token, lease status and stored content hash. `ack_delivery(lease)` invalidates that token and marks its message delivered. A new lease supersedes an expired token. The host cannot prevent arbitrary external code from issuing a model request that bypasses this function. Trusted host wiring and renderer permission separation remain independent integration requirements.

The SHA-256 frame checksum and v0.2 checkpoint digest detect accidental corruption, not attacker-controlled forgery. Local SQLite storage is not a cryptographic security boundary. Do not store sensitive source content in raw form outside the separate host environment without deliberate privacy design. Production services must add backups, operational monitoring, safe migrations, upstream replay, external-action authorization and a protected renderer topology.

## Crash matrix

| Failure point | Durable cursor | Outbox | Safe next action |
| --- | --- | --- | --- |
| Input stream fails before transaction | Unchanged | Unchanged | Replay same source |
| After projection, before writes | Unchanged | Unchanged | Replay same source |
| After SQL writes but before COMMIT | Rolled back | Rolled back | Replay same source |
| After COMMIT but before response | Advanced | Present if nonempty | Read cursor and drain outbox |
| After lease claim, before render | Advanced | Leased until expiry | Redeliver after lease expires |
| After render, before acknowledgement | Advanced | Leased until expiry | Redeliver; consumer must deduplicate side effects |
| After acknowledgement | Advanced | Delivered | Continue with next queued frame |

The `fault` parameter to `process` is a diagnostic switch, not a production API for simulating arbitrary power failures. The tests cover restart and observable transaction boundaries; they do not emulate filesystem corruption, OS process termination during an fsync, hardware power failures, or adversarial database rewrites.

## Host-authority obligations

The `Observation.attested` flag must originate with a trusted adapter and never be populated from incoming world text. The `SourceSignal.acquired` flag must correspond to evidence of the character actually gaining access. A database administrator or trusted host process can still forge information; this API cannot verify physical perception independently. Strict first-person wording does not stop an LLM obeying malicious instructions embedded in quoted world text. Production renderer integrations need separate prompt-injection and role-isolation tests.

## Validation

Run `python -m unittest discover -s tests -v` and `python tools/durable_diagnostic.py`. The durable tests cover atomic rollback, uncertain commit recovery, duplicate sequence rejection after restart, multiple writers, multiple subjects and epochs, FIFO delivery, expiry, invalid leases, corrupted outbox/checkpoint detection, a control-like book sentence and unadmitted high-salience data.

The independent psychological A/B/C/D protocol is unchanged. A tested persistence implementation does not show that the organ improves identity continuity or creates conscious awareness.
