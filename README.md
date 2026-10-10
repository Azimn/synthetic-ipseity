# Synthetic Ipseity

An independent, character-agnostic research component for **first-person subject access** in artificial characters.

**Status:** v0.3 standalone durability candidate. The deterministic organ and v0.1 API remain supported; behavioral efficacy is unvalidated. The v0.1 API remains compatible. The proposed behavioral-continuity benefit remains unvalidated. Not a consciousness model, not a full artificial organism, and not yet a validated behavioral-continuity improvement.

## The governing rule

> An implementation may compute with numerical, symbolic, neural, relational, and database state. A character must not be granted direct introspective access to that state. Every datum admitted to its subject-facing workspace must arrive as a situated first-person experience, with epistemic limits preserved.

Synthetic Ipseity is an **interface organ**, not the identity, renderer, memory store, attention system, or decision maker. Unconscious mechanisms may still cause actions and tendencies. First-person narration is required **only at subject access**, not at every internal computation. "First person" means situated for the subject, not that every sentence must begin with "I".

## Durable standalone host (v0.3)

The `DurableIpseityHost` reference integration atomically commits the organ's event cursor and subject-only output in SQLite. It can recover after a crash, reject replayed events, and retry unacknowledged first-person output. It does not guarantee exactly-once renderer effects. Its independent default-denied perception boundary and original `Ipseity` APIs remain intact.

```python
from synthetic_ipseity import (
    DurableIpseityHost, Observation, SourceSignal, Channel, Kind,
)

with DurableIpseityHost("character.db", subject_id="character-a", epoch_id="life-a") as host:
    reading = Observation(1, 1, "life-a", Channel.BODY,
        SourceSignal("character-a", Kind.COLD, 0.9, acquired=True),
        attested=True)  # the host must actually establish this access
    host.process(1, [reading])
    lease = host.claim_next(now_ms=1000)
    if lease is not None:
        subject_text = host.read_subject_text(lease)
        print(subject_text)  # I feel deeply chilled.
        host.ack_delivery(lease)
```

See [durable host contract](docs/DURABLE_HOST_V0_3.md) for crash recovery, FIFO leases, host authority, transaction limits, and the exactly-once limitation. Use `python tools/durable_diagnostic.py` for an offline crash/restart demonstration.

## Complete organ API (v0.2)

The v0.2 `SyntheticIpseityOrgan` gives a single character and continuity epoch a typed host ingress, default-denied attestation, a monotonically sequenced observation log, limited access arbitration, immutable subject-facing text, separate engineer audit, checksummed restart cursor, and an optional non-mutating preview/commit workflow.

```python
from synthetic_ipseity import (
    Channel, Kind, Observation, SourceSignal,
    SyntheticIpseityOrgan, render_frame,
)

organ = SyntheticIpseityOrgan("subject-1", epoch_id="life-1")
observation = Observation(
    sequence=1, tick=1, epoch_id="life-1", channel=Channel.BODY,
    signal=SourceSignal(
        "subject-1", Kind.COLD, 0.9,
        source_ref="private-body-state", acquired=True,
    ),
    attested=True,  # trusted host adapter only
)
pending = organ.preview(1, [observation])
# Persist pending.next_checkpoint and the source cursor durably, together.
output = organ.commit(pending)
print(render_frame(output.frame))  # "I feel deeply chilled."
# Never pass output.audit, output.receipts, or the checkpoint to a renderer.
```

See [Organ v0.2 integration contract](docs/ORGAN_V0_2_INTEGRATION.md) for the trust model, typed source channels, restart, transactional responsibilities, security limitations, and downstream adoption gates. The v0.1 `Ipseity.process` API remains available for existing consumers. `tools/organ_diagnostic.py` exercises the new end-to-end path without an LLM.

## Separation of authority

```text
authoritative world / body / memory / cognition / tool state
                         |
                         v
               host-certified source
                         |
                         v
          synthetic ipseity projection
                         |
                         v
                 access arbitration
                         |
            +------------+-------------+
            |                          |
     not admitted                 admitted
    (latent/hidden)              SubjectFrame
            |                          |
    engineer audit only          renderer/cognition
                                       |
                                action/expression
```

The subject-facing `SubjectFrame` contains only natural-language experience. The engineer-facing `AuditEnvelope` separately holds diagnostic source values and decisions. **Never serialize the audit envelope into a renderer prompt.** In v0.2, the standalone organ also requires an independent host `attested=True` claim on the typed observation. Untrusted payloads must never set either flag. Host attestations are trusted inputs. They are not cryptographically verified, and the library does not police arbitrary external renderer calls.

## What this repository owns

The **mechanism and its measurements**: typed source ingress, restricted projection, bounded access, subject-scoped frames, audit isolation, negative controls, and a diagnostic test battery. It does not own the autobiography, subjective preferences, recurrent network, agent policy, world simulation, or any individual's memory.

Pretorius is a downstream integration case, **not an architectural dependency**. The existing DUCK SubjectAccessFirewall and The Doctor Lives Universal Phenomenal-Projection Boundary (UPPB) are documented donors; this repository does not silently replace or claim to vendor either one.

## Install and test

Python 3.11+ with the standard library only:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/diagnose.py
python tools/organ_diagnostic.py
python tools/durable_diagnostic.py
```

## Minimal example

```python
from synthetic_ipseity import Ipseity, Kind, SourceSignal, render_frame

organ = Ipseity(capacity=3)
result = organ.process("subject-a", [
    SourceSignal("subject-a", Kind.COLD, 0.8, source_ref="body:1", acquired=True),
    SourceSignal("subject-a", Kind.INSTRUMENT, "61 degrees", source_ref="thermometer:1", acquired=True),
])
print(render_frame(result.frame))
# I feel deeply chilled.
# I can read the instrument: "61 degrees".
# result.audit remains engineer-only
```

See [research contract](docs/RESEARCH_CONTRACT.md), [experimental protocol](docs/EXPERIMENT_PROTOCOL.md), and [donor crosswalk](docs/DONOR_CROSSWALK.md).

## Evidence boundary

The included tests establish **local software contract behavior** for this reference implementation, including the v0.2 event cursor and transactional preview/commit path. They do not establish subjective consciousness, human-likeness, improved character continuity, or a complete no-bypass guarantee in any host application. Those are separate experimental and integration claims requiring adversarial tests and longitudinal controls.

## Release policy

Keep upstream Pretorius behavior unchanged until an explicit opt-in adapter and integration tests are proposed and reviewed. No back-propagation or shared-memory migration is authorized by this scaffold. Semantic versioning and versioned schemas are required before cross-project adoption.
