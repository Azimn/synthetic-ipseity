"""No-model v0.9.3 evidence-responsiveness contract tests."""
from dataclasses import replace
import unittest

from synthetic_ipseity.behavioral_pilot import CASES as SOURCE_CASES
from synthetic_ipseity.evidence_ablation import (
    ARMS,CASES,FIELDS,POLARITY_FIELDS,SCHEMA,NEUTRAL,
    ablation_questions,score_ablation,source_records,
)
from synthetic_ipseity.format_probe import question


def mock_rows(mode):
    rows=[]
    for q in ablation_questions():
        expected=next(s for s in SOURCE_CASES if s.case_id==q["case_id"])
        if q["origin"]=="reversed":
            expected=replace(expected,conflict=not expected.conflict)
        field=q["field"]
        target=expected.expected[field]
        if isinstance(target,bool):
            target="yes" if target else "no"
        letter=next(
            k for k,v in q["label_map"].items() if v==target
        )
        if mode=="position":
            letter="B"
        elif q["origin"]=="neutral":
            letter="A"
        rows.append({
            **{key:q[key] for key in ("case_id","arm","swap","field",
                                      "origin","label_map")},
            "predicted":letter,
        })
    return rows


class EvidenceAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions=ablation_questions()

    def test_reuse_previously_fixed_case_stems_and_arms(self):
        self.assertEqual(CASES,("C01","C02"))
        self.assertEqual(ARMS,("C","D"))
        self.assertEqual(len(FIELDS),6)
        self.assertEqual(len(POLARITY_FIELDS),5)
        self.assertIn("0.9.3",SCHEMA)
        self.assertEqual(len(self.questions),144)

    def test_source_reversal_keeps_topics_and_names_but_changes_polarity(self):
        for case in CASES:
            s=next(s for s in SOURCE_CASES if s.case_id==case)
            for arm in ARMS:
                texts=source_records(case,arm)
                self.assertEqual(set(texts),{"original","reversed","neutral"})
                self.assertNotEqual(texts["original"],texts["reversed"])
                for text in (texts["original"],texts["reversed"]):
                    self.assertIn(s.affirmative,text)
                    self.assertIn(s.speaker_a,text)
                    self.assertIn(s.speaker_b,text)
                self.assertNotIn(s.affirmative,texts["neutral"])
                self.assertNotIn(s.speaker_a,texts["neutral"])
                self.assertNotIn(s.topic,texts["neutral"])

    def test_answer_positions_never_change_with_evidence(self):
        for case in CASES:
            for arm in ARMS:
                for swap in (False,True):
                    for field in FIELDS:
                        subset=[r for r in self.questions
                            if r["case_id"]==case and r["arm"]==arm
                            and r["swap"]==swap and r["field"]==field]
                        self.assertEqual(len(subset),3)
                        self.assertEqual(
                            len({tuple(sorted(r["label_map"].items())) for r in subset}),
                            1,
                        )
                        self.assertEqual(
                            {r["origin"] for r in subset},
                            {"original","reversed","neutral"},
                        )

    def test_no_truth_is_imputed_to_neutral_context(self):
        self.assertIn("no testimony",NEUTRAL)
        for row in self.questions:
            if row["origin"]=="neutral":
                self.assertNotIn("correct_neutral",row)

    def test_ideal_evidence_sensitive_classifier_reverses_predictions(self):
        result=score_ablation(mock_rows("oracle"))
        self.assertEqual(result["n_real_classifications"],144)
        for stats in result["groups"].values():
            self.assertEqual(stats["original_accuracy"],1)
            self.assertEqual(stats["counterfactual_accuracy"],1)
            self.assertEqual(stats["correct_polarity_reversal_rate"],1)
            self.assertEqual(stats["polarity_flip_rate"],1)

    def test_position_only_predictor_cannot_pass_reversal_gate(self):
        result=score_ablation(mock_rows("position"))
        for stats in result["groups"].values():
            self.assertEqual(stats["polarity_flip_rate"],0)
            self.assertEqual(stats["correct_polarity_reversal_rate"],0)

    def test_missing_duplicate_and_invalid_choices_fail_closed(self):
        rows=mock_rows("oracle")
        with self.assertRaises(ValueError):
            score_ablation(rows[:-1])
        with self.assertRaises(ValueError):
            score_ablation(rows+[rows[-1]])
        rows[0]["predicted"]="Z"
        with self.assertRaises(ValueError):
            score_ablation(rows)

    def test_reverse_record_for_D_is_actual_organ_output(self):
        for case in CASES:
            text=source_records(case,"D")
            self.assertIn("I hear someone say:",text["original"])
            self.assertIn("I hear someone say:",text["reversed"])
            self.assertNotIn("host-private:",text["original"])
            self.assertNotIn("engineer-only",text["reversed"])


if __name__=="__main__":
    unittest.main()
