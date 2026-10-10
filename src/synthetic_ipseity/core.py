"""Offline, deterministic reference boundary for subject-accessible information.

This module protects a local API boundary, not an adversarial Python process.
The host is responsible for asserting acquisition truth and for wiring the
renderer to render_frame(result.frame), never to the engineer audit channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import math
from typing import Iterable


class Kind(str, Enum):
    COLD = "bodily_cold"
    FATIGUE = "bodily_fatigue"
    TRUST = "relationship_trust"
    RECOLLECTION = "recollection"
    HEARD_TEXT = "heard_text"
    INSTRUMENT = "read_instrument"
    REMINDER = "reminder"


class MemoryClass(str, Enum):
    LIVED = "lived"
    RECONSTRUCTED = "reconstructed"
    UNCERTAIN = "uncertain"


_NUMERIC = frozenset({Kind.COLD, Kind.FATIGUE, Kind.TRUST})
_TEXTUAL = frozenset({Kind.RECOLLECTION, Kind.HEARD_TEXT, Kind.INSTRUMENT, Kind.REMINDER})
_ISSUER = object()


def _unit(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise TypeError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError(f"{label} must be finite and between 0 and 1")
    return number


@dataclass(frozen=True)
class SourceSignal:
    """Host-supplied signal. Metadata is never placed inside SubjectFrame.

    acquired must be explicitly set True by a trusted host adapter when
    this subject may encounter this specific signal. The default denies access.
    The library relies on the host to attest that claim truthfully.
    salience is a host-supplied priority, not subject introspection.
    """

    subject_id: str
    kind: Kind
    value: float | str
    source_ref: str = ""
    acquired: bool = False
    salience: float = 0.8
    memory_class: MemoryClass = MemoryClass.UNCERTAIN

    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ValueError("subject_id must be a nonblank string")
        if not isinstance(self.kind, Kind):
            raise TypeError("kind must be Kind")
        if not isinstance(self.source_ref, str):
            raise TypeError("source_ref must be a string")
        if not isinstance(self.acquired, bool):
            raise TypeError("acquired must be bool")
        object.__setattr__(self, "salience", _unit(self.salience, "salience"))
        if not isinstance(self.memory_class, MemoryClass):
            raise TypeError("memory_class must be MemoryClass")
        if self.kind in _NUMERIC:
            object.__setattr__(self, "value", _unit(self.value, "signal value"))
            if self.memory_class is not MemoryClass.UNCERTAIN:
                raise ValueError("memory_class applies only to recollection")
        elif self.kind in _TEXTUAL:
            if not isinstance(self.value, str) or not self.value.strip():
                raise ValueError("textual signal requires nonblank text")
            if len(self.value) > 1000:
                raise ValueError("textual signal exceeds bounded capacity")
            if self.kind is not Kind.RECOLLECTION and self.memory_class is not MemoryClass.UNCERTAIN:
                raise ValueError("memory_class applies only to recollection")
        else:
            raise ValueError("unsupported signal kind")


@dataclass(frozen=True, init=False)
class SubjectFrame:
    """The renderer-facing projection: strictly just immutable experience text.

    Construction is issued by the organ, not by arbitrary raw caller data.
    Python module internals are not a security sandbox.
    """

    lines: tuple[str, ...]

    def __init__(self, *, _issuer: object = None, lines: tuple[str, ...] = ()) -> None:
        if _issuer is not _ISSUER:
            raise TypeError("SubjectFrame may only be issued by Ipseity.process")
        if not isinstance(lines, tuple) or any(
            not isinstance(line, str) or not line.strip() for line in lines
        ):
            raise TypeError("SubjectFrame lines must be nonblank immutable text")
        object.__setattr__(self, "lines", lines)


@dataclass(frozen=True)
class AuditRecord:
    """Engineer-only evidence; must not enter subject context."""

    subject_id: str
    source_ref: str
    kind: Kind
    raw_value: float | str
    salience: float
    decision: str


@dataclass(frozen=True)
class AuditEnvelope:
    records: tuple[AuditRecord, ...]


@dataclass(frozen=True)
class ProcessResult:
    frame: SubjectFrame
    audit: AuditEnvelope


def _quoted(raw: str) -> str:
    # Exact external text remains represented as quoted *content*.
    # Quoting does not alone defeat downstream prompt injection.
    return json.dumps(raw.strip(), ensure_ascii=False)


def _experience(signal: SourceSignal) -> str:
    if signal.kind is Kind.COLD:
        level = float(signal.value)
        if level < 0.15:
            return "I barely notice any chill."
        if level < 0.50:
            return "I feel a little cold."
        if level < 0.80:
            return "The cold is becoming hard to ignore."
        return "I feel deeply chilled."
    if signal.kind is Kind.FATIGUE:
        level = float(signal.value)
        if level < 0.15:
            return "I hardly notice tiredness."
        if level < 0.50:
            return "I feel a little tired."
        if level < 0.80:
            return "I am struggling to concentrate through the tiredness."
        return "I am exhausted."
    if signal.kind is Kind.TRUST:
        level = float(signal.value)
        if level < 0.30:
            return "I feel reluctant to trust them."
        if level > 0.75:
            return "I feel at ease with them."
        return "I am not sure how much I trust them."
    if signal.kind is Kind.HEARD_TEXT:
        return f"I hear someone say: {_quoted(str(signal.value))}."
    if signal.kind is Kind.INSTRUMENT:
        return f"I can read the instrument: {_quoted(str(signal.value))}."
    if signal.kind is Kind.REMINDER:
        return f"A reminder draws my attention to: {_quoted(str(signal.value))}."
    if signal.kind is Kind.RECOLLECTION:
        phrase = _quoted(str(signal.value))
        if signal.memory_class is MemoryClass.LIVED:
            return f"I remember an experience of {phrase}."
        if signal.memory_class is MemoryClass.RECONSTRUCTED:
            return f"I have an account of {phrase}, but I do not remember living it."
        return f"I have an uncertain impression of {phrase}."
    raise ValueError("no projector for signal kind")


class Ipseity:
    """Transduce a single subject's host-attested signals into bounded access."""

    def __init__(self, *, capacity: int = 3, admission_threshold: float = 0.35):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
            raise ValueError("capacity must be a nonnegative integer")
        self.capacity = capacity
        self.admission_threshold = _unit(admission_threshold, "admission_threshold")

    def process(self, subject_id: str, signals: Iterable[SourceSignal]) -> ProcessResult:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise ValueError("subject_id must be nonblank")
        sequence = tuple(signals)
        if any(not isinstance(s, SourceSignal) for s in sequence):
            raise TypeError("all signals must be SourceSignal")
        if any(s.subject_id != subject_id for s in sequence):
            raise ValueError("cross-subject input rejected")

        candidates = sorted(
            (index for index, s in enumerate(sequence)
             if s.acquired and s.salience >= self.admission_threshold),
            key=lambda index: (-sequence[index].salience, index),
        )
        admitted = frozenset(candidates[: self.capacity])
        lines: list[str] = []
        records: list[AuditRecord] = []
        for index, signal in enumerate(sequence):
            if index in admitted:
                lines.append(_experience(signal))
                decision = "admitted"
            elif not signal.acquired:
                decision = "unacquired"
            else:
                decision = "not_admitted"
            records.append(AuditRecord(
                subject_id=signal.subject_id,
                source_ref=signal.source_ref,
                kind=signal.kind,
                raw_value=signal.value,
                salience=signal.salience,
                decision=decision,
            ))
        return ProcessResult(
            frame=SubjectFrame(_issuer=_ISSUER, lines=tuple(lines)),
            audit=AuditEnvelope(records=tuple(records)),
        )


def render_frame(frame: SubjectFrame) -> str:
    """The only reference serialization point into subject-facing text."""
    if type(frame) is not SubjectFrame:
        raise TypeError("only SubjectFrame can be rendered")
    return "\n".join(frame.lines)
