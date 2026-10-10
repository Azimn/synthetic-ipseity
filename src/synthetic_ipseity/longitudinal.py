"""Longitudinal source evidence with atomic cursor and outbox persistence.

This reference host stores a PROVENANCE LEDGER, not an authoritative truth
database or a complete character memory. Only independently host-attested,
acquired, host-aligned, comparable source claims become active support. An
append-only history preserves retractions and source changes without erasure.
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
    EpistemicClaim, EpistemicSourceMonitor, EvidenceKind, Stance,
)
from .organ import AccessPolicy, Channel, Observation, SyntheticIpseityOrgan

LEDGER_SCHEMA_VERSION = 1
_ELIGIBLE = frozenset({
    EvidenceKind.OBSERVED, EvidenceKind.HEARD, EvidenceKind.READ,
    EvidenceKind.RECONSTRUCTED, EvidenceKind.LIVED_RECALL,
})


class ChangeKind(str, Enum):
    RETRACT = "retract"


@dataclass(frozen=True)
class EvidenceChange:
    """Host-attested withdrawal of a previously encountered source account."""

    subject_id: str
    source_ref: str
    claim_key: str
    topic: str
    operation: ChangeKind = ChangeKind.RETRACT
    acquired: bool = False
    attested: bool = False
    salience: float = 0.8

    def __post_init__(self) -> None:
        if type(self.operation) is not ChangeKind:
            raise TypeError("operation must be ChangeKind")
        if type(self.acquired) is not bool or type(self.attested) is not bool:
            raise TypeError("acquired and attested must be bool")
        # This is also the bound for host metadata and qualitative output.
        EpistemicClaim(
            subject_id=self.subject_id, kind=EvidenceKind.HEARD,
            text=self.topic, source_ref=self.source_ref,
            claim_key=self.claim_key, topic=self.topic,
            stance=Stance.AFFIRMS, salience=self.salience,
        )


@dataclass(frozen=True)
class LedgerStatus:
    """Engineer-only count of active attributed positions, not truth."""

    claim_key: str
    topic: str | None
    affirming_sources: int
    denying_sources: int
    conflict: bool

    @property
    def unresolved(self) -> bool:
        return self.conflict or (
            self.affirming_sources == 0 and self.denying_sources == 0
        )


@dataclass(frozen=True)
class LedgerCommit:
    """Do not provide this engineering receipt to the subject renderer."""

    cursor: CommitReceipt
    history_added: int
    derived_transitions: tuple[str, ...]


class LongitudinalEpistemicHost(DurableIpseityHost):
    """Opt-in SQLite host with a versioned, append-only evidence ledger.

    Each process_evidence call atomically commits all source events, evidence
    history, active source positions, subject cursor and first-person outbox.
    The legacy DurableIpseityHost.process method remains unchanged.
    """

    def __init__(
        self, db_path: str | Path, *, subject_id: str, epoch_id: str,
        policy: AccessPolicy | None = None,
    ) -> None:
        super().__init__(
            db_path, subject_id=subject_id, epoch_id=epoch_id, policy=policy,
        )
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS epistemic_meta (
                     subject_id TEXT NOT NULL,
                     epoch_id TEXT NOT NULL,
                     ledger_schema INTEGER NOT NULL,
                     PRIMARY KEY(subject_id, epoch_id),
                     FOREIGN KEY(subject_id, epoch_id)
                       REFERENCES subjects(subject_id, epoch_id)
                   )"""
            )
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS epistemic_topics (
                     subject_id TEXT NOT NULL, epoch_id TEXT NOT NULL,
                     claim_key TEXT NOT NULL, topic TEXT NOT NULL,
                     PRIMARY KEY(subject_id, epoch_id, claim_key)
                   )"""
            )
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS epistemic_history (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     subject_id TEXT NOT NULL, epoch_id TEXT NOT NULL,
                     tick INTEGER NOT NULL, sequence INTEGER NOT NULL,
                     claim_key TEXT NOT NULL, topic TEXT NOT NULL,
                     source_ref TEXT NOT NULL, operation TEXT NOT NULL,
                     stance TEXT, evidence_kind TEXT NOT NULL,
                     UNIQUE(subject_id, epoch_id, sequence)
                   )"""
            )
            self._db.execute(
                """CREATE INDEX IF NOT EXISTS idx_epistemic_history
                   ON epistemic_history(subject_id, epoch_id, claim_key, id)"""
            )
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS epistemic_current (
                     subject_id TEXT NOT NULL, epoch_id TEXT NOT NULL,
                     claim_key TEXT NOT NULL, source_ref TEXT NOT NULL,
                     stance TEXT NOT NULL, last_sequence INTEGER NOT NULL,
                     PRIMARY KEY(subject_id, epoch_id, claim_key, source_ref)
                   )"""
            )
            self._db.execute(
                "INSERT OR IGNORE INTO epistemic_meta VALUES (?,?,?)",
                (self.subject_id, self.epoch_id, LEDGER_SCHEMA_VERSION),
            )
            version = self._db.execute(
                "SELECT ledger_schema FROM epistemic_meta "
                "WHERE subject_id=? AND epoch_id=?",
                (self.subject_id, self.epoch_id),
            ).fetchone()[0]
            if version != LEDGER_SCHEMA_VERSION:
                raise ValueError("unsupported epistemic ledger schema")
            self._db.execute("COMMIT")
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            self.close()
            raise

    def _status(self, key: str) -> LedgerStatus:
        row = self._db.execute(
            "SELECT topic FROM epistemic_topics WHERE "
            "subject_id=? AND epoch_id=? AND claim_key=?",
            (self.subject_id, self.epoch_id, key),
        ).fetchone()
        counts = self._db.execute(
            "SELECT stance, count(*) FROM epistemic_current WHERE "
            "subject_id=? AND epoch_id=? AND claim_key=? GROUP BY stance",
            (self.subject_id, self.epoch_id, key),
        ).fetchall()
        groups = dict(counts)
        affirm = groups.get(Stance.AFFIRMS.value, 0)
        deny = groups.get(Stance.DENIES.value, 0)
        return LedgerStatus(
            key, None if row is None else row[0], affirm, deny,
            bool(affirm and deny),
        )

    def status(self, claim_key: str) -> LedgerStatus:
        """Engineer-only ledger summary scoped to this subject and epoch."""
        self._ensure_open()
        if not isinstance(claim_key, str) or not claim_key.strip():
            raise ValueError("claim_key must be nonblank")
        return self._status(claim_key)

    def history_count(self) -> int:
        """Engineer-only number of retained evidence revisions."""
        self._ensure_open()
        return self._db.execute(
            "SELECT count(*) FROM epistemic_history "
            "WHERE subject_id=? AND epoch_id=?",
            (self.subject_id, self.epoch_id),
        ).fetchone()[0]

    def process_evidence(
        self, tick: int, updates: Iterable[EpistemicClaim | EvidenceChange],
        *, fault: str | None = None,
    ) -> LedgerCommit:
        """Commit evidence and subject experience atomically in SQLite.

        Supported deterministic test fault points are after_ledger,
        before_commit, and after_commit. A caller whose response is lost after
        COMMIT must inspect the cursor/outbox, not replay the same sequence.
        """
        self._ensure_open()
        if fault not in (None, "after_ledger", "before_commit", "after_commit"):
            raise ValueError("invalid fault injection point")
        batch = tuple(updates)
        if len(batch) > self.policy.max_batch:
            raise ValueError("updates exceed organ maximum batch")
        for entry in batch:
            if type(entry) not in (EpistemicClaim, EvidenceChange):
                raise TypeError("updates must be claims or evidence changes")
            if entry.subject_id != self.subject_id:
                raise ValueError("cross-subject evidence refused")

        self._db.execute("BEGIN IMMEDIATE")
        try:
            current_checkpoint = self._read_checkpoint_locked()
            organ = SyntheticIpseityOrgan.restore(
                current_checkpoint.to_dict()
            )
            base_seq = current_checkpoint.last_sequence + 1
            observations: list[Observation] = []
            monitored = EpistemicSourceMonitor(max_batch=self.policy.max_batch)
            touched: dict[str, LedgerStatus] = {}
            last_change: dict[str, str] = {}
            history_added = 0

            for i, update in enumerate(batch):
                seq = base_seq + i
                if type(update) is EpistemicClaim:
                    projected = monitored.project(
                        subject_id=self.subject_id,
                        epoch_id=self.epoch_id,
                        tick=tick,
                        start_sequence=seq,
                        claims=(update,),
                    )
                    assert projected.count == 1
                    observations.extend(projected.observations)
                    qualified = (
                        update.attested and update.acquired
                        and update.claim_key is not None
                        and update.kind in _ELIGIBLE
                        and (update.kind is not EvidenceKind.LIVED_RECALL
                             or update.lived_verified)
                    )
                    if not qualified:
                        continue
                    assert update.stance is not None and update.topic is not None
                    key, topic, source = (
                        update.claim_key, update.topic, update.source_ref
                    )
                    if key not in touched:
                        touched[key] = self._status(key)
                    self._record_topic(key, topic)
                    previous = self._db.execute(
                        "SELECT stance FROM epistemic_current WHERE "
                        "subject_id=? AND epoch_id=? AND claim_key=? "
                        "AND source_ref=?",
                        (self.subject_id, self.epoch_id, key, source),
                    ).fetchone()
                    if previous and previous[0] != update.stance.value:
                        last_change[key] = "revised"
                    self._append(
                        tick, seq, key, topic, source, "assert",
                        update.stance.value, update.kind.value,
                    )
                    history_added += 1
                    self._db.execute(
                        "INSERT INTO epistemic_current VALUES (?,?,?,?,?,?) "
                        "ON CONFLICT(subject_id,epoch_id,claim_key,source_ref) "
                        "DO UPDATE SET stance=excluded.stance,"
                        "last_sequence=excluded.last_sequence",
                        (self.subject_id, self.epoch_id, key, source,
                         update.stance.value, seq),
                    )
                else:
                    # The update is a new, source-attested perception of a
                    # correction, not deletion of the original experience.
                    observations.append(Observation(
                        sequence=seq, tick=tick, epoch_id=self.epoch_id,
                        channel=Channel.COMMUNICATION,
                        signal=SourceSignal(
                            self.subject_id, Kind.EVIDENCE_RETRACTION,
                            update.topic, source_ref=update.source_ref,
                            acquired=update.acquired,
                            salience=update.salience,
                        ),
                        attested=update.attested,
                    ))
                    if not (update.attested and update.acquired):
                        continue
                    key = update.claim_key
                    if key not in touched:
                        touched[key] = self._status(key)
                    self._record_topic(key, update.topic)
                    previous = self._db.execute(
                        "SELECT stance FROM epistemic_current WHERE "
                        "subject_id=? AND epoch_id=? AND claim_key=? "
                        "AND source_ref=?",
                        (self.subject_id, self.epoch_id, key, update.source_ref),
                    ).fetchone()
                    if previous is None:
                        raise ValueError("cannot withdraw unknown active evidence")
                    self._append(
                        tick, seq, key, update.topic, update.source_ref,
                        "retract", None, "correction",
                    )
                    history_added += 1
                    self._db.execute(
                        "DELETE FROM epistemic_current WHERE subject_id=? "
                        "AND epoch_id=? AND claim_key=? AND source_ref=?",
                        (self.subject_id, self.epoch_id, key, update.source_ref),
                    )
                    last_change[key] = "retracted"

            transitions = []
            for key, previous in touched.items():
                current = self._status(key)
                if current.conflict and not previous.conflict:
                    kind, code = Kind.EVIDENCE_CONFLICT, "conflict_opened"
                elif previous.conflict and not current.conflict:
                    kind, code = Kind.EVIDENCE_RESOLUTION, "conflict_ceased"
                elif last_change.get(key) == "revised":
                    kind, code = Kind.EVIDENCE_REVISION, "source_revised"
                else:
                    continue
                assert current.topic is not None
                source_ref = "ledger:" + hashlib.sha256(
                    key.encode("utf-8")
                ).hexdigest()[:20]
                observations.append(Observation(
                    sequence=base_seq + len(observations), tick=tick,
                    epoch_id=self.epoch_id, channel=Channel.COGNITION,
                    signal=SourceSignal(
                        self.subject_id, kind, current.topic,
                        source_ref=source_ref, acquired=True, salience=0.95,
                    ),
                    attested=True,
                ))
                transitions.append(code)

            if len(observations) > self.policy.max_batch:
                raise ValueError("events and transitions exceed organ capacity")
            if fault == "after_ledger":
                raise RuntimeError("injected failure after ledger writes")
            pending = organ.preview(tick, observations)
            next_checkpoint = pending.next_checkpoint
            changed = self._db.execute(
                "UPDATE subjects SET checkpoint_json=?,checkpoint_digest=? "
                "WHERE subject_id=? AND epoch_id=? AND checkpoint_digest=?",
                (_json(next_checkpoint.to_dict()), next_checkpoint.digest,
                 self.subject_id, self.epoch_id, current_checkpoint.digest),
            )
            if changed.rowcount != 1:
                raise RuntimeError("cursor lease conflict")
            outbox_id = None
            if pending.output.frame.lines:
                lines_json = _json(list(pending.output.frame.lines))
                outbox_id = self._db.execute(
                    "INSERT INTO outbox "
                    "(subject_id,epoch_id,tick,last_sequence,"
                    "subject_lines_json,content_sha256) VALUES (?,?,?,?,?,?)",
                    (self.subject_id, self.epoch_id, tick,
                     next_checkpoint.last_sequence, lines_json,
                     _digest(lines_json)),
                ).lastrowid
            if fault == "before_commit":
                raise RuntimeError("injected failure before commit")
            self._db.execute("COMMIT")
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise
        if fault == "after_commit":
            raise RuntimeError("injected failure after durable commit")
        return LedgerCommit(
            CommitReceipt(
                outbox_id, next_checkpoint.last_tick,
                next_checkpoint.last_sequence,
            ),
            history_added,
            tuple(transitions),
        )

    def _record_topic(self, key: str, topic: str) -> None:
        current = self._db.execute(
            "SELECT topic FROM epistemic_topics WHERE "
            "subject_id=? AND epoch_id=? AND claim_key=?",
            (self.subject_id, self.epoch_id, key),
        ).fetchone()
        if current and current[0] != topic:
            raise ValueError("claim key topic conflict across time")
        if current is None:
            self._db.execute(
                "INSERT INTO epistemic_topics VALUES (?,?,?,?)",
                (self.subject_id, self.epoch_id, key, topic),
            )

    def _append(
        self, tick: int, seq: int, key: str, topic: str,
        source: str, op: str, stance: str | None, kind: str,
    ) -> None:
        self._db.execute(
            "INSERT INTO epistemic_history "
            "(subject_id,epoch_id,tick,sequence,claim_key,topic,"
            "source_ref,operation,stance,evidence_kind) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (self.subject_id, self.epoch_id, tick, seq, key, topic,
             source, op, stance, kind),
        )
