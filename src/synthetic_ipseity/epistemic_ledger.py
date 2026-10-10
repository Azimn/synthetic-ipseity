"""Append-only, longitudinal epistemic ledger sharing the durable organ transaction.

A working stance is a revisable, host-attested cognitive commitment, NOT a
world-truth claim. Source observations and belief revisions remain engineer
metadata; only access-admitted first-person projections reach the outbox.

No automatic truth arbitration, language understanding, or hostile-host
security guarantee is provided.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .core import Kind, SourceSignal
from .durable_host import CommitReceipt, DurableIpseityHost, _digest, _json
from .epistemics import (
    EpistemicClaim, EpistemicSourceMonitor, EvidenceKind, Stance, _label,
)
from .organ import AccessPolicy, Channel, Observation, SyntheticIpseityOrgan


LEDGER_SCHEMA_VERSION = 1
_CONTRASTABLE = frozenset({
    EvidenceKind.OBSERVED, EvidenceKind.HEARD, EvidenceKind.READ,
    EvidenceKind.RECONSTRUCTED, EvidenceKind.LIVED_RECALL,
})


class Position(str, Enum):
    AFFIRMS = "affirms"
    DENIES = "denies"
    SUSPENDS = "suspends"


@dataclass(frozen=True)
class BeliefRevision:
    """Explicit host-authorized revision, supported by recorded evidence.

    'reason' and basis references are engineer-only; they do not enter
    subject context or assert that any position is true.
    """

    claim_key: str
    position: Position
    reason: str
    basis_sources: tuple[str, ...]
    attested: bool = False

    def __post_init__(self) -> None:
        _label(self.claim_key, "claim_key")
        _label(self.reason, "revision reason", limit=1000)
        if type(self.position) is not Position:
            raise TypeError("position must be Position")
        if type(self.attested) is not bool:
            raise TypeError("revision attested must be bool")
        if type(self.basis_sources) is not tuple or not self.basis_sources:
            raise ValueError("revision requires at least one evidence source")
        if len(self.basis_sources) > 32 or len(set(self.basis_sources)) != len(self.basis_sources):
            raise ValueError("duplicate or excessive revision evidence sources")
        for source in self.basis_sources:
            _label(source, "basis source")


@dataclass(frozen=True)
class BeliefRevisionRecord:
    """Engineer-only append-only trace."""

    tick: int
    claim_key: str
    previous: Position | None
    current: Position
    reason: str
    basis_sources: tuple[str, ...]


@dataclass(frozen=True)
class EpistemicState:
    """Engineer-only derived ledger view; not a renderer frame."""

    claim_key: str
    topic: str
    affirming_sources: tuple[str, ...]
    denying_sources: tuple[str, ...]
    unresolved_conflict: bool
    conflict_projected: bool
    provisional_position: Position | None
    revision_count: int


def _eligible(claim: EpistemicClaim) -> bool:
    return (
        claim.attested and claim.acquired
        and claim.claim_key is not None
        and claim.kind in _CONTRASTABLE
        and (claim.kind is not EvidenceKind.LIVED_RECALL or claim.lived_verified)
    )


class LongitudinalEpistemicHost(DurableIpseityHost):
    """SQLite organ host with an append-only evidence and revision history.

    process_claims() performs source projection, prior-history comparison,
    source evidence writes, provisional belief revisions, organ cursor update,
    and subject-only outbox insert in ONE BEGIN IMMEDIATE transaction.

    Ordinary process() remains available for legacy organ inputs but does NOT
    add evidence to the ledger. Consumers requiring a complete source trail
    must submit epistemic evidence through process_claims(), and separately
    audit any direct process() calls.
    """

    def __init__(
        self, db_path: str | Path, *, subject_id: str, epoch_id: str,
        policy: AccessPolicy | None = None,
    ) -> None:
        super().__init__(
            db_path, subject_id=subject_id, epoch_id=epoch_id, policy=policy,
        )
        try:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                statements = (
                    """CREATE TABLE IF NOT EXISTS epistemic_version (
                         version INTEGER NOT NULL
                       )""",
                    """CREATE TABLE IF NOT EXISTS epistemic_evidence (
                         subject_id TEXT NOT NULL,
                         epoch_id TEXT NOT NULL,
                         sequence INTEGER NOT NULL,
                         tick INTEGER NOT NULL,
                         kind TEXT NOT NULL,
                         source_ref TEXT NOT NULL,
                         claim_key TEXT,
                         topic TEXT,
                         stance TEXT,
                         lived_verified INTEGER NOT NULL,
                         content_digest TEXT NOT NULL,
                         PRIMARY KEY(subject_id, epoch_id, sequence),
                         FOREIGN KEY(subject_id, epoch_id)
                           REFERENCES subjects(subject_id, epoch_id)
                       )""",
                    """CREATE INDEX IF NOT EXISTS ix_epistemic_key
                       ON epistemic_evidence(subject_id, epoch_id, claim_key)""",
                    """CREATE TABLE IF NOT EXISTS epistemic_conflict_projection (
                         subject_id TEXT NOT NULL,
                         epoch_id TEXT NOT NULL,
                         claim_key TEXT NOT NULL,
                         topic TEXT NOT NULL,
                         sequence INTEGER NOT NULL,
                         tick INTEGER NOT NULL,
                         PRIMARY KEY(subject_id, epoch_id, claim_key),
                         FOREIGN KEY(subject_id, epoch_id)
                           REFERENCES subjects(subject_id, epoch_id)
                       )""",
                    """CREATE TABLE IF NOT EXISTS epistemic_revisions (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         subject_id TEXT NOT NULL,
                         epoch_id TEXT NOT NULL,
                         tick INTEGER NOT NULL,
                         claim_key TEXT NOT NULL,
                         topic TEXT NOT NULL,
                         previous_position TEXT,
                         new_position TEXT NOT NULL,
                         reason TEXT NOT NULL,
                         basis_sources_json TEXT NOT NULL,
                         FOREIGN KEY(subject_id, epoch_id)
                           REFERENCES subjects(subject_id, epoch_id)
                       )""",
                )
                for statement in statements:
                    self._db.execute(statement)
                self._db.execute(
                    "INSERT INTO epistemic_version(version) "
                    "SELECT ? WHERE NOT EXISTS (SELECT 1 FROM epistemic_version)",
                    (LEDGER_SCHEMA_VERSION,),
                )
                versions = self._db.execute(
                    "SELECT version FROM epistemic_version"
                ).fetchall()
                if versions != [(LEDGER_SCHEMA_VERSION,)]:
                    raise ValueError("unsupported epistemic ledger schema")
                self._db.execute("COMMIT")
            except BaseException:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
                raise
        except BaseException:
            self.close()
            raise

    def _evidence_rows(self, claim_key: str) -> list[tuple[str, str, str]]:
        return self._db.execute(
            "SELECT topic, source_ref, stance FROM epistemic_evidence "
            "WHERE subject_id=? AND epoch_id=? AND claim_key=? AND stance IS NOT NULL "
            "ORDER BY sequence",
            (self.subject_id, self.epoch_id, claim_key),
        ).fetchall()

    def epistemic_state(self, claim_key: str) -> EpistemicState:
        """Protected introspection for engineers; never hand to a renderer."""
        self._ensure_open()
        _label(claim_key, "claim_key")
        rows = self._evidence_rows(claim_key)
        if not rows:
            raise KeyError("no eligible evidence for claim key")
        topics = {row[0] for row in rows}
        if len(topics) != 1:
            raise ValueError("ledger topic mismatch")
        aff = {ref for _, ref, stance in rows if stance == Stance.AFFIRMS.value}
        den = {ref for _, ref, stance in rows if stance == Stance.DENIES.value}
        emitted = self._db.execute(
            "SELECT 1 FROM epistemic_conflict_projection "
            "WHERE subject_id=? AND epoch_id=? AND claim_key=?",
            (self.subject_id, self.epoch_id, claim_key),
        ).fetchone() is not None
        revision_rows = self._db.execute(
            "SELECT new_position FROM epistemic_revisions "
            "WHERE subject_id=? AND epoch_id=? AND claim_key=? ORDER BY id",
            (self.subject_id, self.epoch_id, claim_key),
        ).fetchall()
        return EpistemicState(
            claim_key, next(iter(topics)), tuple(sorted(aff)),
            tuple(sorted(den)), bool(aff and den and len(aff | den) >= 2),
            emitted,
            Position(revision_rows[-1][0]) if revision_rows else None,
            len(revision_rows),
        )

    def revisions(self, claim_key: str) -> tuple[BeliefRevisionRecord, ...]:
        self._ensure_open()
        _label(claim_key, "claim_key")
        rows = self._db.execute(
            "SELECT tick, claim_key, previous_position, new_position, "
            "reason, basis_sources_json FROM epistemic_revisions "
            "WHERE subject_id=? AND epoch_id=? AND claim_key=? ORDER BY id",
            (self.subject_id, self.epoch_id, claim_key),
        ).fetchall()
        return tuple(
            BeliefRevisionRecord(
                tick, key, Position(previous) if previous else None,
                Position(current), reason, tuple(json.loads(basis)),
            )
            for tick, key, previous, current, reason, basis in rows
        )

    def evidence_count(self) -> int:
        self._ensure_open()
        return self._db.execute(
            "SELECT count(*) FROM epistemic_evidence "
            "WHERE subject_id=? AND epoch_id=?",
            (self.subject_id, self.epoch_id),
        ).fetchone()[0]

    def process_claims(
        self, tick: int, claims: Iterable[EpistemicClaim], *,
        revisions: Iterable[BeliefRevision] = (),
        fault: str | None = None,
    ) -> CommitReceipt:
        """Durably transduce and record claims with optional belief revision.

        Failpoints match the reference host:
        after_preview/before_commit roll back everything; after_commit raises
        after a completed durable commit (retry must inspect checkpoint).
        """
        self._ensure_open()
        if fault not in (None, "after_preview", "before_commit", "after_commit"):
            raise ValueError("unsupported fault point")
        batch = tuple(claims)
        changes = tuple(revisions)
        if len(batch) > self.policy.max_batch:
            raise ValueError("batch exceeds policy capacity")
        if len(changes) > self.policy.max_batch:
            raise ValueError("revisions exceed policy capacity")
        if any(type(x) is not BeliefRevision for x in changes):
            raise TypeError("all revisions must be BeliefRevision")
        self._db.execute("BEGIN IMMEDIATE")
        try:
            current = self._read_checkpoint_locked()
            monitor = EpistemicSourceMonitor(max_batch=self.policy.max_batch)
            projected = monitor.project(
                subject_id=self.subject_id, epoch_id=self.epoch_id,
                tick=tick, start_sequence=current.last_sequence + 1,
                claims=batch,
            )
            # v0.5's within-batch conflict events are intentionally replaced
            # by ONE persistent, cross-tick conflict notice per claim key.
            observations = list(projected.observations[:len(batch)])
            eligible = [
                (item, current.last_sequence + 1 + index)
                for index, item in enumerate(batch)
                if _eligible(item)
            ]
            topics: dict[str, str] = {}
            sources: dict[str, dict[Stance, set[str]]] = {}
            # Read historical evidence and validate canonical key/topic
            # consistency before any SQL write occurs.
            for claim, _ in eligible:
                key, topic = claim.claim_key, claim.topic
                assert key is not None and topic is not None
                if key not in sources:
                    prev_rows = self._evidence_rows(key)
                    if prev_rows and any(row[0] != topic for row in prev_rows):
                        raise ValueError("claim key conflicts with historical topic")
                    topics[key] = topic
                    groups = {Stance.AFFIRMS: set(), Stance.DENIES: set()}
                    for _, ref, stance in prev_rows:
                        groups[Stance(stance)].add(ref)
                    sources[key] = groups
                elif topics[key] != topic:
                    raise ValueError("claim key has mismatched topics in batch")
                sources[key][claim.stance].add(claim.source_ref)

            conflicts: list[tuple[str, str, int]] = []
            for key, groups in sources.items():
                aff, den = groups[Stance.AFFIRMS], groups[Stance.DENIES]
                if not (aff and den and len(aff | den) >= 2):
                    continue
                emitted = self._db.execute(
                    "SELECT 1 FROM epistemic_conflict_projection "
                    "WHERE subject_id=? AND epoch_id=? AND claim_key=?",
                    (self.subject_id, self.epoch_id, key),
                ).fetchone()
                if emitted:
                    continue
                max_salience = max(
                    item.salience for item, _ in eligible if item.claim_key == key
                )
                seq = current.last_sequence + 1 + len(observations)
                source_ref = "conflict:" + hashlib.sha256(
                    key.encode("utf-8")
                ).hexdigest()[:20]
                observations.append(Observation(
                    sequence=seq, tick=tick, epoch_id=self.epoch_id,
                    channel=Channel.COGNITION,
                    signal=SourceSignal(
                        self.subject_id, Kind.EVIDENCE_CONFLICT, topics[key],
                        source_ref=source_ref, acquired=True,
                        salience=max(0.55, max_salience),
                    ),
                    attested=True,
                ))
                conflicts.append((key, topics[key], len(observations) - 1))
            if len(observations) > self.policy.max_batch:
                raise ValueError("derived conflicts exceed policy capacity")
            organ = SyntheticIpseityOrgan.restore(current.to_dict())
            proposal = organ.preview(tick, observations)
            if fault == "after_preview":
                raise RuntimeError("injected failure after preview")

            # The organ cursor and subject-only outbox are committed in the
            # SAME SQLite transaction as all evidence and revisions.
            nxt = proposal.next_checkpoint
            cur = self._db.execute(
                "UPDATE subjects SET checkpoint_json=?, checkpoint_digest=? "
                "WHERE subject_id=? AND epoch_id=? AND checkpoint_digest=?",
                (_json(nxt.to_dict()), nxt.digest, self.subject_id,
                 self.epoch_id, current.digest),
            )
            if cur.rowcount != 1:
                raise RuntimeError("checkpoint lease conflict")
            outbox_id = None
            if proposal.output.frame.lines:
                lines_json = _json(list(proposal.output.frame.lines))
                outbox_id = self._db.execute(
                    "INSERT INTO outbox "
                    "(subject_id, epoch_id, tick, last_sequence, "
                    "subject_lines_json, content_sha256) VALUES (?,?,?,?,?,?)",
                    (self.subject_id, self.epoch_id, tick,
                     nxt.last_sequence, lines_json, _digest(lines_json)),
                ).lastrowid

            for index, claim in enumerate(batch):
                if not (claim.attested and claim.acquired):
                    continue
                self._db.execute(
                    "INSERT INTO epistemic_evidence "
                    "(subject_id, epoch_id, sequence, tick, kind, source_ref, "
                    "claim_key, topic, stance, lived_verified, content_digest) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        self.subject_id, self.epoch_id,
                        current.last_sequence + 1 + index, tick,
                        claim.kind.value, claim.source_ref,
                        claim.claim_key, claim.topic,
                        claim.stance.value if claim.stance else None,
                        int(claim.lived_verified),
                        hashlib.sha256(claim.text.encode("utf-8")).hexdigest(),
                    ),
                )
            # Record one conflict projection after admission, not just after
            # generating it. If it was suppressed by attention capacity, a
            # future source encounter may still surface the conflict.
            for key, topic, index in conflicts:
                if proposal.output.audit.records[index].decision == "admitted":
                    self._db.execute(
                        "INSERT INTO epistemic_conflict_projection VALUES (?,?,?,?,?)",
                        (self.subject_id, self.epoch_id, key, topic,
                         observations[index].sequence, tick),
                    )
            # The position history is a provisional opinion and cannot be
            # declared from unsupported, hidden or cross-subject sources.
            for revision in changes:
                if not revision.attested:
                    raise ValueError("belief revision requires trusted host attestation")
                rows = self._evidence_rows(revision.claim_key)
                if not rows:
                    raise ValueError("revision has no attested evidence")
                source_stances: dict[str, set[str]] = {}
                for topic, ref, stance in rows:
                    source_stances.setdefault(ref, set()).add(stance)
                if any(ref not in source_stances for ref in revision.basis_sources):
                    raise ValueError("revision basis is not known accessible evidence")
                if revision.position is not Position.SUSPENDS and not any(
                    revision.position.value in source_stances[ref]
                    for ref in revision.basis_sources
                ):
                    raise ValueError("provisional position lacks matching evidence")
                old = self._db.execute(
                    "SELECT new_position FROM epistemic_revisions "
                    "WHERE subject_id=? AND epoch_id=? AND claim_key=? ORDER BY id DESC LIMIT 1",
                    (self.subject_id, self.epoch_id, revision.claim_key),
                ).fetchone()
                previous = old[0] if old else None
                if previous == revision.position.value:
                    raise ValueError("duplicate provisional position is not a revision")
                topic = rows[0][0]
                self._db.execute(
                    "INSERT INTO epistemic_revisions "
                    "(subject_id, epoch_id, tick, claim_key, topic, "
                    "previous_position, new_position, reason, basis_sources_json) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        self.subject_id, self.epoch_id, tick,
                        revision.claim_key, topic, previous,
                        revision.position.value, revision.reason,
                        _json(list(revision.basis_sources)),
                    ),
                )
            if fault == "before_commit":
                raise RuntimeError("injected failure before commit")
            self._db.execute("COMMIT")
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise
        if fault == "after_commit":
            raise RuntimeError("injected failure after durable commit")
        return CommitReceipt(outbox_id, nxt.last_tick, nxt.last_sequence)
