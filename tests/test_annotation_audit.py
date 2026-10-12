"""Review-packet tests use SYNTHETIC inputs, never claim a human annotated."""
from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from tools.annotation_audit import (
    PACKET_FIELDS, RELATION, REVIEW_FIELDS, SCHEMA, VERIFICATION,
    _kappa, generate, reviewer_packet, score,
)
from synthetic_ipseity.natural_witness import CORPUS, digest


def _fill_template(path: Path, *, modify_id: str | None = None,
                   missing: bool = False) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    if missing:
        rows.pop()
    for r in rows:
        r["relation_label"] = "DISAGREE" if r["blind_id"] == modify_id else "AGREE"
        r["independent_verification_label"] = "NO"
        r["confidence"] = "LOW"
        r["speaker_a_claim"] = "TEST FIXTURE ONLY — assertion A"
        r["speaker_b_claim"] = "TEST FIXTURE ONLY — assertion B"
        r["object_time_relation"] = "TEST FIXTURE ONLY — shared frame"
        r["verification_evidence_quote"] = ""
        r["annotation_reason"] = "SYNTHETIC UNIT TEST — not a human annotation"
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class ReviewPacketTests(unittest.TestCase):
    def test_one_record_per_case_no_model_predictions_or_gold(self):
        packet=reviewer_packet()
        self.assertEqual(len(packet),24)
        self.assertEqual(len({x["blind_id"] for x in packet}),24)
        self.assertEqual(len({x["record_sha256"] for x in packet}),24)
        self.assertEqual(set(packet[0]),set(PACKET_FIELDS))
        self.assertTrue(all("relation_gold" not in x for x in packet))
        self.assertTrue(all("case_id" not in x for x in packet))
        for p in packet:
            self.assertNotIn("original_author_relation_gold",repr(p))
            self.assertFalse(any(x in p["blind_id"] for x in ("N01","N09","N17")))
            self.assertNotIn("NATURAL WITNESS REAL SUMMARY",str(p))

    def test_packet_deterministic_and_balanced_order(self):
        self.assertEqual(reviewer_packet(),reviewer_packet())
        texts=[x["testimony"] for x in reviewer_packet()]
        firsts=sum(
            t.splitlines()[0] == item.a
            for item in CORPUS for t in texts if item.a in t and item.b in t
        )
        self.assertEqual(firsts,12)

    def test_generated_files_separate_private_alignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=generate(Path(tmp))
            self.assertEqual(manifest["schema"],SCHEMA)
            self.assertEqual(manifest["records"],24)
            self.assertIn("UNANNOTATED",manifest["status"])
            files=list(Path(tmp).iterdir())
            self.assertEqual(len(files),5)
            with (Path(tmp)/"reviewer_packet.csv").open(newline="",encoding="utf-8") as f:
                rows=list(csv.DictReader(f))
                self.assertEqual(len(rows),24)
                self.assertNotIn("relation_gold",f.readline())
            mapping=(Path(tmp)/"post_annotation_alignment_PRIVATE.json").read_text()
            self.assertIn("original_author_relation_gold",mapping)
            self.assertNotIn("original_author_relation_gold",
                             (Path(tmp)/"reviewer_packet.csv").read_text())
            with self.assertRaises(FileExistsError):
                generate(Path(tmp))

    def test_without_submitted_ratings_cannot_report_agreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(Path(tmp))
            with self.assertRaises(ValueError):
                score(Path(tmp)/"reviewer_1_blank.csv",
                      Path(tmp)/"reviewer_2_blank.csv")

    def test_agreement_only_on_two_complete_valid_submissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(Path(tmp))
            a=Path(tmp)/"reviewer_1_blank.csv"
            b=Path(tmp)/"reviewer_2_blank.csv"
            _fill_template(a)
            _fill_template(b)
            result=score(a,b)
            self.assertTrue(result["original_author_gold_not_used"])
            self.assertEqual(result["n_unique_cases"],24)
            for stats in result["metrics"].values():
                self.assertEqual(stats["raw_agreement"],1)
                self.assertEqual(stats["cohens_kappa"],1)
            self.assertEqual(result["disagreements"],[])
            self.assertIn("SYNTHETIC",a.read_text())

    def test_rater_disagreement_detected_not_silently_adjudicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(Path(tmp))
            a=Path(tmp)/"reviewer_1_blank.csv"
            b=Path(tmp)/"reviewer_2_blank.csv"
            _fill_template(a)
            _fill_template(b,modify_id=reviewer_packet()[0]["blind_id"])
            result=score(a,b)
            self.assertEqual(len(result["disagreements"]),1)
            self.assertLess(result["metrics"]["witness_relation"]["raw_agreement"],1)
            self.assertEqual(result["annotation_status"],
                             "agreement computed; adjudication not performed")

    def test_missing_or_tampered_hashes_are_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(Path(tmp))
            a=Path(tmp)/"reviewer_1_blank.csv"
            b=Path(tmp)/"reviewer_2_blank.csv"
            _fill_template(a)
            _fill_template(b,missing=True)
            with self.assertRaises(ValueError):
                score(a,b)
            _fill_template(b)
            text=b.read_text()
            b.write_text(text.replace(reviewer_packet()[0]["record_sha256"],"bogus"))
            with self.assertRaises(ValueError):
                score(a,b)

    def test_expected_kappa_behavior_and_zero_variance(self):
        self.assertEqual(_kappa(["AGREE"]*4,["AGREE"]*4,RELATION),1.0)
        self.assertLess(_kappa(["AGREE","DISAGREE"]*2,
                               ["DISAGREE","AGREE"]*2,RELATION),0)
        self.assertIsNone(_kappa(["AGREE"]*4,["DISAGREE"]*4,RELATION))
        self.assertIn("UNCLEAR",VERIFICATION)

if __name__=="__main__":
    unittest.main()
