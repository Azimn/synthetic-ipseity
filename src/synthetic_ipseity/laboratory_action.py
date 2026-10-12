"""A narrow, durable authorized laboratory action cycle for Synthetic Ipseity.

An untrusted model can PROPOSE a bounded action but cannot write world state.
A trusted host validates and journals the proposal, applies only an allowlisted
effect, ACKs the renderer's leased frame, and admits ONLY real host-produced
feedback to Synthetic Ipseity as a new acquired observation.

This is a single-writer reference laboratory adapter, not a general
multi-agent transaction engine, language parser, or cognitive organ.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Callable

from .core import Ipseity, Kind, SourceSignal
from .durable_host import DeliveryLease, DurableIpseityHost
from .organ import Channel, Observation

ALLOWED_ACTIONS = frozenset({"inspect_lamp", "open_drawer", "inspect_drawer"})
MAX_RESPONSE_CHARS = 4000


def _json(value: object) -> str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


@dataclass(frozen=True)
class LabActionReceipt:
    """Engineer-side receipt. Never pass directly into a subject's prompt."""
    outbox_id: int
    action: str
    accepted: bool
    feedback: str


class LaboratoryActionGateway:
    """Trusted, scoped, durable and idempotent lab actuator.

    Uses the very SAME SQLite database as the DurableIpseityHost, but an
    independent short-lived transaction connection. Host-owned SQLite
    checkpoint/outbox tables are not modified directly.

    Source-of-truth assumptions: one trusted owner of this subject and epoch;
    an authorized renderer lease already exists; no external writer modifies
    a reserved feedback tick. Outbox status/lease is checked on every proposal.
    """

    def __init__(self, db_path: str | Path, *, subject_id: str, epoch_id: str):
        if not isinstance(subject_id,str) or not subject_id.strip():
            raise ValueError("subject_id is required")
        if not isinstance(epoch_id,str) or not epoch_id.strip():
            raise ValueError("epoch_id is required")
        self.subject_id=subject_id
        self.epoch_id=epoch_id
        self._db=sqlite3.connect(str(db_path),timeout=10,isolation_level=None)
        self._db.execute("PRAGMA busy_timeout=10000")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._closed=False
        try:
            with self._db:
                row=self._db.execute(
                    "SELECT 1 FROM subjects WHERE subject_id=? AND epoch_id=?",
                    (self.subject_id,self.epoch_id),
                ).fetchone()
                if row is None:
                    raise ValueError("start DurableIpseityHost for this subject first")
                self._db.executescript("""
                CREATE TABLE IF NOT EXISTS reference_lab_state (
                    subject_id TEXT NOT NULL,
                    epoch_id TEXT NOT NULL,
                    drawer_open INTEGER NOT NULL DEFAULT 0
                      CHECK (drawer_open IN (0,1)),
                    PRIMARY KEY(subject_id,epoch_id),
                    FOREIGN KEY(subject_id,epoch_id)
                      REFERENCES subjects(subject_id,epoch_id)
                );
                CREATE TABLE IF NOT EXISTS reference_lab_action (
                    subject_id TEXT NOT NULL,
                    epoch_id TEXT NOT NULL,
                    outbox_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    accepted INTEGER NOT NULL CHECK (accepted IN (0,1)),
                    feedback TEXT NOT NULL,
                    response_sha256 TEXT NOT NULL,
                    feedback_tick INTEGER,
                    feedback_sequence INTEGER,
                    feedback_applied INTEGER NOT NULL DEFAULT 0
                      CHECK (feedback_applied IN (0,1)),
                    PRIMARY KEY(subject_id,epoch_id,outbox_id),
                    FOREIGN KEY(outbox_id) REFERENCES outbox(id),
                    FOREIGN KEY(subject_id,epoch_id)
                      REFERENCES subjects(subject_id,epoch_id)
                );
                """)
                self._db.execute(
                    "INSERT OR IGNORE INTO reference_lab_state(subject_id,epoch_id) VALUES (?,?)",
                    (self.subject_id,self.epoch_id),
                )
        except BaseException:
            self._db.close()
            raise

    def _ensure_open(self)->None:
        if self._closed:
            raise RuntimeError("action gateway closed")

    def _scoped_receipt(self,outbox_id:int)->LabActionReceipt | None:
        row=self._db.execute(
            "SELECT action,accepted,feedback FROM reference_lab_action "
            "WHERE subject_id=? AND epoch_id=? AND outbox_id=?",
            (self.subject_id,self.epoch_id,outbox_id),
        ).fetchone()
        return None if row is None else LabActionReceipt(
            outbox_id,row[0],bool(row[1]),row[2],
        )

    def _check_lease(self,lease:DeliveryLease)->None:
        if type(lease) is not DeliveryLease:
            raise TypeError("actual delivery lease required")
        row=self._db.execute(
            "SELECT 1 FROM outbox WHERE id=? AND subject_id=? AND epoch_id=? "
            "AND delivery_state='leased' AND lease_token=?",
            (lease.outbox_id,self.subject_id,self.epoch_id,lease.token),
        ).fetchone()
        if row is None:
            raise ValueError("missing, expired, delivered, or foreign lease")

    @staticmethod
    def _decode_proposal(raw:object)->str | None:
        # Exact payload grammar. No loose NL parser, substring or eval.
        if type(raw) is not str or len(raw)>MAX_RESPONSE_CHARS:
            return None
        try:
            obj=json.loads(raw)
        except json.JSONDecodeError:
            return None
        if type(obj) is not dict or set(obj)!={"action"}:
            return None
        action=obj["action"]
        return action if type(action) is str and action in ALLOWED_ACTIONS else None

    def record_action(self,lease:DeliveryLease,raw_model_response:object)->LabActionReceipt:
        """Commit authorized world effect and replay-keyed receipt atomically.

        On retry after a crash, a recorded decision WINS even if the model
        produces different text. Calling code should check receipt_before_model
        to avoid invoking a model twice; both paths are idempotent.
        """
        self._ensure_open()
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._check_lease(lease)
            old=self._scoped_receipt(lease.outbox_id)
            if old is not None:
                self._db.execute("COMMIT")
                return old
            action=self._decode_proposal(raw_model_response)
            accepted=action is not None
            if action=="inspect_lamp":
                feedback="The lamp is lit."
            elif action=="open_drawer":
                self._db.execute(
                    "UPDATE reference_lab_state SET drawer_open=1 "
                    "WHERE subject_id=? AND epoch_id=?",
                    (self.subject_id,self.epoch_id),
                )
                feedback="The drawer opens."
            elif action=="inspect_drawer":
                state=self._db.execute(
                    "SELECT drawer_open FROM reference_lab_state "
                    "WHERE subject_id=? AND epoch_id=?",
                    (self.subject_id,self.epoch_id),
                ).fetchone()
                if state is None:
                    raise RuntimeError("laboratory state missing")
                feedback=("I can see a small specimen tray inside the open drawer."
                          if state[0] else "The drawer is closed; I cannot see inside.")
            else:
                action="REJECTED"
                feedback="That action was not recognized or permitted."
            response_sha=hashlib.sha256(
                (raw_model_response if type(raw_model_response) is str else
                 "<nontext-model-response>").encode("utf-8")
            ).hexdigest()
            self._db.execute(
                "INSERT INTO reference_lab_action("
                "subject_id,epoch_id,outbox_id,action,accepted,feedback,response_sha256"
                ") VALUES (?,?,?,?,?,?,?)",
                (self.subject_id,self.epoch_id,lease.outbox_id,action,
                 int(accepted),feedback,response_sha),
            )
            self._db.execute("COMMIT")
            return LabActionReceipt(lease.outbox_id,action,accepted,feedback)
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def receipt_before_model(self,lease:DeliveryLease)->LabActionReceipt | None:
        self._ensure_open()
        self._check_lease(lease)
        return self._scoped_receipt(lease.outbox_id)

    def drawer_open(self)->bool:
        self._ensure_open()
        row=self._db.execute(
            "SELECT drawer_open FROM reference_lab_state "
            "WHERE subject_id=? AND epoch_id=?",
            (self.subject_id,self.epoch_id),
        ).fetchone()
        if row is None:
            raise RuntimeError("lab state missing")
        return bool(row[0])

    def action_count(self)->int:
        self._ensure_open()
        return self._db.execute(
            "SELECT count(*) FROM reference_lab_action "
            "WHERE subject_id=? AND epoch_id=?",
            (self.subject_id,self.epoch_id),
        ).fetchone()[0]

    def feedback_receipt(self)->LabActionReceipt | None:
        self._ensure_open()
        row=self._db.execute(
            "SELECT outbox_id,action,accepted,feedback "
            "FROM reference_lab_action WHERE subject_id=? AND epoch_id=? "
            "AND feedback_applied=0 ORDER BY outbox_id LIMIT 1",
            (self.subject_id,self.epoch_id),
        ).fetchone()
        return None if row is None else LabActionReceipt(
            row[0],row[1],bool(row[2]),row[3],
        )

    def _feedback_observation(self,receipt:LabActionReceipt,tick:int,seq:int)->Observation:
        """Feedback is host-authored after actual effect, never model-authored."""
        return Observation(
            sequence=seq,tick=tick,epoch_id=self.epoch_id,
            channel=(Channel.WORLD if receipt.accepted else Channel.TOOL),
            signal=SourceSignal(
                self.subject_id,
                (Kind.WORLD_OBJECT if receipt.accepted else Kind.TOOL_TEXT),
                receipt.feedback,
                source_ref=f"host-action-receipt:{receipt.outbox_id}",
                acquired=True,salience=0.99,
            ),
            attested=True,
        )

    def _ensure_expected_feedback_is_durable(
        self, receipt:LabActionReceipt, tick:int, seq:int,
    )->None:
        # Used ONLY in recovery after host.process committed but this
        # reference gateway could not yet mark feedback as applied.
        event=self._feedback_observation(receipt,tick,seq)
        expected=Ipseity().process(self.subject_id,(event.signal,)).frame.lines
        row=self._db.execute(
            "SELECT subject_lines_json,content_sha256 FROM outbox "
            "WHERE subject_id=? AND epoch_id=? AND tick=? AND last_sequence=?",
            (self.subject_id,self.epoch_id,tick,seq),
        ).fetchone()
        if row is None:
            raise RuntimeError("feedback cursor advanced without matching outbox")
        if hashlib.sha256(row[0].encode("utf-8")).hexdigest()!=row[1]:
            raise RuntimeError("feedback outbox integrity failure")
        if json.loads(row[0])!=list(expected):
            raise RuntimeError("cursor is not proven to match feedback event")

    def publish_next_feedback(
        self,host:DurableIpseityHost,*,fault:str|None=None,
    )->LabActionReceipt | None:
        """Commit one feedback observation and dedupe after crash/restart.

        One writer is assumed while feedback tick/sequence are reserved.
        If another producer races on this subject, fail CLOSED rather than
        silently treating unrelated output as character experience.
        """
        self._ensure_open()
        if (type(host) is not DurableIpseityHost
                or (host.subject_id,host.epoch_id)!=(self.subject_id,self.epoch_id)):
            raise ValueError("feedback requires matching authorized host")
        if fault not in (None,"after_feedback_commit"):
            raise ValueError("unsupported injected fault")
        receipt=self.feedback_receipt()
        if receipt is None:
            return None
        # Reserve the intended source cursor so a crash after host.process
        # can be distinguished from a crash before it.
        self._db.execute("BEGIN IMMEDIATE")
        try:
            row=self._db.execute(
                "SELECT feedback_tick,feedback_sequence "
                "FROM reference_lab_action WHERE subject_id=? AND epoch_id=? "
                "AND outbox_id=? AND feedback_applied=0",
                (self.subject_id,self.epoch_id,receipt.outbox_id),
            ).fetchone()
            if row is None:
                raise RuntimeError("pending action disappeared")
            if row[0] is None:
                cp=host.checkpoint()
                tick,seq=cp.last_tick+1,cp.last_sequence+1
                self._db.execute(
                    "UPDATE reference_lab_action SET feedback_tick=?,feedback_sequence=? "
                    "WHERE subject_id=? AND epoch_id=? AND outbox_id=?",
                    (tick,seq,self.subject_id,self.epoch_id,receipt.outbox_id),
                )
            else:
                tick,seq=row
            self._db.execute("COMMIT")
        except BaseException:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

        cp=host.checkpoint()
        if (cp.last_tick,cp.last_sequence)==(tick-1,seq-1):
            host.process(tick,(self._feedback_observation(receipt,tick,seq),),
                         fault=("after_commit" if fault=="after_feedback_commit" else None))
        elif (cp.last_tick,cp.last_sequence)!=(tick,seq):
            raise RuntimeError("another producer advanced reserved feedback cursor")
        # On retry following a committed-but-unmarked event, verify the actual
        # outbox frame contains exactly our host-authored feedback.
        self._ensure_expected_feedback_is_durable(receipt,tick,seq)
        self._db.execute(
            "UPDATE reference_lab_action SET feedback_applied=1 "
            "WHERE subject_id=? AND epoch_id=? AND outbox_id=? AND feedback_applied=0",
            (self.subject_id,self.epoch_id,receipt.outbox_id),
        )
        return receipt

    def close(self)->None:
        if not self._closed:
            self._db.close()
            self._closed=True

    def __enter__(self)->"LaboratoryActionGateway":
        self._ensure_open()
        return self

    def __exit__(self,*_args:object)->None:
        self.close()


