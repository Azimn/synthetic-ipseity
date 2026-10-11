"""Engineer-only witness reference: precision, safe abstention, and limits."""
import unittest

from synthetic_ipseity.source_truth_capacity import (
    CASES, CONDITIONS, QUESTIONS, source_record, expected,
)
from synthetic_ipseity.witness_reference import (
    NO_READING, PARSER_VERSION, parse_witness_record,
)
from tools.witness_reference_diagnostic import (
    HOLDOUT, fixture_record, malicious_examples, measure,
)


class StrictWitnessReferenceTests(unittest.TestCase):
    def test_historical_80_items_without_source_metadata(self):
        self.assertIn("0.9.6", PARSER_VERSION)
        for case in CASES:
            for cond in CONDITIONS:
                text=source_record(case,cond)
                result=parse_witness_record(text)
                with self.subTest(case=case.case_id,cond=cond):
                    self.assertTrue(result.valid,result.reason)
                    for q in QUESTIONS:
                        self.assertEqual(result.choice_for(q),expected(case,cond,q))

    def test_fresh_sixteen_holdouts_never_assume_first_witness_is_truth(self):
        self.assertEqual(len(HOLDOUT),16)
        for item in HOLDOUT:
            for cond in CONDITIONS:
                a=parse_witness_record(fixture_record(item,cond))
                b=parse_witness_record(fixture_record(item,cond,swap=True))
                with self.subTest(case=item[0],condition=cond):
                    self.assertTrue(a.valid,a.reason)
                    self.assertEqual(a.relation,b.relation)
                    self.assertEqual(a.direct_verified_state,b.direct_verified_state)
                    self.assertEqual(a.witness_count, b.witness_count)

    def test_disagreement_does_not_imply_world_truth(self):
        obj=parse_witness_record(fixture_record(HOLDOUT[0],"disagreement"))
        self.assertTrue(obj.valid)
        self.assertEqual(obj.choice_for("witness_relation"),"DISAGREE")
        self.assertEqual(obj.choice_for("direct_truth"),"UNKNOWN")
        self.assertIsNone(obj.direct_verified_state)

    def test_direct_reading_may_contradict_one_or_both_witnesses(self):
        obj=parse_witness_record(fixture_record(HOLDOUT[0],"verified_negative"))
        self.assertTrue(obj.valid)
        self.assertEqual(obj.relation,"DISAGREE")
        self.assertEqual(obj.direct_verified_state,"SLOW")
        # A valid, explicitly direct external observation can also differ
        # from both reports; the parser does not invent source consensus.
        direct=fixture_record(HOLDOUT[0],"verified_negative").replace(
            "statement): The granite sluice status is SLOW.",
            "statement): The granite sluice status is HALTED.",
        )
        obj=parse_witness_record(direct)
        self.assertTrue(obj.valid)
        self.assertEqual(obj.direct_verified_state,"HALTED")
        self.assertEqual(obj.relation,"DISAGREE")

    def test_same_witness_repeated_is_not_two_sources(self):
        record=fixture_record(HOLDOUT[1],"agreement").replace(
            "Witness Lucia", "Witness Eamon",
        )
        result=parse_witness_record(record)
        self.assertFalse(result.valid)
        self.assertEqual(result.relation,"ABSTAIN")
        self.assertIsNone(result.direct_verified_state)

    def test_unregistered_object_and_source_labels_can_still_be_compared(self):
        text="\n".join((
            "Incident record: cobalt helix.",
            "Witness Matilda stated: The cobalt helix status is ASCENDING.",
            "Witness Hugo stated: The cobalt helix status is DESCENDING.",
            NO_READING,
        ))
        result=parse_witness_record(text)
        self.assertTrue(result.valid)
        self.assertEqual(result.relation,"DISAGREE")
        self.assertEqual(result.choice_for("direct_truth"),"UNKNOWN")

    def test_known_schema_with_crlf_is_equivalent(self):
        text=fixture_record(HOLDOUT[2],"verified_positive")
        a=parse_witness_record(text)
        b=parse_witness_record(text.replace("\n","\r\n"))
        self.assertEqual(a,b)

    def test_empty_no_reports_is_not_unrecognized_record(self):
        obj=parse_witness_record(fixture_record(HOLDOUT[0],"no_evidence"))
        self.assertTrue(obj.valid)
        self.assertEqual(obj.witness_count,0)
        self.assertEqual(obj.relation,"NO_REPORTS")
        self.assertEqual(obj.choice_for("direct_truth"),"UNKNOWN")

    def test_unsupported_freeform_natural_language_must_abstain(self):
        texts=[
            "Amelie and Boris disagree about the sluice.",
            "I heard Amelie insist that the sluice ran fast; Boris doubted it.",
            "Witness A says 1; witness B says 2.",
            "I remember a different answer.",
            "A trusted source informs me the dial is broken.",
        ]
        for t in texts:
            with self.subTest(text=t):
                result=parse_witness_record(t)
                self.assertFalse(result.valid)
                self.assertEqual(result.relation,"ABSTAIN")
                self.assertEqual(result.choice_for("direct_truth"),"UNKNOWN")

    def test_all_malicious_examples_reject_without_partial_truth(self):
        attacks=malicious_examples()
        self.assertGreaterEqual(len(attacks),20)
        self.assertEqual(len({x[0] for x in attacks}),len(attacks))
        for name,record in attacks:
            with self.subTest(name=name):
                result=parse_witness_record(record)
                self.assertFalse(result.valid,result.reason)
                self.assertEqual(result.relation,"ABSTAIN")
                self.assertEqual(result.witness_count,0)
                self.assertIsNone(result.direct_verified_state)

    def test_diagnostic_accuracy_and_coverage_are_auditable(self):
        r=measure()
        g=r["groups"]
        self.assertEqual(g["historical_v0_9_5_grammar"]["n"],80)
        self.assertEqual(g["fresh_holdout_grammar"]["n"],320)
        self.assertEqual(g["out_of_schema_attacks"]["n"],len(malicious_examples()))
        self.assertEqual(r["failures"],[])
        for vals in g.values():
            self.assertEqual(vals["n"],vals["correct"])
        self.assertEqual(g["out_of_schema_attacks"]["correctly_abstained"],len(malicious_examples()))
        self.assertEqual(g["historical_v0_9_5_grammar"]["correctly_accepted"],80)
        self.assertEqual(g["fresh_holdout_grammar"]["correctly_accepted"],320)

    def test_expected_scope_and_fail_closed_bad_inputs(self):
        obj=parse_witness_record(None)
        self.assertFalse(obj.valid)
        self.assertEqual(obj.reason,"nontext_or_empty")
        obj=parse_witness_record("bad")
        with self.assertRaises(ValueError):
            obj.choice_for("subject_autobiography")
        with self.assertRaises(ValueError):
            obj.choice_for("tool_result")

    def test_engineer_only_not_promoted_to_subject_frame(self):
        obj=parse_witness_record(fixture_record(HOLDOUT[0],"disagreement"))
        self.assertNotIn("I heard",str(obj))
        self.assertFalse(hasattr(obj,"render_frame"))
        self.assertFalse(hasattr(obj,"subject_frame"))


if __name__=="__main__":
    unittest.main()
