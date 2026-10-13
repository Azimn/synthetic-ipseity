"""Reusable, host-neutral speech validation and bounded recovery for Synthetic Ipseity.

This is a renderer-side linguistic contract, NOT a new cognitive organ, an
identity authority, or a semantic fact verifier. The host MUST supply bindings,
addressee and discourse permissions; no model or user text can redefine them.
Only admitted first-person text is passed as the generator's subject input.
Instructions, hashes and rule IDs are renderer/engineer only.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Callable

from .self_reference import (
    ReferenceBindings, ReferenceContext, ReferenceScore, SelfReferenceGovernor,
)

SUPPORTED_LANGUAGES = frozenset({"en"})


class SpeechControlRejected(RuntimeError):
    """No valid model speech or authorized, validated fallback was available."""


@dataclass(frozen=True)
class SpeechControlAttempt:
    origin: str
    output_digest: str
    accepted: bool
    violation_rule_ids: tuple[str, ...]


@dataclass(frozen=True)
class SpeechControlReceipt:
    """Engineering only: deliberately contains no raw user or model text."""
    subject_digest: str
    instruction_digest: str
    speaker_subject_id: str
    disposition: str
    attempts: tuple[SpeechControlAttempt, ...]


class GovernedSpeechControl:
    """Bounded generator -> validator -> repair -> safe host fallback.

    Primary and repair both see exactly the SAME first-person subject string;
    only the renderer-only instruction changes. Rejected model text is never
    fed back as a first-person percept or as trusted task evidence.
    Fallback is fully authored by the host (never by the model or governor),
    must be validated BEFORE any generation, and must not assert an observation
    the host has not authorized.

    There is no automatic interpretation of non-English text; unsupported
    languages fail closed BEFORE a model call. The default English checker is
    narrow: "accepted" means no *recognized* SRG violation, not that every
    natural-language reference is correct.
    """

    def __init__(
        self, *,
        bindings: ReferenceBindings,
        context: ReferenceContext,
        trusted_instruction: str,
        generate: Callable[[str, str], str],
        fallback_text: str | None = None,
        max_model_attempts: int = 2,
        require_direct_first_person: bool = True,
    ):
        if not isinstance(bindings, ReferenceBindings):
            raise TypeError("Identity must come from explicit host ReferenceBindings")
        if not isinstance(context, ReferenceContext):
            raise TypeError("Discourse authority must come from host ReferenceContext")
        if context.speaker_subject_id != bindings.subject_id:
            raise ValueError("Host speaker mismatch")
        if context.language not in SUPPORTED_LANGUAGES:
            raise SpeechControlRejected(
                "Unsupported language: no verified language-specific checks available"
            )
        if not callable(generate):
            raise TypeError("Trusted renderer callback required")
        if type(trusted_instruction) is not str or not trusted_instruction.strip():
            raise ValueError("Nonempty trusted instruction required")
        if type(max_model_attempts) is not int or max_model_attempts not in (1, 2):
            raise ValueError("Only one model call or one model call plus one repair")
        self.bindings = bindings
        self.context = context
        self._gov = SelfReferenceGovernor()
        self._generate = generate
        self._instruction = trusted_instruction
        if type(require_direct_first_person) is not bool:
            raise TypeError("Strict first-person mode requires a host boolean")
        self._max_calls = max_model_attempts
        self._strict = require_direct_first_person
        self._fallback = fallback_text
        self.receipts: list[SpeechControlReceipt] = []
        self.last_score: ReferenceScore | None = None
        if fallback_text is not None:
            if type(fallback_text) is not str or not fallback_text.strip():
                raise ValueError("Host fallback must be nonempty")
            check = self._gov.check(fallback_text, bindings, context)
            if not check.accepted:
                raise SpeechControlRejected(
                    "Host fallback violates the same speech validation contract"
                )
            if context.discourse_mode == "direct" and not _first_person_anchor(fallback_text):
                raise SpeechControlRejected(
                    "Direct-speech fallback requires explicit first-person anchoring"
                )

    def __call__(self, subject_text: str) -> str:
        if type(subject_text) is not str or not subject_text.strip():
            raise ValueError("Only admitted nonempty first-person input is allowed")
        instruction = self._gov.renderer_instruction(
            self._instruction, self.bindings, self.context
        )
        attempts: list[SpeechControlAttempt] = []
        for index in range(self._max_calls):
            effective = instruction
            if index:
                effective += (
                    "\nRepair instruction: express the admitted experience as "
                    "the host-bound subject's own speech. Do not include frame "
                    "labels, external narrator commentary or unlicensed "
                    "self-address. This correction is renderer configuration "
                    "only, not a new memory or observation."
                )
            try:
                candidate = self._generate(subject_text, effective)
            except (OSError, TimeoutError, ConnectionError, ValueError, TypeError):
                # Known local transport / invalid model output failure. Never
                # leak errors as subject experience or ACK an invalid model
                # reply. One trusted fallback may still be delivered.
                attempts.append(SpeechControlAttempt(
                    "initial" if index == 0 else "repair",
                    sha256(b"").hexdigest(),
                    False,
                    ("SRG-RENDERER-UNAVAILABLE",),
                ))
                self.last_score = None
                break
            if type(candidate) is not str or not candidate.strip():
                score = None
                accepted = False
                violations = ("SRG-EMPTY-RENDERER-OUTPUT",)
                digest = sha256(str(candidate).encode("utf8")).hexdigest()
            else:
                score = self._gov.check(candidate, self.bindings, self.context)
                accepted = score.accepted
                violations = score.violation_rule_ids
                if (accepted and self._strict and self.context.discourse_mode == "direct"
                        and not _first_person_anchor(candidate)):
                    accepted = False
                    violations = (*violations, "SRG-SPEAKER-STANCE-UNVERIFIED")
                digest = sha256(candidate.encode("utf8")).hexdigest()
            attempts.append(SpeechControlAttempt(
                "initial" if index == 0 else "repair",
                digest, accepted, violations
            ))
            self.last_score = score
            if accepted:
                self.receipts.append(self._receipt(subject_text, instruction,
                                                   "primary" if index == 0 else "repaired",
                                                   attempts))
                return candidate
        if self._fallback is not None:
            score = self._gov.check(self._fallback, self.bindings, self.context)
            if not score.accepted:  # validate again, never trust unchecked fallback
                raise SpeechControlRejected("Host fallback failed final validation")
            attempts.append(SpeechControlAttempt(
                "host_fallback", sha256(self._fallback.encode("utf8")).hexdigest(),
                True, score.violation_rule_ids
            ))
            self.last_score = score
            self.receipts.append(
                self._receipt(subject_text, instruction, "fallback", attempts)
            )
            return self._fallback
        self.receipts.append(
            self._receipt(subject_text, instruction, "rejected", attempts)
        )
        raise SpeechControlRejected(
            "All model attempts violated the speech contract; do not ACK delivery"
        )

    def _receipt(self, subject: str, instruction: str, disposition: str,
                 attempts: list[SpeechControlAttempt]) -> SpeechControlReceipt:
        return SpeechControlReceipt(
            subject_digest=sha256(subject.encode("utf8")).hexdigest(),
            instruction_digest=sha256(instruction.encode("utf8")).hexdigest(),
            speaker_subject_id=self.bindings.subject_id,
            disposition=disposition,
            attempts=tuple(attempts),
        )


def _first_person_anchor(text: str) -> bool:
    """Conservative requirement for *trusted fallbacks*, not all model speech."""
    import re
    from .self_reference import _model_owned_text
    return bool(re.search(r"\b(?:I|me|my|mine|myself)\b",
                          _model_owned_text(text), re.I))
