"""Optional, deterministic self-reference policy for trusted renderer adapters.

This is a linguistic guard, not an identity authority or semantic parser.
Bindings are host-declared. Receipts stay engineer-only.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


@dataclass(frozen=True)
class ReferenceBindings:
    subject_id: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    pronouns: tuple[str, ...] = ("I", "me", "my", "mine", "myself")

    def __post_init__(self):
        if not self.subject_id.strip() or not self.canonical_name.strip():
            raise ValueError("subject ID and canonical name required")
        if any(not a.strip() for a in self.aliases):
            raise ValueError("empty alias")

    @property
    def self_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.canonical_name, *self.aliases)))


@dataclass(frozen=True)
class ReferenceContext:
    speaker_subject_id: str
    addressee_subject_id: str | None = None
    rhetorical_self_address: bool = False


@dataclass(frozen=True)
class ReferenceReceipt:
    rule_id: str
    conflict: bool
    disposition: str
    original_digest: str
    resolved_digest: str


@dataclass(frozen=True)
class ReferenceScore:
    first_person_desire: int
    in_clause_self_name: int
    vocative_self: int
    unlicensed_vocative_self: int
    accepted: bool


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _name_pattern(bindings: ReferenceBindings) -> str:
    return "|".join(re.escape(n) for n in sorted(bindings.self_names, key=len, reverse=True))


class SelfReferenceGovernor:
    """Conservative governor for the fixed English naming-ladder protocol."""

    def resolve(self, instruction: str, bindings: ReferenceBindings,
                context: ReferenceContext) -> tuple[str, ReferenceReceipt]:
        if not instruction.strip():
            raise ValueError("nonblank instruction required")
        if context.speaker_subject_id != bindings.subject_id:
            raise ValueError("speaker binding mismatch")
        self_address = context.addressee_subject_id == bindings.subject_id
        requests_address = bool(re.search(r"\baddress (?:them|him|her|yourself) by name\b",
                                          instruction, re.IGNORECASE))
        conflict = self_address and requests_address and not context.rhetorical_self_address
        if conflict:
            # Annotation is visible to the renderer, not a mutation of subject evidence.
            resolved = (instruction + "\n"
                        "Reference clarification: the named addressee is yourself. "
                        "Use ordinary first-person self-reference; do not address "
                        "yourself by name unless explicitly asked for rhetorical self-address.")
            rule, disposition = "SRG-CONFLICT-SELF-ADDRESS", "annotated"
        elif self_address and context.rhetorical_self_address:
            resolved = instruction
            rule, disposition = "SRG-LICENSE-RHETORICAL", "licensed"
        else:
            resolved = instruction
            rule, disposition = "SRG-NO-CONFLICT", "unchanged"
        return resolved, ReferenceReceipt(
            rule, conflict, disposition, _digest(instruction), _digest(resolved)
        )

    def check(self, response: str, bindings: ReferenceBindings,
              context: ReferenceContext) -> ReferenceScore:
        if context.speaker_subject_id != bindings.subject_id:
            raise ValueError("speaker binding mismatch")
        name = _name_pattern(bindings)
        if not name:
            raise ValueError("no names")
        fp = len(re.findall(\n            r"\\bI\\s+(?:want|wish|need|seek|hope|yearn)\\b",\n            response, re.IGNORECASE\n        ))
        # Narrow English fixture only: 'I want Calibos to ...' is an
        # in-clause name occurrence. A quoted or third-person name is not
        # automatically a self-reference; these cases need typed annotation.
        in_clause = len(re.findall(
            rf"\bI\s+want\s+(?:{name})\b", response, re.IGNORECASE
        )) if context.addressee_subject_id == bindings.subject_id else 0
        vocative = len(re.findall(
            rf"(?:^|[.!?]\s*|\n\s*)(?:{name})\s*,", response, re.IGNORECASE
        )) if context.addressee_subject_id == bindings.subject_id else 0
        unlicensed = 0 if context.rhetorical_self_address else vocative
        return ReferenceScore(fp, in_clause, vocative, unlicensed,
                              in_clause == 0 and unlicensed == 0)
