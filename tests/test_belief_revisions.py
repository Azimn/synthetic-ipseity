"""Provisional belief revision extension to the merged v0.6 evidence ledger."""
from pathlib import Path
import sqlite3
import tempfile
import unittest

from synthetic_ipseity import (
    AccessPolicy, EpistemicClaim, EvidenceKind, Stance, render_frame,
)
from synthetic_ipseity.longitudinal import (
    BeliefPosition, ProvisionalBeliefRevision,
    EvidenceChange, LongitudinalEpistemicHost,
)


def report(ref="henry", stance=Stance.AFFIRMS, *, subject="alice",
           acquired=True, attested=True, key="door", topic="the western door"):
    return EpistemicClaim(
        subject, EvidenceKind.HEARD, "the door status", ref,
        acquired=acquired, attested=attested, claim_key=key,
        topic=topic, stance=stance,
    )


def judgment(position, sources, *, attested=True, reason="new evidence"):
    return ProvisionalBeliefRevision(
        "door", position, reason, tuple(sources), attested=attested,
    )


class BeliefRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "beliefs.db"
        self.host = self.open()

    def tearDown(self):
        self.host.close()
        self.temp.cleanup()

    def open(self, *, subject="alice", epoch="life-1"):
        return LongitudinalEpistemicHost(
            self.path, subject_id=subject, epoch_id=epoch,
            policy=AccessPolicy(capacity=6),
        )

    def test_provisional_stance_and_revision_do_not_rewrite_source_history(self):
        self.host.process_evidence(1, [report()], belief_revisions=[
            judgment(BeliefPosition.AFFIRMS, ["henry"], reason="first witness")
        ])
        initial = self.host.history_count()
        self.assertEqual(initial, 1)
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.AFFIRMS)
        self.host.process_evidence(2, [report("morgan", Stance.DENIES)],
            belief_revisions=[
                judgment(BeliefPosition.SUSPENDS, ["henry", "morgan"],
                         reason="independent disagreement"),
            ])
        self.assertEqual(self.host.history_count(), initial + 1)
        self.assertTrue(self.host.status("door").conflict)
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.SUSPENDS)
        log = self.host.belief_revisions("door")
        self.assertEqual(len(log), 2)
        self.assertIsNone(log[0].previous)
        self.assertEqual(log[1].previous, BeliefPosition.AFFIRMS)
        self.assertEqual(log[1].current, BeliefPosition.SUSPENDS)
        self.assertEqual(log[0].reason, "first witness")
        self.host.close()
        self.host = self.open()
        self.assertEqual(self.host.belief_revisions("door"), log)

    def test_provisional_stance_does_not_make_conflict_disappear(self):
        self.host.process_evidence(
            1, [report("A"), report("B", Stance.DENIES)],
            belief_revisions=[judgment(BeliefPosition.DENIES, ["B"])],
        )
        self.assertTrue(self.host.status("door").conflict)
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.DENIES)

    def test_invalid_revision_does_not_advance_cursor(self):
        before = self.host.checkpoint()
        with self.assertRaises(ValueError):
            self.host.process_evidence(
                1, [report()],
                belief_revisions=[judgment(BeliefPosition.DENIES, ["henry"])],
            )
        self.assertEqual(self.host.checkpoint(), before)
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.pending_count(), 0)

    def test_revision_requires_host_authorization(self):
        with self.assertRaises(ValueError):
            self.host.process_evidence(
                1, [report()],
                belief_revisions=[judgment(
                    BeliefPosition.AFFIRMS, ["henry"], attested=False
                )],
            )
        self.assertEqual(self.host.history_count(), 0)

    def test_revision_must_cite_active_source(self):
        self.host.process_evidence(1, [report("A")])
        with self.assertRaises(ValueError):
            self.host.process_evidence(
                2, [], belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["hidden"])]
            )
        self.assertEqual(self.host.checkpoint().last_tick, 1)

    def test_withdrawn_source_cannot_support_new_position(self):
        self.host.process_evidence(1, [report("A")])
        self.host.process_evidence(2, [EvidenceChange(
            "alice", "A", "door", "the western door", acquired=True, attested=True,
        )])
        with self.assertRaises(ValueError):
            self.host.process_evidence(
                3, [], belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["A"])]
            )
        self.assertIsNone(self.host.belief_position("door"))

    def test_unattested_evidence_cannot_support_revision(self):
        with self.assertRaises(ValueError):
            self.host.process_evidence(
                1, [report(acquired=True, attested=False)],
                belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["henry"])],
            )
        self.assertEqual(self.host.history_count(), 0)

    def test_retraction_and_position_change_share_atomic_commit(self):
        self.host.process_evidence(
            1, [report("A"), report("B", Stance.DENIES)],
            belief_revisions=[judgment(BeliefPosition.SUSPENDS, ["A", "B"])],
        )
        self.host.process_evidence(
            2, [EvidenceChange(
                "alice", "B", "door", "the western door",
                attested=True, acquired=True,
            )],
            belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["A"],
                                       reason="other witness retracted")],
        )
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.AFFIRMS)
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.history_count(), 3)

    def test_after_ledger_fault_rolls_back_evidence_and_revision(self):
        with self.assertRaisesRegex(RuntimeError, "after ledger"):
            self.host.process_evidence(
                1, [report()],
                belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["henry"])],
                fault="after_ledger",
            )
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.belief_revisions("door"), ())
        self.assertEqual(self.host.checkpoint().last_sequence, 0)

    def test_before_commit_fault_rolls_back_revision_and_subject_output(self):
        with self.assertRaisesRegex(RuntimeError, "before commit"):
            self.host.process_evidence(
                1, [report()],
                belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["henry"])],
                fault="before_commit",
            )
        self.host.close()
        self.host = self.open()
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.belief_revisions("door"), ())
        self.assertEqual(self.host.pending_count(), 0)

    def test_after_commit_uncertain_result_recovers_position(self):
        with self.assertRaisesRegex(RuntimeError, "after durable commit"):
            self.host.process_evidence(
                1, [report()],
                belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["henry"])],
                fault="after_commit",
            )
        self.host.close()
        self.host = self.open()
        self.assertEqual(self.host.history_count(), 1)
        self.assertEqual(self.host.checkpoint().last_sequence, 1)
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.AFFIRMS)

    def test_revision_only_tick_has_no_forced_narration(self):
        self.host.process_evidence(1, [report()])
        pending = self.host.pending_count()
        old = self.host.checkpoint()
        result = self.host.process_evidence(
            2, [], belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["henry"])]
        )
        self.assertIsNone(result.cursor.outbox_id)
        self.assertEqual(self.host.pending_count(), pending)
        self.assertEqual(self.host.checkpoint().last_tick, 2)
        self.assertEqual(self.host.checkpoint().last_sequence, old.last_sequence)

    def test_invalid_duplicate_revision_does_not_mutate_history(self):
        self.host.process_evidence(
            1, [report()], belief_revisions=[
                judgment(BeliefPosition.AFFIRMS, ["henry"]),
            ]
        )
        with self.assertRaises(ValueError):
            self.host.process_evidence(
                2, [], belief_revisions=[judgment(
                    BeliefPosition.AFFIRMS, ["henry"]
                )],
            )
        self.assertEqual(len(self.host.belief_revisions("door")), 1)
        self.assertEqual(self.host.checkpoint().last_tick, 1)

    def test_same_claim_key_cannot_be_revised_twice_per_tick(self):
        with self.assertRaises(ValueError):
            self.host.process_evidence(1, [report()], belief_revisions=[
                judgment(BeliefPosition.AFFIRMS, ["henry"]),
                judgment(BeliefPosition.SUSPENDS, ["henry"]),
            ])
        self.assertEqual(self.host.history_count(), 0)

    def test_cross_subject_and_epoch_positions_are_isolated(self):
        self.host.process_evidence(1, [report()],
            belief_revisions=[judgment(BeliefPosition.AFFIRMS, ["henry"])])
        with self.open(subject="bob") as other:
            self.assertIsNone(other.belief_position("door"))
            self.assertEqual(other.belief_revisions("door"), ())
        with self.open(epoch="later") as later:
            self.assertIsNone(later.belief_position("door"))
            self.assertEqual(later.belief_revisions("door"), ())

    def test_ledger_positions_are_not_renderer_frames(self):
        self.host.process_evidence(
            1, [report()], belief_revisions=[
                judgment(BeliefPosition.AFFIRMS, ["henry"]),
            ]
        )
        for obj in (self.host.belief_position("door"),
                    self.host.belief_revisions("door"),
                    self.host):
            with self.assertRaises(TypeError):
                render_frame(obj)

    def test_old_v06_schema_migrates_without_losing_history(self):
        self.host.process_evidence(1, [report()])
        before = self.host.history_count()
        self.host.close()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE epistemic_meta SET ledger_schema=1")
        self.host = self.open()
        self.assertEqual(self.host.history_count(), before)
        self.assertIsNone(self.host.belief_position("door"))
        with sqlite3.connect(self.path) as db:
            ver = db.execute("SELECT ledger_schema FROM epistemic_meta "
                             "WHERE subject_id='alice'").fetchone()[0]
            self.assertEqual(ver, 2)

    def test_new_schema_rejects_unknown_version(self):
        self.host.close()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE epistemic_meta SET ledger_schema=999")
        with self.assertRaises(ValueError):
            self.open()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE epistemic_meta SET ledger_schema=2")
        self.host = self.open()

    def test_revision_input_contract(self):
        with self.assertRaises(TypeError):
            judgment("affirms", ["henry"])
        with self.assertRaises(ValueError):
            judgment(BeliefPosition.AFFIRMS, [])
        with self.assertRaises(ValueError):
            judgment(BeliefPosition.AFFIRMS, ["henry", "henry"])
        with self.assertRaises(TypeError):
            ProvisionalBeliefRevision("door", BeliefPosition.AFFIRMS,
                                     "reason", ("henry",), attested="yes")


if __name__ == "__main__":
    unittest.main()
