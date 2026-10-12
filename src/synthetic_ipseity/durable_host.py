"""Durable, character-agnostic reference host for Synthetic Ipseity.

SQLite owns the checkpoint, consumed cursor, and subject-only outbox in one
transaction. This host provides at-least-once delivery attempts, NOT exactly
once rendering or external actions. It assumes trusted source attestations,
a durable upstream event feed, and no direct renderer bypass paths.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
from typing import Callable, Iterable

from .organ import AccessPolicy, Observation, OrganCheckpoint, SyntheticIpseityOrgan

HOST_SCHEMA_VERSION = 1


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _int(value: object, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


@dataclass(frozen=True)
class CommitReceipt:
    """Engineer-only transaction receipt, not a renderer payload."""

    outbox_id: int | None
    last_tick: int
    last_sequence: int


@dataclass(frozen=True)
class DeliveryLease:
    """Opaque receipt for one pending, subject-only experience.

    Only read_subject_text accepts this handle. Never put the handle in a
    model prompt. A lease is bound to one host's subject and continuity epoch.
    """

    outbox_id: int
    token: str


class DurableIpseityHost:
    """One SQLite-backed host instance for a fixed subject and epoch.

    BEGIN IMMEDIATE serializes competing writers on the same SQLite file.
    Each process verifies the CURRENT stored checkpoint before projecting.
    No database transaction is left open during downstream rendering.
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        subject_id: str,
        epoch_id: str,
        policy: AccessPolicy | None = None,
    ) -> None:
        # Validate all identity and policy arguments before opening storage.
        organ = SyntheticIpseityOrgan(subject_id, epoch_id=epoch_id, policy=policy)
        self.subject_id = organ.subject_id
        self.epoch_id = organ.epoch_id
        self.policy = organ.policy
        self._closed = False
        self._db = sqlite3.connect(str(db_path), timeout=10.0, isolation_level=None)
        try:
            self._db.execute("PRAGMA busy_timeout=10000")
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA synchronous=FULL")
            self._db.execute("PRAGMA foreign_keys=ON")
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, HOST_SCHEMA_VERSION):
                raise ValueError("unsupported durable host schema")
            self._db.execute("BEGIN IMMEDIATE")
            try:
                if version == 0:
                    schema = """
                        CREATE TABLE IF NOT EXISTS subjects (
                            subject_id TEXT NOT NULL,
                            epoch_id TEXT NOT NULL,
                            checkpoint_json TEXT NOT NULL,
                            checkpoint_digest TEXT NOT NULL,
                            PRIMARY KEY(subject_id, epoch_id)
                        );
                        CREATE TABLE IF NOT EXISTS outbox (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject_id TEXT NOT NULL,
                            epoch_id TEXT NOT NULL,
                            tick INTEGER NOT NULL,
                            last_sequence INTEGER NOT NULL,
                            subject_lines_json TEXT NOT NULL,
                            content_sha256 TEXT NOT NULL,
                            delivery_state TEXT NOT NULL DEFAULT 'pending'
                                CHECK (delivery_state IN ('pending','leased','delivered')),
                            lease_token TEXT,
                            lease_until_ms INTEGER,
                            attempts INTEGER NOT NULL DEFAULT 0,
                            UNIQUE(subject_id, epoch_id, tick),
                            FOREIGN KEY(subject_id, epoch_id)
                                REFERENCES subjects(subject_id, epoch_id)
                        );
                        CREATE INDEX IF NOT EXISTS idx_ipseity_outbox
                            ON outbox(subject_id, epoch_id, delivery_state, id);
                        """
                    for statement in schema.split(";"):
                        if statement.strip():
                            self._db.execute(statement)
                    self._db.execute(f"PRAGMA user_version={HOST_SCHEMA_VERSION}")
                checkpoint = organ.checkpoint()
                self._db.execute(
                    "INSERT OR IGNORE INTO subjects VALUES (?, ?, ?, ?)",
                    (self.subject_id, self.epoch_id,
                     _json(checkpoint.to_dict()), checkpoint.digest),
                )
                self._read_checkpoint_locked()
                self._db.execute("COMMIT")
            except BaseException:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
                raise
        except BaseException:
            self._db.close()
            raise

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("host is closed")

    def _read_checkpoint_locked(self) -> OrganCheckpoint:
        row = self._db.execute(
            "SELECT checkpoint_json, checkpoint_digest FROM subjects "
            "WHERE subject_id=? AND epoch_id=?",
            (self.subject_id, self.epoch_id),
        ).fetchone()
        if row is None:
            raise RuntimeError("durable subject row disappeared")
        checkpoint = SyntheticIpseityOrgan.restore(json.loads(row[0])).checkpoint()
        if checkpoint.digest != row[1]:
            raise ValueError("checkpoint storage digest mismatch")
        if checkpoint.subject_id != self.subject_id or checkpoint.epoch_id != self.epoch_id:
            raise ValueError("subject identity mismatch")
        if AccessPolicy(
            checkpoint.capacity, checkpoint.admission_threshold, checkpoint.max_batch
        ) != self.policy:
            raise ValueError("host policy differs from persisted policy")
        return checkpoint

    def checkpoint(self) -> OrganCheckpoint:
        self._ensure_open()
        return self._read_checkpoint_locked()

    def process(
        self,
        tick: int,
        observations: Iterable[Observation],
        *,
        fault: str | None = None,
        require_drained: bool = False,
    ) -> CommitReceipt:
        """Atomically advance the organ and append admitted output.

        Fault names are test-only simulated crashes. Source observations are
        streamed from the CALLER'S durable feed. This host never stores raw
        inputs, so the caller must be able to replay the input after rollback.

        'after_preview': rollback; 'before_commit': rollback even after writes;
        'after_commit': data is durable but caller experiences uncertainty.
        """
        self._ensure_open()
        if fault not in (None, "after_preview", "before_commit", "after_commit"):
            raise ValueError("unknown fault injection point")
        if type(require_drained) is not bool:
            raise TypeError("require_drained must be bool")
        # Materialize before acquiring the transaction. A generator cannot
        # partially perform a commit by failing during iteration.
        batch = tuple(observations)
        self._db.execute("BEGIN IMMEDIATE")
        try:
            if require_drained:
                outstanding = self._db.execute(
                    "SELECT 1 FROM outbox WHERE subject_id=? AND epoch_id=? "
                    "AND delivery_state!='delivered' LIMIT 1",
                    (self.subject_id, self.epoch_id),
                ).fetchone()
                if outstanding is not None:
                    raise RuntimeError(
                        "outstanding subject frame must be delivered or "
                        "reconciled before another publish"
                    )
            current = self._read_checkpoint_locked()
            organ = SyntheticIpseityOrgan.restore(current.to_dict())
            proposal = organ.preview(tick, batch)
            if fault == "after_preview":
                raise RuntimeError("injected failure after preview")
            nxt = proposal.next_checkpoint
            cursor = self._db.execute(
                "UPDATE subjects SET checkpoint_json=?, checkpoint_digest=? "
                "WHERE subject_id=? AND epoch_id=? AND checkpoint_digest=?",
                (_json(nxt.to_dict()), nxt.digest,
                 self.subject_id, self.epoch_id, current.digest),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("checkpoint lease conflict")
            outbox_id = None
            if proposal.output.frame.lines:
                lines_json = _json(list(proposal.output.frame.lines))
                row = self._db.execute(
                    "INSERT INTO outbox "
                    "(subject_id, epoch_id, tick, last_sequence, "
                    "subject_lines_json, content_sha256) VALUES (?,?,?,?,?,?)",
                    (self.subject_id, self.epoch_id, tick, nxt.last_sequence,
                     lines_json, _digest(lines_json)),
                )
                outbox_id = row.lastrowid
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

    def pending_count(self) -> int:
        """Count not-yet-acknowledged frames for this exact subject."""
        self._ensure_open()
        return self._db.execute(
            "SELECT count(*) FROM outbox WHERE subject_id=? AND epoch_id=? "
            "AND delivery_state!='delivered'",
            (self.subject_id, self.epoch_id),
        ).fetchone()[0]

    def claim_next(self, *, now_ms: int, lease_ms: int = 30_000) -> DeliveryLease | None:
        """FIFO delivery; a live lease blocks newer messages.

        Expired leases can be claimed again by another worker. The same
        content can be rendered more than once after a crash. Consumers
        should deduplicate any external side effect independently.
        """
        self._ensure_open()
        _int(now_ms, "now_ms")
        _int(lease_ms, "lease_ms", minimum=1)
        if lease_ms > 3_600_000:
            raise ValueError("lease exceeds one hour")
        self._db.execute("BEGIN IMMEDIATE")
        try:
            row = self._db.execute(
                "SELECT id, delivery_state, lease_until_ms FROM outbox "
                "WHERE subject_id=? AND epoch_id=? AND delivery_state!='delivered' "
                "ORDER BY id LIMIT 1",
                (self.subject_id, self.epoch_id),
            ).fetchone()
            if row is None or (row[1] == "leased" and row[2] > now_ms):
                self._db.execute("COMMIT")
                return None
            token = secrets.token_hex(24)
            self._db.execute(
                "UPDATE outbox SET delivery_state='leased', lease_token=?, "
                "lease_until_ms=?, attempts=attempts+1 WHERE id=?",
                (token, now_ms + lease_ms, row[0]),
            )
            self._db.execute("COMMIT")
            return DeliveryLease(row[0], token)
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def _verify_lease(self, lease: DeliveryLease) -> sqlite3.Row | tuple:
        if type(lease) is not DeliveryLease:
            raise TypeError("expected DeliveryLease")
        row = self._db.execute(
            "SELECT subject_lines_json, content_sha256 FROM outbox "
            "WHERE id=? AND subject_id=? AND epoch_id=? "
            "AND delivery_state='leased' AND lease_token=?",
            (lease.outbox_id, self.subject_id, self.epoch_id, lease.token),
        ).fetchone()
        if row is None:
            raise ValueError("unknown, stale or foreign delivery lease")
        return row

    def read_subject_text(self, lease: DeliveryLease) -> str:
        """Only reference renderer handoff from durable storage.

        This endpoint loads ONLY persisted subject lines, never raw
        observations, engineer audits or diagnostic checkpoint JSON.
        """
        self._ensure_open()
        raw, digest = self._verify_lease(lease)
        if _digest(raw) != digest:
            raise ValueError("subject outbox integrity mismatch")
        lines = json.loads(raw)
        if not isinstance(lines, list) or not lines or any(
            not isinstance(s, str) or not s.strip() for s in lines
        ):
            raise ValueError("invalid subject-only output")
        return "\n".join(lines)

    def ack_delivery(self, lease: DeliveryLease) -> None:
        """Acknowledge AFTER rendering. Never assume exactly-once delivery."""
        self._ensure_open()
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._verify_lease(lease)
            self._db.execute(
                "UPDATE outbox SET delivery_state='delivered', "
                "lease_token=NULL, lease_until_ms=NULL "
                "WHERE id=? AND subject_id=? AND epoch_id=? AND lease_token=?",
                (lease.outbox_id, self.subject_id, self.epoch_id, lease.token),
            )
            self._db.execute("COMMIT")
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def close(self) -> None:
        if not self._closed:
            self._db.close()
            self._closed = True

    def __enter__(self) -> "DurableIpseityHost":
        self._ensure_open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
