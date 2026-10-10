"""A deterministic, restartable subject-access organ.

This is a host-trust boundary, not an isolation sandbox for malicious Python
plugins or model runtimes. Host code MUST route renderer ingress exclusively
through render_frame(output.frame); audits and checkpoints are engineer-only.

An organ belongs to one subject and one continuity epoch. A strict increasing
event cursor provides exact-once processing without unbounded deduplication
storage. All validation happens before the organ state can advance.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping

from .core import (
    AuditEnvelope, Ipseity, Kind, SourceSignal, SubjectFrame,
)


SCHEMA_VERSION = "synthetic-ipseity-organ/0.2"


class Channel(str, Enum):
    BODY = "body"
    RELATIONSHIP = "relationship"
    MEMORY = "memory"
    WORLD = "world"
    COMMUNICATION = "communication"
    INSTRUMENT = "instrument"
    SCHEDULER = "scheduler"
    TOOL = "tool"
    COGNITION = "cognition"
    SELF_PERCEPTION = "self_perception"


# An ingress source cannot claim to be another type of access by changing
# a string label. The host is still responsible for truthfully attesting it.
_ALLOWED: Mapping[Kind, frozenset[Channel]] = {
    Kind.COLD: frozenset({Channel.BODY}),
    Kind.FATIGUE: frozenset({Channel.BODY}),
    Kind.TRUST: frozenset({Channel.RELATIONSHIP}),
    Kind.RECOLLECTION: frozenset({Channel.MEMORY}),
    Kind.HEARD_TEXT: frozenset({Channel.COMMUNICATION, Channel.SELF_PERCEPTION}),
    Kind.INSTRUMENT: frozenset({Channel.INSTRUMENT}),
    Kind.REMINDER: frozenset({Channel.SCHEDULER}),
    Kind.PAIN: frozenset({Channel.BODY}),
    Kind.HUNGER: frozenset({Channel.BODY}),
    Kind.FEAR: frozenset({Channel.BODY, Channel.COGNITION}),
    Kind.SEEN_TEXT: frozenset({Channel.WORLD}),
    Kind.TOOL_TEXT: frozenset({Channel.TOOL}),
    Kind.WORLD_OBJECT: frozenset({Channel.WORLD}),
    Kind.IMPULSE: frozenset({Channel.COGNITION}),
    Kind.INTENTION: frozenset({Channel.COGNITION}),
    Kind.CONCERN: frozenset({Channel.COGNITION}),
    Kind.INFERENCE: frozenset({Channel.COGNITION}),
    Kind.IMAGINATION: frozenset({Channel.COGNITION}),
    Kind.DREAM: frozenset({Channel.MEMORY}),
    Kind.SELF_SPEECH: frozenset({Channel.SELF_PERCEPTION}),
    Kind.RECOGNITION_VAGUE: frozenset({Channel.WORLD}),
    Kind.RECOGNITION_POSSIBLE: frozenset({Channel.WORLD}),
    Kind.RECOGNITION_LIKELY: frozenset({Channel.WORLD}),
    Kind.RECOGNITION_STRONG: frozenset({Channel.WORLD}),
    Kind.EVIDENCE_CONFLICT: frozenset({Channel.COGNITION}),
}


def _nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonblank string")
    if len(value) > 160:
        raise ValueError(f"{label} exceeds 160 characters")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _canonical(value: dict[str, object]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class AccessPolicy:
    capacity: int = 3
    admission_threshold: float = 0.35
    max_batch: int = 128

    def __post_init__(self) -> None:
        _integer(self.capacity, "capacity")
        _integer(self.max_batch, "max_batch", minimum=1)
        if self.capacity > 64:
            raise ValueError("capacity exceeds 64")
        # Delegate scalar validation to the original deterministic kernel.
        core = Ipseity(
            capacity=self.capacity,
            admission_threshold=self.admission_threshold,
        )
        object.__setattr__(self, "admission_threshold", core.admission_threshold)


@dataclass(frozen=True)
class Observation:
    """A host assertion about one acquisition opportunity.

    "attested" must be assigned by trusted integration code, not by user or
    retrieved tool text. Unattested signals consume a sequence number but
    cannot reach the subject. No cryptographic attestation is claimed.
    """

    sequence: int
    tick: int
    epoch_id: str
    channel: Channel
    signal: SourceSignal
    attested: bool = False

    def __post_init__(self) -> None:
        _integer(self.sequence, "sequence", minimum=1)
        _integer(self.tick, "tick")
        _nonblank(self.epoch_id, "epoch_id")
        if type(self.channel) is not Channel:
            raise TypeError("channel must be Channel")
        if type(self.signal) is not SourceSignal:
            raise TypeError("signal must be SourceSignal")
        if type(self.attested) is not bool:
            raise TypeError("attested must be bool")
        if self.channel not in _ALLOWED[self.signal.kind]:
            raise ValueError(
                f"{self.signal.kind.value} cannot be acquired through "
                f"{self.channel.value}"
            )


@dataclass(frozen=True)
class IngressDecision:
    """Engineer-only receipt. Never serialize this into a subject frame."""

    sequence: int
    channel: Channel
    decision: str


@dataclass(frozen=True)
class OrganOutput:
    """Do not pass the entire OrganOutput to a model or renderer."""

    frame: SubjectFrame
    audit: AuditEnvelope
    receipts: tuple[IngressDecision, ...]


@dataclass(frozen=True)
class PendingStep:
    """Prepare output and next cursor without mutating the live organ.

    A host must durably record next_checkpoint and source-stream progress
    before calling commit(). Output must not be rendered before that commit.
    """

    output: OrganOutput
    base_digest: str
    next_checkpoint: "OrganCheckpoint"


@dataclass(frozen=True)
class OrganCheckpoint:
    """Serializable, tamper-evident (not authenticated) cursor checkpoint.

    The digest catches accidental corruption only. An attacker able to edit
    both the checkpoint and its digest can forge it. A real host must protect
    this record and commit it atomically with consumed source events.
    """

    schema: str
    subject_id: str
    epoch_id: str
    last_tick: int
    last_sequence: int
    capacity: int
    admission_threshold: float
    max_batch: int
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "subject_id": self.subject_id,
            "epoch_id": self.epoch_id,
            "last_tick": self.last_tick,
            "last_sequence": self.last_sequence,
            "capacity": self.capacity,
            "admission_threshold": self.admission_threshold,
            "max_batch": self.max_batch,
            "digest": self.digest,
        }


class SyntheticIpseityOrgan:
    """Single-subject, offline, bounded access organ.

    The event cursor is deliberately strict: source events are sequential and
    gap-free. The host must persist the organ checkpoint alongside its source
    stream position. The same event cannot be processed twice within an epoch.
    """

    def __init__(
        self, subject_id: str, *, epoch_id: str = "epoch-1",
        policy: AccessPolicy | None = None,
    ) -> None:
        self.subject_id = _nonblank(subject_id, "subject_id")
        self.epoch_id = _nonblank(epoch_id, "epoch_id")
        if policy is not None and type(policy) is not AccessPolicy:
            raise TypeError("policy must be AccessPolicy")
        self.policy = policy or AccessPolicy()
        self._kernel = Ipseity(
            capacity=self.policy.capacity,
            admission_threshold=self.policy.admission_threshold,
        )
        self._last_tick = -1
        self._last_sequence = 0

    @property
    def last_tick(self) -> int:
        return self._last_tick

    @property
    def last_sequence(self) -> int:
        return self._last_sequence

    def step(
        self, tick: int, observations: Iterable[Observation],
    ) -> OrganOutput:
        _integer(tick, "tick")
        if tick <= self._last_tick:
            raise ValueError("tick must advance strictly")
        batch = tuple(observations)
        if len(batch) > self.policy.max_batch:
            raise ValueError("batch exceeds declared maximum")
        expected = self._last_sequence + 1
        for item in batch:
            if type(item) is not Observation:
                raise TypeError("batch accepts Observation only")
            if item.sequence != expected:
                raise ValueError("duplicate, skipped, or reordered event sequence")
            expected += 1
            if item.tick != tick:
                raise ValueError("observation tick does not match step tick")
            if item.epoch_id != self.epoch_id:
                raise ValueError("cross-epoch input rejected")
            if item.signal.subject_id != self.subject_id:
                raise ValueError("cross-subject input rejected")

        # Attestation and acquisition are independent gates. Merely setting
        # SourceSignal.acquired True does NOT grant access in this organ.
        gated = tuple(
            replace(item.signal, acquired=item.attested and item.signal.acquired)
            for item in batch
        )
        # Kernel projection may fail: do not advance the cursor on failure.
        result = self._kernel.process(self.subject_id, gated)
        receipts = tuple(
            IngressDecision(
                sequence=item.sequence,
                channel=item.channel,
                decision=(
                    "not_attested" if not item.attested else
                    "not_acquired" if not item.signal.acquired else
                    record.decision
                ),
            )
            for item, record in zip(batch, result.audit.records)
        )
        output = OrganOutput(result.frame, result.audit, receipts)
        self._last_tick = tick
        if batch:
            self._last_sequence = batch[-1].sequence
        return output

    def preview(
        self, tick: int, observations: Iterable[Observation],
    ) -> PendingStep:
        """Evaluate on a disposable clone; leave the live cursor unchanged."""
        base = self.checkpoint()
        clone = type(self).restore(base.to_dict())
        output = clone.step(tick, observations)
        return PendingStep(
            output=output,
            base_digest=base.digest,
            next_checkpoint=clone.checkpoint(),
        )

    def commit(self, pending: PendingStep) -> OrganOutput:
        """Apply a previously prepared transaction using an optimistic lease.

        A stale proposal is rejected. The host is responsible for persisting
        the proposed checkpoint and stream cursor as one durable transaction.
        """
        if type(pending) is not PendingStep:
            raise TypeError("pending must be PendingStep")
        if pending.base_digest != self.checkpoint().digest:
            raise ValueError("stale proposal or wrong base organ")
        updated = type(self).restore(pending.next_checkpoint.to_dict())
        if (updated.subject_id != self.subject_id
                or updated.epoch_id != self.epoch_id
                or updated.policy != self.policy
                or updated.last_tick <= self.last_tick
                or updated.last_sequence < self.last_sequence):
            raise ValueError("proposal violates subject or cursor continuity")
        self._last_tick = updated.last_tick
        self._last_sequence = updated.last_sequence
        return pending.output

    def checkpoint(self) -> OrganCheckpoint:
        body: dict[str, object] = {
            "schema": SCHEMA_VERSION,
            "subject_id": self.subject_id,
            "epoch_id": self.epoch_id,
            "last_tick": self._last_tick,
            "last_sequence": self._last_sequence,
            "capacity": self.policy.capacity,
            "admission_threshold": self.policy.admission_threshold,
            "max_batch": self.policy.max_batch,
        }
        return OrganCheckpoint(**body, digest=hashlib.sha256(_canonical(body)).hexdigest())

    @classmethod
    def restore(cls, data: Mapping[str, object]) -> "SyntheticIpseityOrgan":
        if not isinstance(data, Mapping):
            raise TypeError("checkpoint must be a mapping")
        required = frozenset(OrganCheckpoint.__dataclass_fields__)
        if set(data) != required:
            raise ValueError("checkpoint keys do not match schema")
        if data["schema"] != SCHEMA_VERSION:
            raise ValueError("unsupported checkpoint schema")
        _nonblank(data["subject_id"], "subject_id")
        _nonblank(data["epoch_id"], "epoch_id")
        tick = _integer(data["last_tick"], "last_tick", minimum=-1)
        sequence = _integer(data["last_sequence"], "last_sequence")
        if sequence > 0 and tick < 0:
            raise ValueError("event history requires a committed tick")
        policy = AccessPolicy(
            capacity=data["capacity"],
            admission_threshold=data["admission_threshold"],
            max_batch=data["max_batch"],
        )
        body = {key: data[key] for key in required if key != "digest"}
        expected = hashlib.sha256(_canonical(body)).hexdigest()
        if not isinstance(data["digest"], str) or data["digest"] != expected:
            raise ValueError("checkpoint integrity mismatch")
        organ = cls(
            data["subject_id"], epoch_id=data["epoch_id"], policy=policy,
        )
        organ._last_tick = tick
        organ._last_sequence = sequence
        return organ
