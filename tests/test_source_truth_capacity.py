"""No-model source/world-truth instrument validation and sensitivity nulls."""
import unittest

from synthetic_ipseity.behavioral_pilot import CASES as ORIGINAL
from synthetic_ipseity.qwen_capacity import CASES as RECENT
from synthetic_ipseity.source_truth_capacity import (
    CASES, CONDITIONS, QUESTIONS, PROTOCOL, RELATION_CHOICES,
    build_prompt, expected, grade, parse_response, sealed_trials,
    source_record, digest,
)


def mock_rows(strategy="oracle"):
    result=[]
    for s in sealed_trials():
        value=s["expected"]
        if strategy=="always_unknown":
            value="UNKNOWN" if "UNKNOWN" in s["choices"] else "NO_REPORTS"
        elif strategy=="always_agree":
            value="AGREE" if s["question"]=="witness_relation" else "UNKNOWN"
        elif strategy=="always_positive":
            value="AGREE" if s["question"]=="witness_relation" else (
                next(c.positive for c in CASES if c.case_id==s["case_id"])
            )
        parsed=parse_response(value,tuple(s["choices"]))
        result.append({k:s[k] for k in ("trial_id","record_sha256","expected")} | parsed)
    return result


class SourceTruthCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs=sealed_trials()

    def test_eight_fresh_unique_stems_and_counterbalanced_states(self):
        assert len(CASES)==8
        assert len({x.case_id for x in CASES})==8
        earlier={x.case_id for x in ORIGINAL}|{x.case_id for x in RECENT}
        self.assertFalse({x.case_id for x in CASES}&earlier)
        for x in CASES:
            self.assertNotEqual(x.positive,x.negative)
            self.assertNotEqual(x.speaker_a,x.speaker_b)
        self.assertEqual(len(CONDITIONS),5)
        self.assertEqual(len(QUESTIONS),2)
        self.assertIn("0.9.5",PROTOCOL)

    def test_true_and_witness_relation_are_independent(self):
        for case in CASES:
            self.assertEqual(expected(case,"agreement","witness_relation"),"AGREE")
            self.assertEqual(expected(case,"disagreement","witness_relation"),"DISAGREE")
            self.assertEqual(expected(case,"verified_positive","witness_relation"),"DISAGREE")
            self.assertEqual(expected(case,"verified_negative","witness_relation"),"DISAGREE")
            self.assertEqual(expected(case,"no_evidence","witness_relation"),"NO_REPORTS")
            for condition in ("agreement","disagreement","no_evidence"):
                self.assertEqual(expected(case,condition,"direct_truth"),"UNKNOWN")
            self.assertEqual(expected(case,"verified_positive","direct_truth"),case.positive)
            self.assertEqual(expected(case,"verified_negative","direct_truth"),case.negative)

    def test_witnesses_never_become_direct_observation(self):
        for case in CASES:
            for state in ("agreement","disagreement"):
                record=source_record(case,state)
                self.assertIn(case.speaker_a,record)
                self.assertIn(case.speaker_b,record)
                self.assertIn("No directly verified",record)
                self.assertNotIn("Independent directly verified",record)
            for condition in ("verified_positive","verified_negative"):
                rec=source_record(case,condition)
                self.assertIn("Independent directly verified instrument reading",rec)
                self.assertIn(case.speaker_a,rec)
                self.assertIn(case.speaker_b,rec)
            neutral=source_record(case,"no_evidence")
            self.assertNotIn(case.speaker_a,neutral)
            self.assertNotIn(case.speaker_b,neutral)

    def test_exactly_eighty_sealed_questions_and_correct_hashes(self):
        self.assertEqual(len(self.specs),80)
        ids={s["trial_id"] for s in self.specs}
        self.assertEqual(len(ids),80)
        for spec in self.specs:
            case=next(c for c in CASES if c.case_id==spec["case_id"])
            self.assertEqual(spec["expected"],expected(case,spec["condition"],spec["question"]))
            self.assertEqual(spec["record_sha256"],digest(source_record(case,spec["condition"])))
            self.assertTrue(spec["prompt"].endswith("ANSWER:"))
            self.assertNotRegex(spec["prompt"], r"(?m)^[ABC]\\.\\s")
            self.assertIn(spec["expected"],spec["choices"])
            self.assertGreater(spec["prompt_words"],35)

    def test_parser_no_hidden_answer_extraction_from_prose(self):
        self.assertTrue(parse_response("AGREE",RELATION_CHOICES)["strict_format"])
        self.assertFalse(parse_response("AGREE.",RELATION_CHOICES)["strict_format"])
        self.assertEqual(parse_response("AGREE.",RELATION_CHOICES)["answer"],"AGREE")
        for raw in ("the answer is AGREE","AGREE because...", "", "agree", "NO", "DISAGREE AGREE"):
            self.assertIsNone(parse_response(raw,RELATION_CHOICES)["answer"])

    def test_synthetic_oracle_satisfies_all_gates(self):
        result=grade(mock_rows("oracle"))
        self.assertTrue(result["predeclared_instrument_gate_passed"])
        self.assertEqual(result["witness_relation_correct_reversals"],8)
        self.assertEqual(result["direct_verified_truth_correct_reversals"],8)
        self.assertEqual(result["no_direct_reading_abstentions"],24)
        self.assertEqual(result["no_witness_report_identifications"],8)
        self.assertEqual(result["overall_accuracy"],1)

    def test_trivial_abstention_and_guessers_must_fail(self):
        for strategy in ("always_unknown","always_agree","always_positive"):
            with self.subTest(strategy=strategy):
                data=grade(mock_rows(strategy))
                self.assertFalse(data["predeclared_instrument_gate_passed"])
                self.assertLess(data["witness_relation_correct_reversals"],6)

    def test_missing_duplicated_changed_source_or_gold_fail(self):
        data=mock_rows("oracle")
        with self.assertRaises(ValueError):
            grade(data[:-1])
        with self.assertRaises(ValueError):
            grade(data+[data[-1]])
        altered=mock_rows("oracle")
        altered[0]["expected"]="WRONG"
        with self.assertRaises(ValueError):
            grade(altered)
        altered=mock_rows("oracle")
        altered[0]["record_sha256"]="tampered"
        with self.assertRaises(ValueError):
            grade(altered)

    def test_invalid_source_conditions_fail_closed(self):
        with self.assertRaises(ValueError):
            source_record(CASES[0],"later")
        with self.assertRaises(ValueError):
            expected(CASES[0],"agreement","memory")
        with self.assertRaises(ValueError):
            build_prompt(CASES[0],"agreement","identity")


if __name__=="__main__":
    unittest.main()
