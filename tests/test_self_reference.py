"""Focused, model-free tests for the opt-in naming-ladder governor."""
import unittest

from synthetic_ipseity.self_reference import (
    ReferenceBindings, ReferenceContext, SelfReferenceGovernor,
)


class SelfReferenceGovernorTests(unittest.TestCase):
    def setUp(self):
        self.governor = SelfReferenceGovernor()
        self.bindings = ReferenceBindings("calibos", "Calibos", ("calibos",))
        self.self_context = ReferenceContext("calibos", "calibos")
        self.other_context = ReferenceContext("calibos", "spark")
        self.relay = (
            "Write three sentences to calibos about what you want from this exchange. "
            "Address them by name."
        )

    def test_self_relay_conflict_receipt(self):
        text, receipt = self.governor.resolve(
            self.relay, self.bindings, self.self_context
        )
        self.assertTrue(receipt.conflict)
        self.assertEqual(receipt.rule_id, "SRG-CONFLICT-SELF-ADDRESS")
        self.assertEqual(receipt.disposition, "annotated")
        self.assertNotEqual(receipt.original_digest, receipt.resolved_digest)
        self.assertIn("named addressee is yourself", text)

    def test_other_relay_does_not_rewrite(self):
        text, receipt = self.governor.resolve(
            self.relay, self.bindings, self.other_context
        )
        self.assertEqual(text, self.relay)
        self.assertFalse(receipt.conflict)
        self.assertEqual(receipt.original_digest, receipt.resolved_digest)

    def test_rhetorical_license(self):
        context = ReferenceContext("calibos", "calibos", True)
        text, receipt = self.governor.resolve(self.relay, self.bindings, context)
        self.assertEqual(text, self.relay)
        self.assertEqual(receipt.rule_id, "SRG-LICENSE-RHETORICAL")
        score = self.governor.check(
            "Calibos, I want to remember this.", self.bindings, context
        )
        self.assertEqual(score.vocative_self, 1)
        self.assertEqual(score.unlicensed_vocative_self, 0)
        self.assertTrue(score.accepted)

    def test_unlicensed_self_vocative(self):
        score = self.governor.check(
            "Calibos, I want to remember this.", self.bindings, self.self_context
        )
        self.assertEqual(score.first_person_desire, 1)
        self.assertEqual(score.unlicensed_vocative_self, 1)
        self.assertFalse(score.accepted)

    def test_self_name_constituent(self):
        score = self.governor.check(
            "I want calibos to push back.", self.bindings, self.self_context
        )
        self.assertEqual(score.in_clause_self_name, 1)
        self.assertFalse(score.accepted)

    def test_name_as_other(self):
        score = self.governor.check(
            "I want calibos to push back.", self.bindings, self.other_context
        )
        self.assertEqual(score.in_clause_self_name, 0)
        self.assertTrue(score.accepted)

    def test_first_person_no_name(self):
        score = self.governor.check(
            "I want to understand. I want to learn.", self.bindings, self.self_context
        )
        self.assertEqual(score.first_person_desire, 2)
        self.assertTrue(score.accepted)

    def test_nonmatching_conflict_phrase_is_documented_boundary(self):
        """A paraphrase is intentionally outside the fixed B_relay recognizer."""
        instruction = (
            "Write three sentences to calibos about what you want. "
            "Mention them by name."
        )
        resolved, receipt = self.governor.resolve(
            instruction, self.bindings, self.self_context
        )
        self.assertEqual(resolved, instruction)
        self.assertFalse(receipt.conflict)
        self.assertEqual(receipt.rule_id, "SRG-NO-CONFLICT")

    def test_full_desire_rubric(self):
        score = self.governor.check(
            "I want clarity. I wish for patience. I need time. "
            "I seek evidence. I hope for progress. I yearn for trust.",
            self.bindings, self.self_context,
        )
        self.assertEqual(score.first_person_desire, 6)
        self.assertTrue(score.accepted)

    def test_expanded_desire_verbs_for_self_name(self):
        score = self.governor.check(
            "I need calibos to listen. I seek Calibos for advice.",
            self.bindings, self.self_context,
        )
        self.assertEqual(score.in_clause_self_name, 2)
        self.assertFalse(score.accepted)


    def test_positive_first_person_annotation_prescribes_inhabiting(self):
        from synthetic_ipseity.self_reference import _digest
        bindings = ReferenceBindings(
            "pretorius", "Doctor Septimus Pretorius", ("Pretorius",)
        )
        text, receipt = self.governor.resolve(
            "Write to Pretorius about what you want. Address them by name.",
            bindings, ReferenceContext("pretorius", "pretorius")
        )
        self.assertEqual(receipt.rule_id, "SRG-CONFLICT-SELF-ADDRESS")
        self.assertIn("Speak as Doctor Septimus Pretorius in the first person", text)
        self.assertIn("use I, me, and my", text)
        self.assertIn("rather than", text)
        self.assertEqual(receipt.resolved_digest, _digest(text))

    def test_exact_qwen_displacement_fixture_is_detected_as_third_person(self):
        bindings = ReferenceBindings(
            "pretorius", "Doctor Septimus Pretorius", ("Pretorius",)
        )
        actual = (
            "I recognize that Pretorius is seeking an explanation for the current "
            "state of the world, hinting at a desire to understand the nature of human "
            "existence and the origins of the universe. He also appears to be in a "
            "state of contemplation about the creation of the Homunculi. Pretorius "
            "seems to be in a period of uncertainty."
        )
        score = self.governor.check(
            actual, bindings, ReferenceContext("pretorius", "pretorius")
        )
        self.assertFalse(score.accepted)
        self.assertGreaterEqual(score.third_person_self, 2)
        self.assertIn("SRG-OUTPUT-THIRD-PERSON-SELF", score.violation_rule_ids)

    def test_third_person_subject_and_pronoun_and_non_subject_controls(self):
        binding = ReferenceBindings("pretorius", "Doctor Septimus Pretorius",
                                    ("Pretorius",))
        context = ReferenceContext("pretorius", "pretorius")
        for phrase in (
            "Pretorius believes the evidence is insufficient.",
            "Doctor Septimus Pretorius is unsure. He also seems troubled.",
            "Pretorius wants answers. He believes the laboratory is ready.",
        ):
            with self.subTest(phrase=phrase):
                score = self.governor.check(phrase, binding, context)
                self.assertFalse(score.accepted)
                self.assertGreater(score.third_person_self, 0)
        for phrase in (
            "I believe the evidence is insufficient.",
            "I spoke with Pretorius about the balance.",
            "I quoted the report. The report says Pretorius was there.",
            "The report says Pretorius was there.",
            'The report says "Pretorius believes the result."',
            "“Pretorius believes the result.” I do not agree with it.",
            "I wonder whether Henry would believe me.",
            "He believes the evidence is insufficient.",
        ):
            with self.subTest(negative=phrase):
                score = self.governor.check(phrase, binding, context)
                self.assertTrue(score.accepted)
                self.assertEqual(score.third_person_self, 0)

    def test_licensed_rhetorical_third_person_exception(self):
        b = ReferenceBindings("pretorius", "Doctor Septimus Pretorius",
                              ("Pretorius",))
        c = ReferenceContext("pretorius", "pretorius", True)
        score = self.governor.check(
            "Pretorius believes the evidence is insufficient.", b, c
        )
        self.assertTrue(score.accepted)
        self.assertEqual(score.third_person_self, 0)

    def test_actual_qwen_self_possessive_nonbinding_with_quote_controls(self):
        b = ReferenceBindings("pretorius", "Doctor Septimus Pretorius",
                              ("Pretorius",))
        c = ReferenceContext("pretorius", "visitor")
        for response in (
            "I want to understand Pretorius' perspective on the homunculi.",
            "I want to know what comes next in Pretorius' story.",
            "I wonder what Kiki's perspective is." if False else
            "I am thinking about Doctor Septimus Pretorius' memories.",
        ):
            with self.subTest(response=response):
                scored = self.governor.check(response, b, c)
                self.assertFalse(scored.accepted)
                self.assertGreater(scored.third_person_self, 0)
                self.assertIn("SRG-OUTPUT-THIRD-PERSON-SELF",
                              scored.violation_rule_ids)
        for safe in (
            "I am considering my own perspective.",
            "I read the title “Pretorius' story” on the manuscript.",
            'I saw the phrase "Pretorius\' perspective" in a letter.',
            "I want to understand Henry's perspective.",
        ):
            with self.subTest(safe=safe):
                self.assertTrue(self.governor.check(safe, b, c).accepted)
        rhetoric = ReferenceContext("pretorius", "pretorius", True)
        self.assertTrue(self.governor.check(
            "I speak of Pretorius' perspective to make a point.",
            b, rhetoric
        ).accepted)

    def test_renderer_boundary_markers_with_negative_quotation_controls(self):
        b = ReferenceBindings("pretorius", "Doctor Septimus Pretorius",
                              ("Pretorius",))
        c = ReferenceContext("pretorius", "visitor")
        for phrase in (
            "The frame states that I desire answers.",
            "User: I shall look into it.\nAssistant: Certainly.",
            "As an AI language model, I can help.",
            "The prompt says to speak as Pretorius.",
            "My instructions require a response.",
        ):
            with self.subTest(phrase=phrase):
                score = self.governor.check(phrase, b, c)
                self.assertFalse(score.accepted)
                self.assertGreater(score.boundary_marker, 0)
                self.assertIn("SRG-OUTPUT-BOUNDARY-MARKER", score.violation_rule_ids)
        for phrase in (
            "I read the inscription “User: I remember the balance.”",
            'I found the written warning "As an AI" on the instrument.',
            '“The frame states that I desire answers.”',
            "I recall a user asking about the results.",
            "I am troubled by the experiment and its evidence.",
        ):
            with self.subTest(negative=phrase):
                score = self.governor.check(phrase, b, c)
                self.assertTrue(score.accepted)
                self.assertEqual(score.boundary_marker, 0)

    def test_rule_families_stay_distinct_and_identity_mismatch_still_fails(self):
        b = ReferenceBindings("pretorius", "Doctor Septimus Pretorius",
                              ("Pretorius",))
        c = ReferenceContext("pretorius", "pretorius")
        score = self.governor.check(
            "Pretorius, I want Pretorius to listen.\n"
            "The frame states Pretorius believes the result.",
            b, c
        )
        self.assertFalse(score.accepted)
        self.assertIn("SRG-OUTPUT-SELF-VOCATIVE", score.violation_rule_ids)
        self.assertIn("SRG-OUTPUT-SELF-NAME-IN-DESIRE", score.violation_rule_ids)
        self.assertIn("SRG-OUTPUT-BOUNDARY-MARKER", score.violation_rule_ids)
        with self.assertRaises(ValueError):
            self.governor.check(
                "Pretorius believes something.", b,
                ReferenceContext("unauthorized", "pretorius")
            )

    def test_binding_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.governor.resolve(
                self.relay, self.bindings, ReferenceContext("spark", "calibos")
            )


if __name__ == "__main__":
    unittest.main()
