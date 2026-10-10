"""PALINODE: opt-in, durable, guarded second-thought access.

A provisional position change in the epistemic ledger is not automatically
an experience. A host must separately attest awareness. Only an admitted
notice that was ACKNOWLEDGED by the subject-only outbox can support a later
host-attested recollection. Acknowledgement is a delivery signal, not
evidence of consciousness or of an actual biological memory.

All tickets and revision identifiers remain engineer-only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .core import Kind, SourceSignal
from .durable_host import CommitReceipt, _json, _digest
from .longitudinal import LongitudinalEpistemicHost
from .organ import AccessPolicy, Channel, Observation, SyntheticIpseityOrgan


PALINODE_SCHEMA_VERSION = 1


class ReflectionMode(str, Enum):
    NOTICE = "notice"
    RECALL = "recall"


@dataclass(frozen=True)
class ReflectionRequest:
    """A host-attested opportunity, never an arbitrary fabricated memory."""

    subject_id: str
    epoch_id: str
    revision_id: int
    mode: ReflectionMode
    acquired: bool = False
    attested: bool = False
    salience: float = 0.8

    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ValueError("subject_id is required")
        if not isinstance(self.epoch_id, str) or not self.epoch_id.strip():
            raise ValueError("epoch_id is required")
        if type(self.revision_id) is not int or self.revision_id < 1:
            raise ValueError("revision_id must be a positive integer")
        if type(self.mode) is not ReflectionMode:
            raise TypeError("mode must be ReflectionMode")
        if type(self.acquired) is not bool or type(self.attested) is not bool:
            raise TypeError("acquired and attested must be bool")
        # Delegate bound/NaN handling to the existing kernel.
        signal = SourceSignal(
            self.subject_id, Kind.PALINODE_SHIFT, "validated",
            acquired=self.acquired, salience=self.salience,
        )
        object.__setattr__(self, "salience", signal.salience)


@dataclass(frozen=True)
class ReflectionStatus:
    """Engineer-only observable delivery state."""

    revision_id: int
    notice_issued: bool
    notice_delivered: bool
    recall_issued: bool
    recall_delivered: bool


class PalinodeHost(LongitudinalEpistemicHost):
    """Additive opt-in extension. Uses canonical v0.7 source and belief tables.

    No new world or memory model is introduced. Both original process_evidence
    and raw host process APIs retain their previous behavior. Reflection events
    are tracked separately and use the same bounded source-access interface.
    """

    def __init__(
        self, db_path: str | Path, *, subject_id: str, epoch_id: str,
        policy: AccessPolicy | None = None,
    ) -> None:
        super().__init__(db_path, subject_id=subject_id, epoch_id=epoch_id, policy=policy)
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS palinode_meta (
                     subject_id TEXT NOT NULL, epoch_id TEXT NOT NULL,
                     schema_version INTEGER NOT NULL,
                     PRIMARY KEY(subject_id, epoch_id),
                     FOREIGN KEY(subject_id, epoch_id)
                         REFERENCES subjects(subject_id, epoch_id)
                   )"""
            )
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS palinode_tickets (
                     subject_id TEXT NOT NULL, epoch_id TEXT NOT NULL,
                     revision_id INTEGER NOT NULL,
                     mode TEXT NOT NULL CHECK(mode IN ('notice','recall')),
                     outbox_id INTEGER NOT NULL,
                     tick INTEGER NOT NULL, sequence INTEGER NOT NULL,
                     PRIMARY KEY(subject_id, epoch_id, revision_id, mode),
                     FOREIGN KEY(outbox_id) REFERENCES outbox(id)
                   )"""
            )
            self._db.execute(
                "INSERT OR IGNORE INTO palinode_meta VALUES (?,?,?)",
                (self.subject_id, self.epoch_id, PALINODE_SCHEMA_VERSION),
            )
            ver = self._db.execute(
                "SELECT schema_version FROM palinode_meta WHERE "
                "subject_id=? AND epoch_id=?",
                (self.subject_id, self.epoch_id),
            ).fetchone()
            if ver is None or ver[0] != PALINODE_SCHEMA_VERSION:
                raise ValueError("unsupported Palinode schema")
            self._db.execute("COMMIT")
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            self.close()
            raise

    def reconsideration_ids(self, claim_key: str) -> tuple[int, ...]:
        """Protected index of changes of mind; excludes first position."""
        self._ensure_open()
        if not isinstance(claim_key, str) or not claim_key.strip():
            raise ValueError("claim_key must be nonblank")
        rows = self._db.execute(
            "SELECT id FROM epistemic_belief_history "
            "WHERE subject_id=? AND epoch_id=? AND claim_key=? "
            "AND previous_position IS NOT NULL ORDER BY id",
            (self.subject_id, self.epoch_id, claim_key),
        ).fetchall()
        return tuple(row[0] for row in rows)

    def reflection_status(self, revision_id: int) -> ReflectionStatus:
        """Protected state; delivered means an outbox ACK, not consciousness."""
        self._ensure_open()
        if type(revision_id) is not int or revision_id < 1:
            raise ValueError("invalid revision id")
        rows = self._db.execute(
            "SELECT t.mode, o.delivery_state FROM palinode_tickets t "
            "JOIN outbox o ON o.id=t.outbox_id "
            "WHERE t.subject_id=? AND t.epoch_id=? AND t.revision_id=?",
            (self.subject_id, self.epoch_id, revision_id),
        ).fetchall()
        by_mode = dict(rows)
        return ReflectionStatus(
            revision_id,
            ReflectionMode.NOTICE.value in by_mode,
            by_mode.get(ReflectionMode.NOTICE.value) == "delivered",
            ReflectionMode.RECALL.value in by_mode,
            by_mode.get(ReflectionMode.RECALL.value) == "delivered",
        )

    def process_reflections(
        self, tick: int, requests: Iterable[ReflectionRequest], *,
        fault: str | None = None,
    ) -> CommitReceipt:
        """Atomically persist subject-only reflective notices and cursor.

        All reflection claims require prior committed belief revisions.
        Recall additionally requires a previous notice acknowledged by the
        outbox renderer. Unacquired or unattested opportunities still consume
        a sequence but never create tickets.
        """
        self._ensure_open()
        if fault not in (None, "after_preview", "before_commit", "after_commit"):
            raise ValueError("unknown fault point")
        batch = tuple(requests)
        if len(batch) > self.policy.max_batch:
            raise ValueError("reflection batch exceeds host bound")
        for item in batch:
            if type(item) is not ReflectionRequest:
                raise TypeError("reflection batch accepts ReflectionRequest only")
            if item.subject_id != self.subject_id or item.epoch_id != self.epoch_id:
                raise ValueError("cross-subject or epoch reflection denied")
        if len({(x.revision_id, x.mode) for x in batch}) != len(batch):
            raise ValueError("duplicate reflection request")
        self._db.execute("BEGIN IMMEDIATE")
        try:
            current = self._read_checkpoint_locked()
            observations = []
            for idx, item in enumerate(batch):
                row = self._db.execute(
                    "SELECT b.previous_position, b.new_position, b.tick, t.topic "
                    "FROM epistemic_belief_history b "
                    "JOIN epistemic_topics t ON t.subject_id=b.subject_id "
                    "AND t.epoch_id=b.epoch_id AND t.claim_key=b.claim_key "
                    "WHERE b.id=? AND b.subject_id=? AND b.epoch_id=?",
                    (item.revision_id, self.subject_id, self.epoch_id),
                ).fetchone()
                if row is None:
                    raise ValueError("reflection revision not found in this lifetime")
                previous, new_position, revision_tick, topic = row
                if previous is None:
                    raise ValueError("first position is not a reconsideration")
                if revision_tick >= tick:
                    raise ValueError("cannot introspect an uncommitted or future revision")
                authorized = item.acquired and item.attested
                if authorized:
                    other = self._db.execute(
                        "SELECT outbox_id FROM palinode_tickets "
                        "WHERE subject_id=? AND epoch_id=? AND revision_id=? AND mode=?",
                        (self.subject_id, self.epoch_id, item.revision_id, item.mode.value),
                    ).fetchone()
                    if other is not None:
                        raise ValueError("reflection already admitted for this revision")
                    if item.mode is ReflectionMode.RECALL:
                        prior = self._db.execute(
                            "SELECT o.delivery_state FROM palinode_tickets t "
                            "JOIN outbox o ON o.id=t.outbox_id "
                            "WHERE t.subject_id=? AND t.epoch_id=? "
                            "AND t.revision_id=? AND t.mode='notice'",
                            (self.subject_id, self.epoch_id, item.revision_id),
                        ).fetchone()
                        if prior is None or prior[0] != "delivered":
                            raise ValueError(
                                "cannot recall a reflection never delivered to the renderer"
                            )
                kind = (
                    Kind.PALINODE_RECALL if item.mode is ReflectionMode.RECALL
                    else Kind.PALINODE_DOUBT if new_position == "suspends"
                    else Kind.PALINODE_SHIFT
                )
                observations.append(Observation(
                    sequence=current.last_sequence + 1 + idx,
                    tick=tick,
                    epoch_id=self.epoch_id,
                    channel=Channel.MEMORY if item.mode is ReflectionMode.RECALL
                    else Channel.COGNITION,
                    signal=SourceSignal(
                        self.subject_id, kind, topic,
                        source_ref=f"palinode:{item.revision_id}:{item.mode.value}",
                        acquired=item.acquired, salience=item.salience,
                    ),
                    attested=item.attested,
                ))
            organ = SyntheticIpseityOrgan.restore(current.to_dict())
            proposal = organ.preview(tick, observations)
            if fault == "after_preview":
                raise RuntimeError("injected failure after preview")
            nxt = proposal.next_checkpoint
            result = self._db.execute(
                "UPDATE subjects SET checkpoint_json=?, checkpoint_digest=? "
                "WHERE subject_id=? AND epoch_id=? AND checkpoint_digest=?",
                (_json(nxt.to_dict()), nxt.digest,
                 self.subject_id, self.epoch_id, current.digest),
            )
            if result.rowcount != 1:
                raise RuntimeError("checkpoint lease conflict")
            outbox_id = None
            if proposal.output.frame.lines:
                lines_json = _json(list(proposal.output.frame.lines))
                outbox_id = self._db.execute(
                    "INSERT INTO outbox "
                    "(subject_id, epoch_id, tick, last_sequence, "
                    "subject_lines_json, content_sha256) VALUES (?,?,?,?,?,?)",
                    (self.subject_id, self.epoch_id, tick, nxt.last_sequence,
                     lines_json, _digest(lines_json)),
                ).lastrowid
            for item, audit, observation in zip(
                batch, proposal.output.audit.records, observations
            ):
                if audit.decision != "admitted":
                    continue
                assert outbox_id is not None
                self._db.execute(
                    "INSERT INTO palinode_tickets "
                    "(subject_id, epoch_id, revision_id, mode, outbox_id, tick, sequence) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (self.subject_id, self.epoch_id, item.revision_id,
                     item.mode.value, outbox_id, tick, observation.sequence),
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
