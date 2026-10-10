"""Contract checks for a real-inference smoke; never call models in unit CI."""
import unittest

from synthetic_ipseity.behavioral_pilot import (
    PROTOCOL, SEED, trial_manifest,
)
from tools.cpu_model_smoke import (
    CASES, ARMS, MODELS, SMOKE_VERSION, choose_trials,
)


class ActualModelSmokeSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = trial_manifest(seed=SEED, replicates=1)

    def test_smoke_uses_two_fixed_balanced_cases_and_real_model_ids(self):
        self.assertEqual(CASES, ("C01", "C02"))
        self.assertEqual(ARMS, ("C", "D"))
        self.assertEqual(len(MODELS), 2)
        self.assertNotEqual(MODELS[0], MODELS[1])
        self.assertIn("cpu-smoke", SMOKE_VERSION)
        self.assertEqual(self.parent["protocol"], PROTOCOL)

    def test_all_paired_c_d_same_swap_cases_are_present(self):
        chosen = choose_trials(self.parent)
        self.assertEqual(len(chosen), 8)
        ids = [x["trial_id"] for x in chosen]
        self.assertEqual(len(set(ids)), 8)
        for case_id in CASES:
            for swap in (True, False):
                self.assertEqual(
                    {x["arm"] for x in chosen
                     if x["case_id"] == case_id and x["swap"] == swap},
                    {"C", "D"},
                )

    def test_smoke_does_not_mix_deliberately_unmatched_boundary_block(self):
        for trial in choose_trials(self.parent):
            self.assertEqual(trial["block"], "matched")
            self.assertNotIn("ENGINEER_ONLY_DIAGNOSTIC", trial["prompt"])
            self.assertIn("ONLY JSON", trial["prompt"])

    def test_real_smoke_selection_preserves_parent_order_and_hashes(self):
        selected = choose_trials(self.parent)
        expected = [
            t for t in self.parent["trials"]
            if t["block"] == "matched"
            and t["case_id"] in CASES and t["arm"] in ARMS
        ]
        self.assertEqual(selected, expected)
        self.assertTrue(all("exposure_sha256" in t for t in selected))

    def test_incomplete_selection_fails_closed(self):
        partial = dict(self.parent)
        partial["trials"] = [
            x for x in self.parent["trials"]
            if x["trial_id"] != "matched:C01:D:0:1"
        ]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            choose_trials(partial)


if __name__ == "__main__":
    unittest.main()