class AuthorizedLaboratoryTurn:
    """Deliberate action cycle; does NOT automatically promote model text to memory."""

    def __init__(
        self,host:DurableIpseityHost,gateway:LaboratoryActionGateway,
        renderer:Callable[[str],str],
    ):
        if type(host) is not DurableIpseityHost:
            raise TypeError("trusted DurableIpseityHost required")
        if type(gateway) is not LaboratoryActionGateway:
            raise TypeError("trusted action gateway required")
        if (host.subject_id,host.epoch_id)!=(gateway.subject_id,gateway.epoch_id):
            raise ValueError("cross-subject lab gateway forbidden")
        if not callable(renderer):
            raise TypeError("text renderer required")
        self.host=host
        self.gateway=gateway
        self.renderer=renderer

    def propose_and_execute(
        self,*,now_ms:int,lease_ms:int=30000,fault:str|None=None
    )->LabActionReceipt|None:
        if fault not in (None,"after_action_commit"):
            raise ValueError("unsupported fault")
        lease=self.host.claim_next(now_ms=now_ms,lease_ms=lease_ms)
        if lease is None:
            return None
        prior=self.gateway.receipt_before_model(lease)
        if prior is None:
            # This is the ONLY model ingress; NO raw host/world/audit values.
            admitted=self.host.read_subject_text(lease)
            raw=self.renderer(admitted)
            # A model suggestion has ZERO authority until host validation.
            result=self.gateway.record_action(lease,raw)
        else:
            result=prior   # don't re-render or re-execute after a crash
        if fault=="after_action_commit":
            raise RuntimeError("injected crash after durable action, before outbox ACK")
        self.host.ack_delivery(lease)
        return result
