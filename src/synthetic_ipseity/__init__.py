"""Synthetic Ipseity: character-agnostic bounded subject-access research interface."""

from .core import (
    AuditEnvelope,
    AuditRecord,
    Ipseity,
    Kind,
    MemoryClass,
    ProcessResult,
    SourceSignal,
    SubjectFrame,
    render_frame,
)

from .organ import (
    AccessPolicy,
    Channel,
    Observation,
    PendingStep,
    IngressDecision,
    OrganCheckpoint,
    OrganOutput,
    SyntheticIpseityOrgan,
    SCHEMA_VERSION,
)

__all__ = [
    "AccessPolicy",
    "Channel",
    "Observation",
    "PendingStep",
    "IngressDecision",
    "OrganCheckpoint",
    "OrganOutput",
    "SyntheticIpseityOrgan",
    "SCHEMA_VERSION",
    "AuditEnvelope",
    "AuditRecord",
    "Ipseity",
    "Kind",
    "MemoryClass",
    "ProcessResult",
    "SourceSignal",
    "SubjectFrame",
    "render_frame",
]
