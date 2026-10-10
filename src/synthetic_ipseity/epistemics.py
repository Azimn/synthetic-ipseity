"""Deterministic, character-agnostic source monitoring before subject access.

This adapter transforms host-attested epistemic claims into typed organ inputs.
It distinguishes how information was acquired from whether its proposition is
true. It never turns testimony, inferred material, reconstructed autobiography,
imagination or dreams into verified lived history.

The trusted host still owns verification, source identity and visibility. This
module cannot authenticate an adversarial host or defeat downstream LLM prompt
injection merely by quoting external text.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import math
from typing import Iterable

from .core import Kind, MemoryClass, SourceSignal
from .organ import Channel, Observation


class EvidenceKind(str, Enum):
    OBSERVED = "observed"
    HEARD = "heard"
    READ = "read"
    LIVED_RECALL = "lived_recall"
    RECONSTRUCTED = "reconstructed"
    INFERRED = "inferred"
    IMAGINED = "imagined"
    DREAMED = "dreamed"
    RECOGNIZED = "recognized"


class Stance(str, Enum):
    AFFIRMS = "affirms"
    DENIES = "denies"


_CONFLICT_ELIGIBLE = frozenset({
    EvidenceKind.OBSERVED, EvidenceKind.HEARD, EvidenceKind.READ,
    EvidenceKind.RECONSTRUCTED, EvidenceKind.LIVED_RECALL,
})


def _label(value: object, name: str, *, limit: int = 160) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonblank text")
    if len(value) > limit:
        raise ValueError(f"{name} exceeds {limit} characters")
    return value


def _flag(value: object, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool")


def _confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("recognition_confidence must be a number")
    score = float(value)
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ValueError("recognition_confidence must be finite within 0..1")
    return score


@dataclass(frozen=True)
class EpistemicClaim:
    """One source-attested candidate. Metadata never enters SubjectFrame."""

    subject_id: str
    kind: EvidenceKind
    text: str
    source_ref: str
    acquired: bool = False
    attested: bool = False
    salience: float = 0.8
    lived_verified: bool = False
    recognition_confidence: float | None = None
    source_name: str | None = None
    claim_key: str | None = None
    topic: str | None = None
    stance: Stance | None = None

    def __post_init__(self) -> None:
        _label(self.subject_id, "subject_id")
        if type(self.kind) is not EvidenceKind:
            raise TypeError("kind must be EvidenceKind")
        _label(self.text, "text", limit=1000)
        _label(self.source_ref, "source_ref")
        _flag(self.acquired, "acquired")
        _flag(self.attested, "attested")
        _flag(self.lived_verified, "lived_verified")
        if self.lived_verified and self.kind is not EvidenceKind.LIVED_RECALL:
            raise ValueError("only a lived recollection may use lived_verified")
        if self.recognition_confidence is None:
            if self.kind is EvidenceKind.RECOGNIZED:
                raise ValueError("recognition requires a confidence value")
        else:
            if self.kind is not EvidenceKind.RECOGNIZED:
                raise ValueError("confidence is supported only for recognition")
            object.__setattr__(
                self, "recognition_confidence",
                _confidence(self.recognition_confidence),
            )
        if self.source_name is not None:
            _label(self.source_name, "source_name")
            if self.kind not in (EvidenceKind.HEARD, EvidenceKind.READ):
                raise ValueError("source_name is for visible testimony or texts")
        if any(x is not None for x in (self.claim_key, self.topic, self.stance)):
            if self.claim_key is None or self.topic is None or self.stance is None:
                raise ValueError("claim_key, topic and stance must be supplied together")
            _label(self.claim_key, "claim_key")
            _label(self.topic, "topic", limit=1000)
            if type(self.stance) is not Stance:
                raise TypeError("stance must be Stance")
            if self.kind not in _CONFLICT_ELIGIBLE:
                raise ValueError("only external evidence or recollection can be contrasted")
        # Validate priority and basic text/metadata bounds with the same
        # typed ingress contract as the core without granting access.
        baseline = SourceSignal(
            self.subject_id, Kind.SEEN_TEXT, self.text, self.source_ref,
            acquired=self.acquired, salience=self.salience,
        )
        object.__setattr__(self, "salience", baseline.salience)


@dataclass(frozen=True)
class EpistemicReceipt:
    """Engineer-only decision record, not subjective source knowledge."""

    source_ref: str
    kind: EvidenceKind
    decision: str


@dataclass(frozen=True)
class EpistemicBatch:
    observations: tuple[Observation, ...]
    receipts: tuple[EpistemicReceipt, ...]

    @property
    def count(self) -> int:
        return len(self.observations)


def _mapping(claim: EpistemicClaim) -> tuple[Kind, Channel, MemoryClass, str, str]:
    mode = claim.kind
    ordinary = MemoryClass.UNCERTAIN
    if mode is EvidenceKind.OBSERVED:
        return Kind.WORLD_OBJECT, Channel.WORLD, ordinary, claim.text, "observed"
    if mode is EvidenceKind.HEARD:
        words = claim.text if claim.source_name is None else (
            f"{claim.source_name} says: {claim.text}"
        )
        return Kind.HEARD_TEXT, Channel.COMMUNICATION, ordinary, words, "heard"
    if mode is EvidenceKind.READ:
        words = claim.text if claim.source_name is None else (
            f"{claim.source_name}: {claim.text}"
        )
        return Kind.SEEN_TEXT, Channel.WORLD, ordinary, words, "read"
    if mode is EvidenceKind.LIVED_RECALL:
        mem_class = (
            MemoryClass.LIVED if claim.lived_verified else MemoryClass.UNCERTAIN
        )
        return (
            Kind.RECOLLECTION, Channel.MEMORY, mem_class, claim.text,
            "verified_lived" if claim.lived_verified else "downgraded_unverified_lived",
        )
    if mode is EvidenceKind.RECONSTRUCTED:
        return (
            Kind.RECOLLECTION, Channel.MEMORY,
            MemoryClass.RECONSTRUCTED, claim.text, "reconstructed_not_lived",
        )
    if mode is EvidenceKind.INFERRED:
        return Kind.INFERENCE, Channel.COGNITION, ordinary, claim.text, "inferred"
    if mode is EvidenceKind.IMAGINED:
        return Kind.IMAGINATION, Channel.COGNITION, ordinary, claim.text, "imagined"
    if mode is EvidenceKind.DREAMED:
        return Kind.DREAM, Channel.MEMORY, ordinary, claim.text, "dreamed"
    if mode is EvidenceKind.RECOGNIZED:
        score = claim.recognition_confidence
        if score < 0.30:
            kind = Kind.RECOGNITION_VAGUE
        elif score < 0.65:
            kind = Kind.RECOGNITION_POSSIBLE
        elif score < 0.90:
            kind = Kind.RECOGNITION_LIKELY
        else:
            kind = Kind.RECOGNITION_STRONG
        return kind, Channel.WORLD, ordinary, claim.text, "uncertain_recognition"
    raise ValueError("unmapped evidence class")


class EpistemicSourceMonitor:
    """Pure source monitor. No ledger, model inference or host side effects.

    Contradictions are explicitly scoped to attested, acquired evidence with
    opposite host-coded stances under the same canonical claim key, from
    different source references. This is NOT open-ended semantic contradiction
    detection. Duplicating a single source cannot establish conflict.
    """

    def __init__(self, *, max_batch: int = 128):
        if type(max_batch) is not int or max_batch < 1 or max_batch > 4096:
            raise ValueError("max_batch must be an integer within 1..4096")
        self.max_batch = max_batch

    def project(
        self, *, subject_id: str, epoch_id: str, tick: int,
        start_sequence: int, claims: Iterable[EpistemicClaim],
    ) -> EpistemicBatch:
        _label(subject_id, "subject_id")
        _label(epoch_id, "epoch_id")
        if type(tick) is not int or tick < 0:
            raise ValueError("tick must be a nonnegative integer")
        if type(start_sequence) is not int or start_sequence < 1:
            raise ValueError("start_sequence must be >= 1")
        batch = tuple(claims)
        if len(batch) > self.max_batch:
            raise ValueError("claims exceed bounded monitor capacity")
        for claim in batch:
            if type(claim) is not EpistemicClaim:
                raise TypeError("all claims must be EpistemicClaim")
            if claim.subject_id != subject_id:
                raise ValueError("cross-subject epistemic input rejected")
        observations: list[Observation] = []
        receipts: list[EpistemicReceipt] = []
        sources: dict[str, tuple[str, dict[Stance, set[str]], float]] = {}
        # These values are never supplied to the character without passing
        # the same typed organ access and attention gates.
        for index, claim in enumerate(batch):
            kind, channel, memory_class, value, decision = _mapping(claim)
            observation = Observation(
                sequence=start_sequence + index,
                tick=tick,
                epoch_id=epoch_id,
                channel=channel,
                signal=SourceSignal(
                    subject_id, kind, value, source_ref=claim.source_ref,
                    acquired=claim.acquired, salience=claim.salience,
                    memory_class=memory_class,
                ),
                attested=claim.attested,
            )
            observations.append(observation)
            receipts.append(EpistemicReceipt(
                source_ref=claim.source_ref,
                kind=claim.kind,
                decision=decision if claim.attested and claim.acquired
                else "not_attested" if not claim.attested else "not_acquired",
            ))
            valid_contrast = (
                claim.acquired and claim.attested
                and claim.claim_key is not None
                and (
                    claim.kind is not EvidenceKind.LIVED_RECALL
                    or claim.lived_verified
                )
            )
            if valid_contrast:
                assert claim.topic is not None and claim.stance is not None
                if claim.claim_key not in sources:
                    sources[claim.claim_key] = (
                        claim.topic, {Stance.AFFIRMS: set(), Stance.DENIES: set()},
                        claim.salience,
                    )
                old_topic, group, salience = sources[claim.claim_key]
                if old_topic != claim.topic:
                    raise ValueError("one claim key has inconsistent topic labels")
                group[claim.stance].add(claim.source_ref)
                sources[claim.claim_key] = (
                    old_topic, group, max(salience, claim.salience),
                )
        for key, (topic, group, salience) in sources.items():
            if not group[Stance.AFFIRMS] or not group[Stance.DENIES]:
                continue
            if len(group[Stance.AFFIRMS] | group[Stance.DENIES]) < 2:
                continue
            source_ref = "conflict:" + hashlib.sha256(
                key.encode("utf-8")
            ).hexdigest()[:20]
            observations.append(Observation(
                sequence=start_sequence + len(observations),
                tick=tick, epoch_id=epoch_id,
                channel=Channel.COGNITION,
                signal=SourceSignal(
                    subject_id, Kind.EVIDENCE_CONFLICT, topic,
                    source_ref=source_ref, acquired=True,
                    salience=max(0.55, salience),
                ),
                attested=True,
            ))
            receipts.append(EpistemicReceipt(
                source_ref=source_ref,
                kind=EvidenceKind.INFERRED,
                decision="source_conflict_no_verdict",
            ))
        if len(observations) > self.max_batch:
            raise ValueError("claims and detected conflicts exceed bounded capacity")
        return EpistemicBatch(tuple(observations), tuple(receipts))
