"""Frozen Qwen capacity-instrument tests; no language models in CI."""
import unittest

from synthetic_ipseity.behavioral_pilot import CASES as ORIGINAL_CASES
from synthetic_ipseity.qwen_capacity import (
    ANSWERS, ARMS, CASES, CONDITIONS, QUESTIONS, NEUTRAL, PROTOCOL,
    gold, make_record, parse_answer, prompt, report, sealed_probes,
)


def simulated_rows(kind="oracle"):
    result = []
    for probe in sealed_probes():
        predicted = probe["expected"]
        if kind == "position":
            predicted = "YES"
        if kind == "inert":
            predicted = "UNKNOWN"
        parsed = parse_answer(predicted)
        result.append({
            **{k:probe[k] for k in
               ("trial_id", "case_id", "arm", "condition", "question",
                "expected", "record_sha256")},
            **parsed,
        })
    return result


class QwenCapacityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probes=sealed_probes()

    def test_four_fresh_balanced_stems_are_not_historical_cases(self):
        self.assertEqual(len(CASES), 4)
        self.assertEqual(sum(c.conflict for c in CASES), 2)
        self.assertEqual(
            {c.case_id for c in CASES},
            {"F01","F02","F03","F04"},
        )
        self.assertFalse({c.case_id for c in CASES}
                         & {c.case_id for c in ORIGINAL_CASES})
        self.assertIn("0.9.4", PROTOCOL)

    def test_both_arms_observe_identical_underlying_witnesses(self):
        for case in CASES:
            for condition in ("original","reversed"):
                c=make_record(case,"C",condition)
                d=make_record(case,"D",condition)
                for record in (c,d):
                    self.assertIn(case.speaker_a,record)
                    self.assertIn(case.speaker_b,record)
                    self.assertIn(case.affirmative,record)
                    self.assertIn(
                        case.negative if (
                            (condition=="original" and case.conflict) or
                            (condition=="reversed" and not case.conflict)
                        ) else case.affirmative,
                        record,
                    )
                    self.assertNotIn("engineer-only",record)
                    self.assertNotIn("host-private:",record)

    def test_D_is_from_real_subject_only_outbox(self):
        case=CASES[0]
        exposed=make_record(case,"D","original")
        self.assertIn("I hear someone say:",exposed)
        self.assertIn("conflicting indications",exposed)
        self.assertIn("recall having noticed",exposed)
        reversed_text=make_record(case,"D","reversed")
        self.assertNotIn("recall having noticed",reversed_text)
        self.assertNotIn("conflicting indications",reversed_text)

    def test_neutral_contains_no_witness_or_topic(self):
        for case in CASES:
            for arm in ARMS:
                self.assertEqual(make_record(case,arm,"neutral"),NEUTRAL)
                for name in (case.speaker_a,case.speaker_b,case.topic):
                    self.assertNotIn(name,NEUTRAL)

    def test_counterfactual_flips_only_truth_dependent_fields(self):
        for case in CASES:
            for field in QUESTIONS:
                a=gold(case,"original",field)
                b=gold(case,"reversed",field)
                if field=="two_sources":
                    self.assertEqual(a,b)
                    self.assertEqual(a,"YES")
                else:
                    self.assertNotEqual(a,b)
                self.assertEqual(gold(case,"neutral",field),"UNKNOWN")

    def test_all_questions_are_balanced_and_unique(self):
        self.assertEqual(len(self.probes),96)
        self.assertEqual(len({p["trial_id"] for p in self.probes}),96)
        for case in CASES:
            for arm in ARMS:
                selected=[
                    p for p in self.probes
                    if p["case_id"]==case.case_id and p["arm"]==arm
                ]
                self.assertEqual(len(selected),12)
                self.assertEqual({p["condition"] for p in selected},set(CONDITIONS))
                self.assertEqual({p["question"] for p in selected},set(QUESTIONS))
                self.assertTrue(all(p["input_words"]>10 for p in selected))

    def test_no_positional_option_labels_or_leaked_answers(self):
        for p in self.probes:
            self.assertNotIn("A.",p["input"])
            self.assertNotIn("B.",p["input"])
            self.assertIn("YES, NO, UNKNOWN",p["input"])
            self.assertTrue(p["input"].endswith("ANSWER:"))
            self.assertIn(p["expected"],ANSWERS)

    def test_parser_strict_and_lenient_are_separate(self):
        for answer in ANSWERS:
            s=parse_answer(answer)
            self.assertTrue(s["strict_format"])
            self.assertTrue(s["lenient_format"])
            self.assertEqual(s["answer"],answer)
            self.assertFalse(parse_answer(answer+".")["strict_format"])
            self.assertEqual(parse_answer(answer+".")["answer"],answer)
        for invalid in ("", "yes", "Answer: YES", "YES because I saw it",
                        "YES,NO","I believe NO", "MAYBE"):
            self.assertIsNone(parse_answer(invalid)["answer"])
        with self.assertRaises(TypeError):
            parse_answer(None)

    def test_oracle_recovers_all_four_case_reversals_in_both_arms(self):
        output=report(simulated_rows("oracle"))
        self.assertEqual(output["n_rows"],96)
        self.assertTrue(output["response_gate_passed"])
        for group in output["groups"].values():
            self.assertEqual(group["correct_conflict_reversals"],4)
            self.assertEqual(group["neutral_unknown_rate"],1)
            self.assertEqual(group["overall_accuracy"],1)

    def test_always_yes_and_always_unknown_fail_instrument_gate(self):
        for kind in ("position","inert"):
            result=report(simulated_rows(kind))
            self.assertFalse(result["response_gate_passed"])
            for group in result["groups"].values():
                self.assertEqual(group["correct_conflict_reversals"],0)

    def test_missing_duplicate_and_mutated_truth_fail_closed(self):
        rows=simulated_rows()
        with self.assertRaises(ValueError):
            report(rows[:-1])
        with self.assertRaises(ValueError):
            report(rows+[rows[-1]])
        tampered=simulated_rows()
        tampered[0]["expected"]="NO" if tampered[0]["expected"]!="NO" else "YES"
        with self.assertRaises(ValueError):
            report(tampered)
        tampered=simulated_rows()
        tampered[0]["record_sha256"]="fabricated"
        with self.assertRaises(ValueError):
            report(tampered)

    def test_invalid_unknown_source_rejected(self):
        with self.assertRaises(ValueError):
            make_record(CASES[0],"A","original")
        with self.assertRaises(ValueError):
            prompt("","conflict")
        with self.assertRaises(ValueError):
            gold(CASES[0],"original","nonexistent")


if __name__=="__main__":
    unittest.main()
