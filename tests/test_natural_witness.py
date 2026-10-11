"""v0.9.7 natural-language instrument and fail-closed comparator checks."""
import unittest

from synthetic_ipseity.natural_witness import (
    CORPUS, PROTOCOL, MODEL_REPO, MODEL_FILE, MODEL_REVISION,
    QUESTIONS, ORDERS, choices, gold, grade, parse_answer,
    prompt, record, sealed_probes,
)
from synthetic_ipseity.source_truth_capacity import CASES as OLDER
from synthetic_ipseity.qwen_capacity import CASES as FIRST
from synthetic_ipseity.witness_reference import parse_witness_record
from tools.natural_witness_reference import evaluate


def fixture_rows(strategy="oracle"):
    result=[]
    for s in sealed_probes():
        a=s["expected"]
        if strategy=="always_agree":
            a="AGREE" if s["question"]=="relation" else "NO"
        elif strategy=="always_insufficient":
            a="INSUFFICIENT" if s["question"]=="relation" else "NO"
        elif strategy=="always_yes":
            a="AGREE" if s["question"]=="relation" else "YES"
        parsed=parse_answer(a,s["question"])
        result.append({
            **{k:s[k] for k in ("trial_id","record_sha256","expected")},
            **parsed
        })
    return result


class NaturalWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sealed=sealed_probes()

    def test_cases_are_fresh_balanced_and_independent_of_old_parser(self):
        self.assertIn("0.9.7",PROTOCOL)
        self.assertEqual(len(CORPUS),24)
        self.assertEqual(len({x.case_id for x in CORPUS}),24)
        ids={x.case_id for x in OLDER}|{x.case_id for x in FIRST}
        self.assertFalse(ids & {x.case_id for x in CORPUS})
        for label in ("AGREE","DISAGREE","INSUFFICIENT"):
            self.assertEqual(sum(x.relation_gold==label for x in CORPUS),8)
        self.assertEqual(sum(bool(x.independent_note) for x in CORPUS),8)
        self.assertEqual(len(ORDERS),2)
        self.assertEqual(len(QUESTIONS),2)

    def test_freeform_parser_must_abstain_and_not_reclassify_as_no_reports(self):
        baseline=evaluate()
        self.assertEqual(baseline["n_input_records"],48)
        self.assertEqual(baseline["coverage"],0)
        self.assertEqual(baseline["abstained"],48)
        for item in CORPUS:
            for order in ORDERS:
                p=parse_witness_record(record(item,order))
                self.assertFalse(p.valid,p)
                self.assertEqual(p.relation,"ABSTAIN")
                self.assertIsNone(p.direct_verified_state)

    def test_swapping_witnesses_preserves_gold_and_independent_note(self):
        for item in CORPUS:
            a=record(item,"original")
            b=record(item,"swapped")
            self.assertNotEqual(a,b)
            self.assertIn(item.a,a)
            self.assertIn(item.a,b)
            self.assertIn(item.b,a)
            self.assertIn(item.b,b)
            if item.independent_note:
                self.assertTrue(a.endswith(item.independent_note))
                self.assertTrue(b.endswith(item.independent_note))
            for q in QUESTIONS:
                self.assertEqual(gold(item,q),gold(item,q))

    def test_no_gold_or_case_id_in_model_prompt(self):
        self.assertEqual(len(self.sealed),96)
        self.assertEqual(len({x["trial_id"] for x in self.sealed}),96)
        for item in CORPUS:
            for order in ORDERS:
                for q in QUESTIONS:
                    p=prompt(item,order,q)
                    self.assertIn("ACCOUNTS:",p)
                    self.assertNotIn(item.case_id,p)
                    self.assertTrue(p.endswith("ANSWER:"))
                    self.assertIn(gold(item,q),choices(q))
                    self.assertEqual(p.count(item.a),1)
                    self.assertEqual(p.count(item.b),1)
        with self.assertRaises(ValueError):
            record(CORPUS[0],"third")
        with self.assertRaises(ValueError):
            prompt(CORPUS[0],"original","truth")

    def test_strict_vs_predefined_lenient_format(self):
        for q in QUESTIONS:
            for expected in choices(q):
                v=parse_answer(expected,q)
                self.assertTrue(v["strict_format"])
                self.assertTrue(v["lenient_format"])
                self.assertEqual(v["answer"],expected)
                v=parse_answer(expected+".",q)
                self.assertFalse(v["strict_format"])
                self.assertEqual(v["answer"],expected)
            for bad in ("", "Maybe", "I think AGREE", "yes", "AGREE because both", "UNKNOWN"):
                if bad not in choices(q):
                    self.assertIsNone(parse_answer(bad,q)["answer"])
        with self.assertRaises(TypeError):
            parse_answer(None,"relation")

    def test_gold_is_independent_of_verification_for_relation(self):
        assert all(x.relation_gold in choices("relation") for x in CORPUS)
        for item in CORPUS:
            self.assertEqual(gold(item,"independent_verification"),
                             "YES" if item.independent_note else "NO")
            self.assertEqual(gold(item,"relation"),item.relation_gold)

    def test_ideal_oracle_passes_all_gates_and_position_baselines_fail(self):
        report=grade(fixture_rows("oracle"))
        self.assertTrue(report["predeclared_qualification_passed"])
        for g in report["paired_counts"].values():
            self.assertEqual(g["correct"],g["total"])
        for strategy in ("always_agree","always_insufficient","always_yes"):
            with self.subTest(strategy=strategy):
                self.assertFalse(grade(fixture_rows(strategy))["predeclared_qualification_passed"])

    def test_missing_extra_duplicate_mutated_cases_are_not_imputed(self):
        rows=fixture_rows()
        for broken in (rows[:-1],rows+[rows[-1]]):
            with self.assertRaises(ValueError):
                grade(broken)
        rowset=fixture_rows()
        rowset[0]["record_sha256"]="tampered"
        with self.assertRaises(ValueError):
            grade(rowset)
        rowset=fixture_rows()
        rowset[0]["expected"]="WRONG"
        with self.assertRaises(ValueError):
            grade(rowset)

    def test_gate_requires_each_group_not_just_overall_accuracy(self):
        rows=fixture_rows()
        for r in rows:
            if r["trial_id"].startswith("N17:") and r["trial_id"].endswith(":relation"):
                r["answer"]="AGREE"
            if r["trial_id"].startswith("N18:") and r["trial_id"].endswith(":relation"):
                r["answer"]="AGREE"
            if r["trial_id"].startswith("N19:") and r["trial_id"].endswith(":relation"):
                r["answer"]="AGREE"
        result=grade(rows)
        self.assertFalse(result["predeclared_qualification_passed"])
        self.assertEqual(result["paired_counts"]["insufficient"]["correct"],5)


if __name__=="__main__":
    unittest.main()
