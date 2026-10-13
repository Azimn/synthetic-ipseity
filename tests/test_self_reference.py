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

    def test_binding_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.governor.resolve(
                self.relay, self.bindings, ReferenceContext("spark", "calibos")
            )


if __name__ == "__main__":
    unittest.main()
