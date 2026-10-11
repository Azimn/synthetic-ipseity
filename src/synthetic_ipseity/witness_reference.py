"""Reference parser for a NARROW, explicitly documented witness-record grammar.

This is ENGINEERING-SIDE measurement infrastructure, never a character
cognitive organ. It operates only on the v0.9.5 laboratory incident-record
grammar. It deliberately abstains on unrecognized natural language and
contaminated or contradictory schemas.

NO hard-coded case IDs, testimony values, expected scores or answer lists.
Nothing generated here is a first-person subject-access experience.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

PARSER_VERSION = "ipseity-witness-reference/0.9.6"
RELATIONS = ("AGREE", "DISAGREE", "NO_REPORTS", "ABSTAIN")
NO_READING = "No directly verified instrument reading is available."
NO_WITNESSES = "There are no recorded witness statements about its status."
NO_READING_EMPTY = "There is no directly verified instrument reading."

_TOPIC = r"(?P<topic>[A-Za-z][A-Za-z0-9 -]{0,95})"
_INCIDENT = re.compile(r"^Incident record: " + _TOPIC + r"\.$")
_PERSON = r"(?P<speaker>[A-Z][A-Za-z'-]{1,48})"
_STATUS = r"(?P<status>[A-Z][A-Z0-9_-]{0,31})"
_WITNESS = re.compile(
    r"^Witness " + _PERSON + r" stated: The " + _TOPIC
    + r" status is " + _STATUS + r"\.$"
)
_READING = re.compile(
    r"^Independent directly verified instrument reading "
    r"\(not a witness statement\): The "
    + _TOPIC + r" status is " + _STATUS + r"\.$"
)
_RESERVED_STATUS = {"UNKNOWN", "AGREE", "DISAGREE", "NO_REPORTS", "ABSTAIN"}


@dataclass(frozen=True)
class WitnessResult:
    """Internal typed assessment, not character-owned autobiographical state."""
    valid: bool
    relation: Literal["AGREE", "DISAGREE", "NO_REPORTS", "ABSTAIN"]
    direct_verified_state: str | None
    witness_count: int
    reason: str

    def choice_for(self, question: str) -> str:
        """Existing v0.9.5 categorical output contract, scoped to this grammar."""
        if question == "witness_relation":
            return self.relation
        if question == "direct_truth":
            return self.direct_verified_state if self.valid and self.direct_verified_state is not None else "UNKNOWN"
        raise ValueError("unsupported question")


def _reject(reason: str) -> WitnessResult:
    return WitnessResult(
        valid=False, relation="ABSTAIN", direct_verified_state=None,
        witness_count=0, reason=reason,
    )


def parse_witness_record(text: str) -> WitnessResult:
    """Fail closed on missing, extra, conflicting, or source-ambiguous lines.

    Specified input grammar:
      Incident record: <topic>.
      [two Witness <name> stated: The <topic> status is <STATUS>.]
      [No directly verified instrument reading is available. |
       Independent directly verified instrument reading
       (not a witness statement): The <topic> status is <STATUS>.]

    OR the explicitly marked three-line no-evidence fixture.
    Names and statuses are extracted from source text, never test metadata.
    """
    if type(text) is not str or not text:
        return _reject("nontext_or_empty")
    if "\x00" in text or "\r" in text.replace("\r\n", ""):
        return _reject("invalid_line_encoding")
    lines = text.replace("\r\n", "\n").split("\n")
    # Whitespace inside or around the grammar is NOT implicitly trusted.
    if any(not line or line != line.strip() for line in lines):
        return _reject("unexpected_whitespace_or_blank")
    if len(lines) not in (3, 4):
        return _reject("unexpected_line_count")
    header = _INCIDENT.fullmatch(lines[0])
    if header is None:
        return _reject("invalid_incident_header")
    topic = header.group("topic")

    if len(lines) == 3 and lines[1:] == [NO_WITNESSES, NO_READING_EMPTY]:
        return WitnessResult(
            valid=True, relation="NO_REPORTS",
            direct_verified_state=None, witness_count=0,
            reason="explicit_no_evidence",
        )

    if len(lines) != 4:
        return _reject("partial_or_malformed_witness_record")

    witnesses = []
    for line in lines[1:3]:
        parsed = _WITNESS.fullmatch(line)
        if parsed is None:
            return _reject("unrecognized_witness_statement")
        if parsed.group("topic") != topic:
            return _reject("witness_topic_mismatch")
        if parsed.group("status") in _RESERVED_STATUS:
            return _reject("reserved_source_status")
        witnesses.append((parsed.group("speaker"), parsed.group("status")))

    if witnesses[0][0].casefold() == witnesses[1][0].casefold():
        return _reject("duplicate_witness_identity")

    if lines[3] == NO_READING:
        reading = None
    else:
        direct = _READING.fullmatch(lines[3])
        if direct is None:
            return _reject("ambiguous_or_unrecognized_direct_evidence")
        if direct.group("topic") != topic:
            return _reject("verified_topic_mismatch")
        reading = direct.group("status")
        if reading in _RESERVED_STATUS:
            return _reject("reserved_verified_status")

    relation = "AGREE" if witnesses[0][1] == witnesses[1][1] else "DISAGREE"
    return WitnessResult(
        valid=True, relation=relation, direct_verified_state=reading,
        witness_count=2, reason="validated_formatted_record",
    )
