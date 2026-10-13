"""Character-agnostic speech control contracts, not a Pretorius fixture."""
from __future__ import annotations
import unittest

from synthetic_ipseity.self_reference import (
    ReferenceBindings, ReferenceContext, SelfReferenceGovernor,
)
from synthetic_ipseity.speech_control import (
    GovernedSpeechControl, SpeechControlRejected,
)


class SpeechControlTests(unittest.TestCase):
    def bindings(self, subject):
        return ReferenceBindings(subject.lower(), subject, (subject.lower(),))

    def context(self, subject, **overrides):
        return ReferenceContext(
            speaker_subject_id=subject.lower(),
            addressee_subject_id=overrides.pop("addressee", "visitor"),
            **overrides,
        )

    def make(self, subject="Calibos", *, responses=(), fallback=None,
             context=None, calls=2, require=True):
        seen = []
        queue = list(responses)

        def renderer(frame, instruction):
            seen.append((frame, instruction))
            return queue.pop(0)

        gov = GovernedSpeechControl(
            bindings=self.bindings(subject),
            context=context or self.context(subject),
            trusted_instruction="Answer the visitor.",
            generate=renderer,
            fallback_text=fallback,
            max_model_attempts=calls,
            require_direct_first_person=require,
        )
        return gov, seen

    def test_three_independent_hosts_use_identical_contract(self):
        for subject in ("Calibos", "Kiki", "Pretorius"):
            with self.subTest(subject=subject):
                gov, seen = self.make(
                    subject, responses=["I am considering the evidence."],
                    fallback="I must be cautious."
                )
                self.assertEqual(gov("I have a question."),
                                 "I am considering the evidence.")
                self.assertEqual(len(seen), 1)
                self.assertIn("speak AS " + subject, seen[0][1])
                self.assertEqual(seen[0][0], "I have a question.")
                self.assertEqual(gov.receipts[0].speaker_subject_id,
                                 subject.lower())
                self.assertEqual(gov.receipts[0].disposition, "primary")

    def test_bounded_repair_uses_same_admitted_subject_text(self):
        gov, seen = self.make(responses=[
            "Calibos believes the answer is uncertain.",
            "I believe the answer is uncertain.",
        ])
        self.assertEqual(gov("I recall uncertainty."),
                         "I believe the answer is uncertain.")
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0][0], seen[1][0])
        self.assertEqual(gov.receipts[0].disposition, "repaired")
        self.assertEqual(gov.receipts[0].attempts[0].violation_rule_ids,
                         ("SRG-OUTPUT-THIRD-PERSON-SELF",))
        self.assertEqual(gov.receipts[0].attempts[1].origin, "repair")
        self.assertIn("Repair instruction", seen[1][1])
        self.assertNotIn("Calibos believes", seen[1][1])

    def test_host_fallback_is_not_model_generated_or_memory(self):
        gov, seen = self.make(
            responses=["User: Calibos thinks.", "As an AI, I agree."],
            fallback="I cannot establish that from what I know."
        )
        self.assertEqual(gov("I need evidence."),
                         "I cannot establish that from what I know.")
        self.assertEqual(len(seen), 2)
        receipt = gov.receipts[0]
        self.assertEqual(receipt.disposition, "fallback")
        self.assertEqual(len(receipt.attempts), 3)
        self.assertEqual(receipt.attempts[-1].origin, "host_fallback")
        self.assertTrue(receipt.attempts[-1].accepted)
        self.assertNotIn("User:", str(receipt))

    def test_no_fallback_means_durable_host_must_keep_pending(self):
        gov, seen = self.make(responses=[
            "Calibos believes the evidence.", "User: help"
        ])
        with self.assertRaises(SpeechControlRejected):
            gov("I remember a disagreement.")
        self.assertEqual(len(seen), 2)
        self.assertEqual(gov.receipts[0].disposition, "rejected")

    def test_no_output_with_unverified_speaker_stance_silently_passes(self):
        gov, seen = self.make(responses=["He disagrees.", "The scene is settled."],
                              fallback="I cannot verify this.")
        result = gov("I cannot verify this.")
        self.assertEqual(result, "I cannot verify this.")
        self.assertEqual(gov.receipts[0].disposition, "fallback")
        self.assertEqual(gov.receipts[0].attempts[0].violation_rule_ids,
                         ("SRG-SPEAKER-STANCE-UNVERIFIED",))
        self.assertEqual(len(seen), 2)

    def test_quoted_false_positives_and_host_narrative_mode(self):
        ctx = self.context("Calibos", discourse_mode="narrated")
        gov, seen = self.make(
            responses=["Calibos believes the evidence is limited."],
            context=ctx
        )
        self.assertEqual(gov("I examined the matter."),
                         "Calibos believes the evidence is limited.")
        self.assertEqual(gov.receipts[0].disposition, "primary")
        quoted = self.make(
            responses=['I read the inscription “User: the evidence is suspect.”']
        )[0]
        self.assertIn("inscription", quoted("I have read the inscription."))

    def test_language_and_authority_fail_closed_before_model_call(self):
        seen = []
        with self.assertRaises(SpeechControlRejected):
            GovernedSpeechControl(
                bindings=self.bindings("Kiki"),
                context=self.context("Kiki", language="es"),
                trusted_instruction="Speak Spanish.",
                generate=lambda *_: seen.append("invoked") or "Yo comprendo.",
            )
        self.assertEqual(seen, [])
        with self.assertRaises(ValueError):
            GovernedSpeechControl(
                bindings=self.bindings("Kiki"),
                context=self.context("Calibos"),
                trusted_instruction="Answer.",
                generate=lambda *_: "I agree.",
            )
        with self.assertRaises(ValueError):
            ReferenceContext("kiki", discourse_mode="arbitrary")
        with self.assertRaises(TypeError):
            ReferenceContext("kiki", rhetorical_self_address="yes")

    def test_broken_host_fallback_is_rejected_before_generating(self):
        seen = []
        with self.assertRaises(SpeechControlRejected):
            GovernedSpeechControl(
                bindings=self.bindings("Kiki"), context=self.context("Kiki"),
                trusted_instruction="Answer.", fallback_text="Kiki thinks so.",
                generate=lambda *_: seen.append(1) or "I think so.",
            )
        self.assertEqual(seen, [])
        with self.assertRaises(SpeechControlRejected):
            GovernedSpeechControl(
                bindings=self.bindings("Kiki"), context=self.context("Kiki"),
                trusted_instruction="Answer.", fallback_text="Yes.",
                generate=lambda *_: "I think so.",
            )

    def test_trusted_self_context_with_rhetorical_license(self):
        b = self.bindings("Kiki")
        context = ReferenceContext("kiki", "kiki", rhetorical_self_address=True)
        control = GovernedSpeechControl(
            bindings=b, context=context, trusted_instruction="Address them by name.",
            generate=lambda frame, instr: "Kiki, I want an answer.",
        )
        self.assertEqual(control("I am thinking."),
                         "Kiki, I want an answer.")

    def test_subject_frame_quarantine_and_receipt_no_raw_text(self):
        utterance = "I watched the dawn over the laboratory."
        gov, seen = self.make(responses=[utterance])
        gov("I had a private observation.")
        receipt = str(gov.receipts[0])
        self.assertNotIn(utterance, receipt)
        self.assertNotIn("I had a private observation.", receipt)
        self.assertNotIn("renderer_instruction", seen[0][0])
        self.assertIn("Direct-speech task", seen[0][1])


if __name__ == "__main__":
    unittest.main()
