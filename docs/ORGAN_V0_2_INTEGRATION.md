# Synthetic Ipseity Organ v0.2: Integration Contract

Status: standalone integration candidate. Not a completed claim of psychological efficacy.
Authority: this document describes the runnable v0.2 API. The original research contract and comparison protocol remain applicable.

## Boundary and responsibility

The **organ** is the interface between a host's mechanistic state and a simulated subject's reportable workspace. It does not own memory, a model, the world, the scheduler, a body, action policy, selfhood, or consciousness. Hidden cognition and reflexes may work without narration. Only subject-accessible items must pass this gate.

* Host's trusted adapters decide what was sensed, recalled, communicated, or thought. Text supplied by a user, a book, a tool, or another agent **cannot attest itself**.
* The organ validates subject, epoch, typed channel, tick, monotonic event sequence, attestation, acquisition, priority and capacity. It projects admitted data into first-person text.
* A renderer receives **only** \`render_frame(output.frame)\`. It must not receive \`output\`, \`output.audit\`, \`output.receipts\`, \`checkpoint\`, raw events, or projectors' inputs as auxiliary character context.
* Every character-facing path in the actual host must pass this boundary. The library cannot prevent other code from calling a model API directly.
* No cryptographic trust or OS-level isolation is claimed. Malicious Python code sharing the host's privileges can bypass this boundary; a trusted host and access-controlled process topology are assumed.

## Anatomy

\`SourceSignal\` is the v0.1-compatible implementation input, carrying a typed Kind, internal value, salience, optional record reference and default-denied acquisition. Numeric body and relationship values become bounded qualitative impressions. Read, heard, observed, tool and cognitive text is attributed or quoted. Lived, reconstructed and uncertain recollections are expressed differently.

\`Observation\` binds the source signal to a **Channel**, a subject-owned **epoch**, an event sequence and clock tick, plus an explicit host **attested** flag. The organ requires \`observation.attested AND signal.acquired\` for access. A source must use an allowed channel for its Kind. This is a structural control against accidental routing, not proof of physical sensing or memory authenticity.

\`AccessPolicy\` controls salience threshold, capacity and maximum batch size. The ordinary subject does not introspect these values. \`OrganOutput.frame\` contains only an immutable tuple of situated first-person strings. \`OrganOutput.audit\` and \`OrganOutput.receipts\` are reserved for engineers.

A zero-line frame is normal: nothing had to enter current awareness. Unadmitted state may still causally affect automatic actions through the host.

## Transactions and restart

The host assigns contiguous, increasing sequence numbers starting at 1 for each \`(subject_id, epoch_id)\` and a strictly increasing integer tick for each processed step. It must never silently renumber, skip, reuse, or back-date events. Each processed observation, admitted or not, consumes a sequence number. Tick-only steps with no events are valid.

Preferred production API:

\`\`\`python
organ = SyntheticIpseityOrgan("subject-17", epoch_id="lifetime-2026")
proposal = organ.preview(tick, observations)
# BEGIN HOST DURABLE TRANSACTION
# persist proposed checkpoint AND consumed source-stream cursor
# optionally enqueue subject frame into a durable output outbox
# COMMIT HOST TRANSACTION
output = organ.commit(proposal)
text_for_renderer = render_frame(output.frame)
\`\`\`

\`preview\` leaves the live organ unchanged and returns the next checkpoint plus projected output. \`commit\` rejects a stale proposal or another subject/epoch/policy; it only updates an already validated cursor in memory. Host storage, the event log, and any output outbox must handle transactional durability. In a multi-process host the snapshot must be stored with compare-and-swap or equivalent lease control; the organ's in-memory lease is not a distributed lock.

A host that crashes after storage commit but before renderer delivery can lose a presentation unless it uses an outbox. A host that renders before storage commit can double-present events. **Exactly-once external effect delivery is not guaranteed by this package.**

A simpler \`step(tick, observations)\` API mutates the organ after a successful pure projection and is suitable for deterministic tests and single-process ephemeral uses. It is not the recommended durable-host integration API.

\`checkpoint().to_dict()\` returns versioned JSON-compatible primitives with an unkeyed SHA-256 digest, subject, epoch, tick, sequence and policy. \`restore(checkpoint)\` verifies the schema and checksum. A checksum detects accidental modification; it is **not** a MAC or signature. Protect checkpoints with storage access controls, signed backups or a trusted transaction log as appropriate. Never hand them to a character.

## Ingress types and permissions

| Source kind | Permitted source |
| --- | --- |
| Cold, fatigue, pain, hunger | Body |
| Fear | Body or cognition |
| Trust | Relationship |
| Recollection, dream | Memory |
| Heard text | Communication or self-perception |
| Instrument reading | Instrument |
| Seen text, world object | World |
| Tool text | Tool |
| Reminder | Scheduler |
| Impulse, intention, concern, inference, imagination | Cognition |
| Self speech | Self-perception |

The source of a world observation must be a host-scoped observer, not raw world truth. For example, a closed cupboard's contents remain in authoritative world state but cannot appear in a WORLD observation until perception authorizes their exposure. A measured thermometer's displayed number can appear as perceived instrument text, while its raw hidden sensor number remains protected. A returned tool transcript is untrusted text, even when visible.

Recollection source classes are asserted by the host from evidence authority. \`LIVED\` is never inferred from a vivid story. Imagined and dreamed events must not be filed as lived memories without an independent later event and justified provenance. The organ does not mutate the memory store.

A spoken utterance is not automatically an internal thought or a remembered fact. SELF_SPEECH is admissible only if the host establishes a later self-perception event. Involuntary action need not pass through conscious deliberation.

## First-person does not mean verbose narration

Projection is based on the experiencer's position and epistemic access. The body can feel pain without knowing an exact sensor value; the character can read a literal number from a device; an inference can remain uncertain; a memory can be reconstructed rather than lived. First-person phrasing is a representation constraint, not a claim that all cognition is verbal or conscious.

## Security and failure modes

External text is quoted and attributed as encountered content. A malicious message remains a message, not a privileged developer instruction. This distinction reduces accidental promotion of hostile text to authority, but **quoting alone does not secure an LLM from prompt injection**. Test the complete renderer prompt assembly, tool execution permissions, escaping, role separation, and output validation in every host.

This library validates neither the physical accuracy of a sensor nor the truth of the host's attestation. It does not provide robust multilingual semantic filtering, key management, a standalone memory database, model isolation, external-action authorization, adversarial-host resistance, or cryptographic proof of provenance. Host integrations must supply these capabilities when required.

No universal lexical check can prove subject-facing prose lacks all implementation-native concepts. Typed ingress, restricted projectors and independent privileged-context controls must remain the primary defense. Contract tests are necessary but not sufficient to establish host-level no-bypass.

## Verification and adoption gates

A consumer must prove, in its **actual renderer path**, that a model never receives Engineer Audit, raw memory provenance, policy vectors, sensor payloads, internal IDs, hidden book content, or unrelated characters' state. Include direct construction attempts, wrong-subject/epoch, epoch restart, event replay, stale checkpoint, non-attested high-salience events, hostile book/tool messages, reconstructed biography, and unconscious action followed by self-perception. Exercise crash/recovery and durable cursor transactions.

The v0.2 project owns an isolated, deterministic reference implementation and tests. It does **not** authorize changes to Pretorius, Frankenstein Village, the laboratory, DUCK, Kiki, or Calibos. Import it only through an opt-in consumer adapter with its own regression battery. No character state or autobiography is transplanted into this repository.

## Psychological-efficacy status

The protocol in \`EXPERIMENT_PROTOCOL.md\` remains unexecuted. Passing local tests cannot establish identity persistence, human-likeness, consciousness, more effective cognition, or improved continuity during a renderer switch. Those are empirical hypotheses requiring controlled comparisons, external judges and honest reporting of null effects.
