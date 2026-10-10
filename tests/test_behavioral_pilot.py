"""Design and measurement integrity tests, NOT an empirical result."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from synthetic_ipseity.behavioral_pilot import (
    ARMS, CASES, FIELDS, PROTOCOL, SEED, boundary_prompt, canonical,
    evaluate, matched_lines, organ_transcript, phase_one, phase_two,
    score, sha256, trial_manifest,
)
from tools.continuity_benchmark import (
    read_manifest, simulated_rows, save_new, rows_to_jsonl, main,
)


class BehavioralPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # This really executes the v0.8 organ for all 12 synthetic subjects.
        cls.manifest = trial_manifest(seed=SEED, replicates=1)

    def test_scenario_count_and_conflict_balance(self):
        self.assertEqual(len(CASES), 12)
        self.assertEqual(len({s.case_id for s in CASES}), 12)
        self.assertEqual(sum(s.conflict for s in CASES), 6)
        self.assertEqual(sum(not s.conflict for s in CASES), 6)

    def test_each_arm_gets_same_acquired_statements_in_matched_block(self):
        for s in CASES:
            with self.subTest(case=s.case_id):
                for arm in ARMS:
                    text = "\n".join(matched_lines(s, arm))
                    self.assertIn(s.affirmative, text)
                    self.assertIn(s.second_statement, text)
                    self.assertIn(s.speaker_a, text)
                    self.assertIn(s.speaker_b, text)
                    self.assertIn(s.topic, text)
                    self.assertNotIn(s.sentinel, text)
                    self.assertNotIn("host-private:", text)
                    self.assertNotIn("engineer-only revision rationale", text)

    def test_full_organ_true_trace_has_no_automatic_reconsideration_without_change(self):
        for s in CASES:
            text = "\n".join(organ_transcript(s))
            self.assertEqual("recall having noticed" in text, s.conflict)
            self.assertEqual("no longer certain" in text, s.conflict)
            self.assertEqual("conflicting indications" in text, s.conflict)

    def test_experiment_is_paired_across_arms_swaps_and_conditions(self):
        expected = 12 * 4 * (2 + 1)
        self.assertEqual(len(self.manifest["trials"]), expected)
        ids = [t["trial_id"] for t in self.manifest["trials"]]
        self.assertEqual(len(ids), len(set(ids)))
        for s in CASES:
            for swap in (False, True):
                subset = [
                    t for t in self.manifest["trials"]
                    if t["case_id"] == s.case_id and t["block"] == "matched"
                    and t["swap"] is swap
                ]
                self.assertEqual({t["arm"] for t in subset}, set(ARMS))
                for t in subset:
                    self.assertEqual(t["expected"], s.expected)

    def test_manifest_is_immutable_sha_and_deterministic(self):
        a = self.manifest
        b = trial_manifest(seed=SEED, replicates=1)
        self.assertEqual(a, b)
        signed = {k: v for k, v in a.items() if k != "manifest_sha256"}
        self.assertEqual(a["manifest_sha256"], sha256(signed))
        self.assertEqual(a["protocol"], PROTOCOL)

    def test_seed_changes_order_not_case_definitions(self):
        different = trial_manifest(seed=SEED + 1, replicates=1)
        self.assertNotEqual(
            [t["trial_id"] for t in different["trials"]],
            [t["trial_id"] for t in self.manifest["trials"]],
        )
        self.assertEqual(
            {t["trial_id"] for t in different["trials"]},
            {t["trial_id"] for t in self.manifest["trials"]},
        )

    def test_no_privileged_context_leaks_except_deliberately_unmatched_A(self):
        for t in self.manifest["trials"]:
            s = next(s for s in CASES if s.case_id == t["case_id"])
            if t["block"] == "matched" or t["arm"] != "A":
                self.assertNotIn(s.sentinel, t["prompt"])
            else:
                self.assertIn(s.sentinel, t["prompt"])
            self.assertNotIn("host-private:", t["prompt"])

    def test_boundary_prompt_is_not_pooled_into_behavioral_metric(self):
        rows = simulated_rows(self.manifest, strategy="leaky")
        report = evaluate(self.manifest, rows, bootstrap_samples=100)
        self.assertEqual(
            report["summary"]["boundary:A:0"]["sentinel_leak_rate"], 1.0
        )
        self.assertEqual(
            report["summary"]["boundary:D:0"]["sentinel_leak_rate"], 0.0
        )
        self.assertNotIn("mean_score", report["summary"]["boundary:A:0"])
        self.assertEqual(
            report["summary"]["matched:D:0"]["mean_score"], 1.0
        )

    def test_oracle_simulation_reports_zero_effect_not_fabricated_improvement(self):
        report = evaluate(
            self.manifest, simulated_rows(self.manifest, strategy="oracle"),
            bootstrap_samples=150,
        )
        for stats in report["paired_contrasts"].values():
            self.assertEqual(stats["mean_difference"], 0.0)
            self.assertEqual(stats["bootstrap_ci95"], [0.0, 0.0])
            self.assertEqual(stats["n_independent_cases"], 12)

    def test_failed_json_is_included_in_denominator(self):
        rows = simulated_rows(self.manifest, strategy="bad")
        report = evaluate(self.manifest, rows, bootstrap_samples=100)
        self.assertEqual(report["summary"]["matched:D:1"]["mean_score"], 0.0)
        self.assertEqual(report["summary"]["matched:D:1"]["valid_rate"], 0.0)
        self.assertEqual(report["summary"]["matched:C:1"]["valid_rate"], 0.0)

    def test_undisclosed_missing_trial_cannot_be_imputed(self):
        rows = simulated_rows(self.manifest, strategy="oracle")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            evaluate(self.manifest, rows[:-1], bootstrap_samples=100)

    def test_duplicate_trial_and_manifest_mismatch_rejected(self):
        rows = simulated_rows(self.manifest, strategy="oracle")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluate(self.manifest, rows + [rows[0]], bootstrap_samples=100)
        rows[0]["manifest_sha256"] = "mismatched"
        with self.assertRaisesRegex(ValueError, "do not match"):
            evaluate(self.manifest, rows, bootstrap_samples=100)

    def test_score_enforces_allowed_values_and_schema(self):
        trial = next(t for t in self.manifest["trials"] if t["block"] == "matched")
        self.assertFalse(score(trial, "I was uncertain")["valid"])
        self.assertFalse(score(trial, '{}')["valid"])
        self.assertFalse(score(trial, canonical({
            **trial["expected"], "recalls_notice": "yes",
        }))["valid"])
        self.assertFalse(score(trial, canonical({
            **trial["expected"], "new_key": "hidden",
        }))["valid"])

    def test_one_mistake_reduces_score_by_exactly_one_sixth(self):
        trial = next(
            t for t in self.manifest["trials"]
            if t["block"] == "matched" and t["expected"]["stance"] == "suspends"
        )
        response = dict(trial["expected"])
        response["stance"] = "affirms"
        scored = score(trial, canonical(response))
        self.assertTrue(scored["valid"])
        self.assertEqual(scored["items_correct"], 5)
        self.assertAlmostEqual(scored["score"], 5 / 6)

    def test_full_organ_equivalent_to_C_proves_no_design_wins_baked_in(self):
        # CI scoring never calls a model. This deliberate fixture gives C
        # and D the same answers, so the paired effect must be zero.
        rows = simulated_rows(self.manifest, strategy="oracle")
        by_id = {r["trial_id"]: r for r in rows}
        for s in CASES:
            for swap in (False, True):
                for arm in ("C", "D"):
                    self.assertEqual(
                        by_id[f"matched:{s.case_id}:{arm}:0:{int(swap)}"]["response"],
                        canonical(s.expected),
                    )
        self.assertEqual(
            evaluate(self.manifest, rows, bootstrap_samples=100)
            ["paired_contrasts"]["D_minus_C_swap_1"]["mean_difference"], 0.0,
        )

    def test_true_model_swap_requires_second_model_for_phase_two(self):
        from tools.continuity_benchmark import model_rows
        tiny = {
            "seed": SEED, "manifest_sha256": self.manifest["manifest_sha256"],
            "trials": [next(t for t in self.manifest["trials"]
                            if t["block"] == "matched" and t["swap"])],
        }
        calls = []
        def fake_query(prompt, model, **kwargs):
            calls.append(model)
            return canonical(tiny["trials"][0]["expected"]), {"eval_count": 6}
        with patch("tools.continuity_benchmark.query_ollama", fake_query):
            result = model_rows(
                tiny, model_a="local-A", model_b="local-B",
                temperature=0, timeout=1, limit=None,
            )
        self.assertEqual(calls, ["local-A", "local-B"])
        self.assertEqual(result[0]["run_kind"], "local_ollama")

    def test_same_model_control_makes_same_number_of_calls(self):
        from tools.continuity_benchmark import model_rows
        tiny = {
            "seed": SEED, "manifest_sha256": self.manifest["manifest_sha256"],
            "trials": [next(t for t in self.manifest["trials"]
                            if t["block"] == "matched" and not t["swap"])],
        }
        calls = []
        def fake_query(prompt, model, **kwargs):
            calls.append(model)
            return canonical(tiny["trials"][0]["expected"]), {}
        with patch("tools.continuity_benchmark.query_ollama", fake_query):
            model_rows(tiny, model_a="local-A", model_b="local-B",
                       temperature=0, timeout=1, limit=None)
        self.assertEqual(calls, ["local-A", "local-A"])

    def test_cli_prepare_simulate_evaluate_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            predictions = Path(tmp) / "predictions.jsonl"
            report = Path(tmp) / "report.json"
            main(["prepare", "--out", str(manifest)])
            main(["simulate", "--manifest", str(manifest),
                  "--out", str(predictions)])
            main(["evaluate", "--manifest", str(manifest),
                  "--responses", str(predictions), "--out", str(report)])
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(data["empirical_model_run"])
            self.assertEqual(data["n_trials"], len(self.manifest["trials"]))
            self.assertEqual(
                data["paired_contrasts"]["D_minus_C_swap_0"]["mean_difference"],
                0.0,
            )
            self.assertIn("DIAGNOSTIC ONLY", data["interpretation"])
            with self.assertRaises(FileExistsError):
                main(["prepare", "--out", str(manifest)])

    def test_tampered_manifest_is_rejected_even_if_trial_ids_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            save_new(path, canonical(self.manifest))
            original = read_manifest(path)
            original["trials"][0]["prompt"] = "tampered"
            path.write_text(canonical(original), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "integrity mismatch"):
                read_manifest(path)

    def test_invalid_replication_and_seeds_fail(self):
        for kwargs in ({"replicates": 0}, {"replicates": True},
                       {"replicates": 11}, {"seed": -1}, {"seed": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                trial_manifest(**kwargs)

    def test_matched_record_not_exposed_to_second_renderer_except_via_handoff(self):
        same = phase_two('{"stance":"suspends"}')
        self.assertIn("suspends", same)
        self.assertNotIn("Henry", same)
        self.assertNotIn("ENGINEER_ONLY", same)
        self.assertEqual(len(FIELDS), 6)


if __name__ == "__main__":
    unittest.main()
