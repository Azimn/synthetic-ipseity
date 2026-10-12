# Trusted subject-projection interoperability v0.9.11

Status: additive, review-gated interface for cognitive hosts that already own a
validated subject-native projection layer. The canonical Synthetic Ipseity
organ remains character-agnostic and has no Pretorius memories or identity.

## Why this exists

A host such as The-Doctor-Lives already represents perceived information as
protected `SubjectFrame` strings. Feeding those through an ordinary
`Kind.RECOLLECTION`, `Kind.WORLD_OBJECT`, or `Kind.TOOL_TEXT` source would
invent another source attribution and change epistemic meaning. A reclassified
reconstructed memory might sound lived; an original thought might sound like
a received tool message. This must not happen.

`Kind.PROJECTED_SUBJECT_EVENT` is accepted only through
`Channel.COGNITION`. Once the trusted host attests acquisition, the organ
preserves the host-projected text byte for byte while still applying independent
attestation, acquisition, capacity, subject/epoch, sequence, tick and durable
checkpoint controls. Engineer-only lineage and source IDs stay in the audit.

**Trust precondition:** Only a trusted, typed host projector, never a user,
language-model answer or raw tool/world payload, can produce this kind of
signal. `SourceSignal` itself cannot prove that it was so produced. The
host MUST enforce type/capability control before setting `attested=True`.
This is not a substitute for semantic projection or an OS security boundary.

Passing raw implementation data by marking it projected violates this
contract. Host security tests must vary hidden state and privileged payloads,
prove renderer callback receives only approved subject text, and verify denial,
cross-subject replay and state recovery. Do not construct this type in a
renderer. Do not feed its engineer receipts back into subject cognition.

## Adoption restrictions

The organ does not own the consuming character's autobiographical store,
neural policy, action authority or renderer identity. Integrating this kind
does not prove self-initiated recall, continuity improvement or consciousness.
The character host retains responsibility for authenticating perceived events.

The original `Kind.RECOLLECTION` semantic projector remains available for
raw trusted source observations not yet projected into subject language. This
new kind is solely for already projected, authorized subject frames.

See The-Doctor-Lives production integration gate for a concrete caller.

## Optional transactional backpressure

`DurableIpseityHost.process(..., require_drained=True)` is a nonbreaking
versioned-host option. When enabled, the host checks for any pending **or
leased** frame in the same `BEGIN IMMEDIATE` transaction as cursor advancement.
It rejects a second publish without mutating the checkpoint or outbox. This
prevents a character session from generating unbounded duplicate prompts while
older first-person experience awaits model delivery.

The historical default remains `require_drained=False` for compatibility.
It does not provide exactly-once inference or atomic coordination with the
character's separate brain database. A crashed renderer may still repeat
delivery when its lease expires. Dedicated tests cover same-process and
competing-process denial, restart, rollback, and legacy behavior.
