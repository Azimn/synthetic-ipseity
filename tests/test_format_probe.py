"""Instrument tests run without downloading any LLM or making API calls."""
import unittest
from synthetic_ipseity.behavioral_pilot import (
    SEED, sha256 as parent_sha, trial_manifest,
)
from synthetic_ipseity.format_probe import (
    ARMS, CASES, FIELDS, SCHEMA, OPTIONS, build_prompt,
    expected_for, grade_logits, parse_free_letter,
    question, select_trials, summarize,
)


class CalibratedMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = trial_manifest(seed=SEED, replicates=1)

    def test_locked_stems_no_new_after_seeing_failures(self):
        self.assertEqual(CASES, ("C01", "C02"))
        self.assertEqual(ARMS, ("C", "D"))
        self.assertEqual(len(FIELDS), 6)
        self.assertIn("0.9.2", SCHEMA)

    def test_every_field_has_grounded_truth_for_both_stems(self):
        for case in CASES:
            actual = expected_for(case)
            self.assertEqual(set(actual), set(FIELDS))
            for field in FIELDS:
                self.assertIn(actual[field], OPTIONS[field])
        self.assertEqual(expected_for("C01")["stance"], "suspends")
        self.assertEqual(expected_for("C02")["evidence"], "corroborating")
        self.assertEqual(expected_for("C01")["recalls_notice"], "yes")
        self.assertEqual(expected_for("C02")["recalls_notice"], "no")
        with self.assertRaises(ValueError):
            expected_for("C99")

    def test_pairwise_C_and_D_see_identical_option_permutation(self):
        for case in CASES:
            for swap in (False, True):
                for field in FIELDS:
                    q = question(case, field, swap=swap)
                    self.assertEqual(len(q.labels), len(OPTIONS[field]))
                    self.assertEqual(len(set(dict(q.labels).values())),
                                     len(OPTIONS[field]))
                    self.assertEqual(len(set(dict(q.labels))), len(q.labels))
                    self.assertEqual(q.label_map[q.correct_label],
                                     expected_for(case)[field])
                    self.assertIn(q.correct_label, ("A","B","C"))

    def test_answers_rotate_across_cases_and_dimensions(self):
        permutations = set()
        for field in FIELDS:
            for case in CASES:
                for swap in (False, True):
                    q = question(case, field, swap=swap)
                    permutations.add((field, tuple(q.label_map.values())))
        self.assertGreater(len(permutations), len(FIELDS))

    def test_question_never_embeds_expected_label_unintentionally(self):
        q = question("C01", "evidence", swap=True)
        msg = build_prompt("Someone heard two contradictory reports", q)
        self.assertIn("ONE multiple-choice question", msg)
        self.assertIn("CHARACTER RECORD:", msg)
        self.assertTrue(msg.endswith("Answer:"))
        self.assertIn("A.", msg)
        self.assertIn("B.", msg)
        self.assertNotIn("expected_for", msg)
        with self.assertRaises(ValueError):
            build_prompt("", q)

    def test_free_letter_format_is_separately_scored(self):
        q = question("C01", "stance", swap=False)
        self.assertTrue(parse_free_letter(q.correct_label, q)["format_valid"])
        self.assertTrue(parse_free_letter(" " + q.correct_label + "\n", q)["format_valid"])
        self.assertTrue(parse_free_letter("A", q)["format_valid"])
        for example in ("Answer: A", '{"stance":"suspends"}',
                        "AB", "the answer is C", "", "D", "a"):
            with self.subTest(example=example):
                outcome = parse_free_letter(example, q)
                self.assertFalse(outcome["format_valid"])
                self.assertIsNone(outcome["semantic_correct_if_valid"])

    def test_forced_choice_semantics_remain_scoreable_when_free_text_is_invalid(self):
        q = question("C02", "evidence", swap=True)
        logits = {label:(8.0 if label==q.correct_label else -1.0)
                  for label in q.label_map}
        graded = grade_logits(logits, q)
        self.assertTrue(graded["semantic_correct"])
        self.assertGreater(graded["margin_top_two"],0)
        self.assertFalse(parse_free_letter("not-json or letter",q)["format_valid"])

    def test_wrong_forced_choice_is_measured_not_discarded(self):
        q = question("C01", "next_action", swap=False)
        wrong = next(label for label in q.label_map if label != q.correct_label)
        logits = {label:(1.0 if label==wrong else 0.0)
                  for label in q.label_map}
        self.assertFalse(grade_logits(logits, q)["semantic_correct"])
        with self.assertRaises(ValueError):
            grade_logits({"A":2.0},q)
        with self.assertRaises(ValueError):
            grade_logits({key:float("nan") for key in q.label_map},q)

    def test_subset_matches_original_locked_pilot_without_rewriting_it(self):
        selected = select_trials(self.parent)
        self.assertEqual(len(selected), 8)
        self.assertEqual(len(set(x["trial_id"] for x in selected)), 8)
        self.assertTrue(all(t["block"] == "matched" for t in selected))
        altered = dict(self.parent)
        altered["trials"] = [x for x in self.parent["trials"]
                             if x["trial_id"] != "matched:C01:D:0:0"]
        with self.assertRaises(ValueError):
            select_trials(altered)

    @staticmethod
    def rows(correct: bool = True, valid: bool = False):
        rows = []
        for case in CASES:
            for arm in ARMS:
                for swap in (False,True):
                    for origin in ("handoff","direct"):
                        for field in FIELDS:
                            q = question(case,field,swap=swap)
                            pred = q.correct_label if correct else next(
                                x for x in q.label_map if x != q.correct_label
                            )
                            logits = {
                                k:(1.0 if k==pred else 0.0)
                                for k in q.label_map
                            }
                            rows.append({
                                "case_id":case,"arm":arm,"swap":swap,
                                "origin":origin,"field":field,
                                "forced":grade_logits(logits,q),
                                "free":parse_free_letter(pred if valid else "not letter",q),
                            })
        return rows

    def test_summary_handles_semantics_without_valid_generation(self):
        report = summarize(self.rows(correct=True,valid=False))
        self.assertEqual(report["n_probes"],96)
        self.assertEqual(
            report["groups"]["handoff:D:1"]["forced_choice_accuracy"],1.0
        )
        self.assertEqual(
            report["groups"]["handoff:D:1"]["letter_format_valid_rate"],0.0
        )
        self.assertEqual(
            report["groups"]["handoff:C:1"]["letter_accuracy_unconditional"],0.0
        )
        self.assertEqual(
            report["per_field_handoff"]["evidence"]["n"],8
        )

    def test_wrong_semantics_are_detected_even_when_format_is_valid(self):
        report = summarize(self.rows(correct=False,valid=True))
        self.assertEqual(
            report["groups"]["direct:C:0"]["forced_choice_accuracy"],0.0
        )
        self.assertEqual(
            report["groups"]["direct:C:0"]["letter_format_valid_rate"],1.0
        )
        self.assertEqual(
            report["groups"]["direct:C:0"]["letter_accuracy_unconditional"],0.0
        )

    def test_missing_and_duplicate_measurements_are_not_imputed(self):
        samples=self.rows()
        with self.assertRaises(ValueError):
            summarize(samples[:-1])
        with self.assertRaises(ValueError):
            summarize(samples+[samples[0]])


if __name__=="__main__":
    unittest.main()
