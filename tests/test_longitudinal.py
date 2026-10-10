"""Tests for longitudinal evidence, retractions and transactional restarts."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from synthetic_ipseity import (
    AccessPolicy, EvidenceKind, EpistemicClaim, Stance,
)
from synthetic_ipseity.longitudinal import (
    ChangeKind, EvidenceChange, LongitudinalEpistemicHost,
)


def claim(source="a", stance=Stance.AFFIRMS, *,
          topic="the brass door", key="door", subject="alice",
          acquired=True, attested=True, kind=EvidenceKind.HEARD,
          lived_verified=False, salience=0.8):
    return EpistemicClaim(
        subject_id=subject, kind=kind,
        text=f"the report of {topic}",
        source_ref=source, acquired=acquired, attested=attested,
        claim_key=key, topic=topic, stance=stance,
        lived_verified=lived_verified, salience=salience,
    )


def withdraw(source="a", *, key="door", topic="the brass door",
             subject="alice", acquired=True, attested=True):
    return EvidenceChange(
        subject_id=subject, source_ref=source, claim_key=key,
        topic=topic, operation=ChangeKind.RETRACT,
        acquired=acquired, attested=attested,
    )


class LedgerHostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "subject.db"
        self.host = self.open()

    def tearDown(self):
        self.host.close()
        self.tmp.cleanup()

    def open(self, subject="alice", epoch="life-1", *, policy=None):
        return LongitudinalEpistemicHost(
            self.db, subject_id=subject, epoch_id=epoch,
            policy=policy or AccessPolicy(capacity=8),
        )

    def reopen(self):
        self.host.close()
        self.host = self.open()
        return self.host

    def deliver(self, now=100):
        lease = self.host.claim_next(now_ms=now)
        self.assertIsNotNone(lease)
        text = self.host.read_subject_text(lease)
        self.host.ack_delivery(lease)
        return text

    def test_single_source_does_not_imply_truth(self):
        receipt = self.host.process_evidence(1, [claim()])
        self.assertEqual(receipt.history_added, 1)
        self.assertEqual(receipt.derived_transitions, ())
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.status("door").affirming_sources, 1)
        self.assertEqual(self.host.status("door").denying_sources, 0)
        self.assertIn("the report", self.deliver())
        self.assertEqual(self.host.history_count(), 1)

    def test_conflict_survives_restart_across_separate_days(self):
        self.host.process_evidence(1, [claim("Henry")])
        self.deliver()
        self.reopen()
        receipt = self.host.process_evidence(100, [
            claim("Morgan", Stance.DENIES),
        ])
        self.assertEqual(receipt.derived_transitions, ("conflict_opened",))
        self.assertEqual(receipt.cursor.last_sequence, 3)
        self.assertTrue(self.host.status("door").conflict)
        self.assertEqual(self.host.history_count(), 2)
        self.reopen()
        text = self.deliver()
        self.assertIn("conflicting indications", text)
        self.assertIn("cannot yet tell which is right", text)
        self.assertNotIn("ledger:", text)
        self.assertNotIn("Henry", text)  # source_refs are audit-only
        self.assertNotIn("Morgan", text)
        self.assertTrue(self.host.status("door").conflict)

    def test_conflict_does_not_repeat_without_transition(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        self.host.process_evidence(2, [claim("B", Stance.DENIES)])
        self.deliver()
        continued = self.host.process_evidence(3, [
            claim("C", Stance.DENIES),
        ])
        self.assertEqual(continued.derived_transitions, ())
        self.assertEqual(self.host.status("door").denying_sources, 2)
        self.assertNotIn("conflicting indications", self.deliver())

    def test_same_source_revision_not_independent_confirmation(self):
        self.host.process_evidence(1, [claim("single")])
        self.deliver()
        receipt = self.host.process_evidence(
            2, [claim("single", Stance.DENIES)]
        )
        self.assertEqual(receipt.derived_transitions, ("source_revised",))
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.status("door").affirming_sources, 0)
        self.assertEqual(self.host.status("door").denying_sources, 1)
        self.assertEqual(self.host.history_count(), 2)
        self.assertIn("changed account", self.deliver())

    def test_retraction_ceases_conflict_without_claiming_truth(self):
        self.host.process_evidence(1, [
            claim("A"), claim("B", Stance.DENIES),
        ])
        self.deliver()
        self.reopen()
        receipt = self.host.process_evidence(2, [withdraw("B")])
        self.assertEqual(receipt.derived_transitions, ("conflict_ceased",))
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.status("door").affirming_sources, 1)
        self.assertEqual(self.host.status("door").denying_sources, 0)
        self.assertEqual(self.host.history_count(), 3)
        self.reopen()
        text = self.deliver()
        self.assertIn("was withdrawn", text)
        self.assertIn("no longer conflict", text)
        self.assertIn("does not prove", text)

    def test_retraction_keeps_historical_account(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        self.host.process_evidence(2, [withdraw("A")])
        self.deliver()
        self.assertEqual(self.host.history_count(), 2)
        self.assertEqual(self.host.status("door").affirming_sources, 0)
        with sqlite3.connect(self.db) as conn:
            rows = conn.execute(
                "SELECT operation, stance FROM epistemic_history ORDER BY id"
            ).fetchall()
        self.assertEqual(rows, [("assert", "affirms"), ("retract", None)])

    def test_retraction_unknown_source_fails_atomically(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        with self.assertRaises(ValueError):
            self.host.process_evidence(2, [withdraw("never-seen")])
        self.assertEqual(self.host.history_count(), 1)
        self.assertEqual(self.host.checkpoint().last_tick, 1)
        self.assertEqual(self.host.pending_count(), 0)

    def test_unattested_retraction_does_not_delete_evidence(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        receipt = self.host.process_evidence(
            2, [withdraw("A", attested=False)]
        )
        self.assertEqual(receipt.history_added, 0)
        self.assertEqual(self.host.status("door").affirming_sources, 1)
        self.assertEqual(self.host.history_count(), 1)
        self.assertEqual(self.host.pending_count(), 0)

    def test_unacquired_retraction_does_not_delete_evidence(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        receipt = self.host.process_evidence(
            2, [withdraw("A", acquired=False)]
        )
        self.assertEqual(receipt.history_added, 0)
        self.assertEqual(self.host.status("door").affirming_sources, 1)
        self.assertEqual(self.host.pending_count(), 0)

    def test_unattested_claim_cannot_create_later_conflict(self):
        self.host.process_evidence(1, [claim("A", attested=False)])
        self.host.process_evidence(2, [claim("B", Stance.DENIES)])
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.history_count(), 1)
        self.assertNotIn("conflicting indications", self.deliver())

    def test_unacquired_claim_cannot_create_later_conflict(self):
        self.host.process_evidence(1, [claim("A", acquired=False)])
        self.host.process_evidence(2, [claim("B", Stance.DENIES)])
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.history_count(), 1)

    def test_unverified_recollection_is_not_active_support(self):
        self.host.process_evidence(1, [claim(
            "A", kind=EvidenceKind.LIVED_RECALL, lived_verified=False,
        )])
        self.deliver()
        self.host.process_evidence(2, [claim("B", Stance.DENIES)])
        self.assertEqual(self.host.history_count(), 1)
        self.assertFalse(self.host.status("door").conflict)
        self.assertEqual(self.host.status("door").denying_sources, 1)

    def test_verified_lived_memory_can_count_but_not_become_truth(self):
        self.host.process_evidence(1, [claim(
            "A", kind=EvidenceKind.LIVED_RECALL, lived_verified=True,
        )])
        self.deliver()
        self.host.process_evidence(2, [claim("B", Stance.DENIES)])
        self.assertEqual(self.host.history_count(), 2)
        self.assertTrue(self.host.status("door").conflict)

    def test_same_key_different_topic_fails_across_restoration(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        self.reopen()
        with self.assertRaises(ValueError):
            self.host.process_evidence(2, [
                claim("B", topic="the red chair"),
            ])
        self.assertEqual(self.host.checkpoint().last_tick, 1)
        self.assertEqual(self.host.history_count(), 1)

    def test_duplicate_source_repeat_is_not_new_confirmation(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        self.host.process_evidence(2, [claim("A")])
        self.assertEqual(self.host.status("door").affirming_sources, 1)
        self.assertEqual(self.host.history_count(), 2)

    def test_all_at_once_conflict_detected_once(self):
        receipt = self.host.process_evidence(1, [
            claim("A"), claim("B", Stance.DENIES),
        ])
        self.assertEqual(receipt.derived_transitions, ("conflict_opened",))
        self.assertEqual(receipt.cursor.last_sequence, 3)
        text = self.deliver()
        self.assertEqual(text.count("conflicting indications"), 1)

    def test_two_topics_remain_independent(self):
        self.host.process_evidence(1, [
            claim("A"), claim("Z", Stance.DENIES, topic="the green lamp", key="lamp"),
        ])
        self.deliver()
        r = self.host.process_evidence(2, [
            claim("B", Stance.DENIES),
            claim("Y", Stance.AFFIRMS, topic="the green lamp", key="lamp"),
        ])
        self.assertEqual(r.derived_transitions, (
            "conflict_opened", "conflict_opened",
        ))
        self.assertTrue(self.host.status("door").conflict)
        self.assertTrue(self.host.status("lamp").conflict)
        self.assertEqual(r.cursor.last_sequence, 6)

    def test_no_delivered_source_identifiers(self):
        self.host.process_evidence(1, [
            claim("secret-source-A"), claim("secret-source-B", Stance.DENIES),
        ])
        text = self.deliver()
        self.assertNotIn("secret-source-A", text)
        self.assertNotIn("secret-source-B", text)
        self.assertNotIn("claim_key", text)
        self.assertNotIn("raw_value", text)

    def test_history_is_separate_from_subject_outbox(self):
        self.host.process_evidence(1, [claim("source:alpha")])
        with sqlite3.connect(self.db) as conn:
            outbox = conn.execute(
                "SELECT subject_lines_json FROM outbox"
            ).fetchone()[0]
            evidence = conn.execute(
                "SELECT source_ref FROM epistemic_history"
            ).fetchone()[0]
        self.assertNotIn("source:alpha", outbox)
        self.assertEqual(evidence, "source:alpha")

    def test_cross_subject_isolation_even_when_db_is_shared(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        other = self.open(subject="bob")
        try:
            self.assertEqual(other.history_count(), 0)
            self.assertIsNone(other.status("door").topic)
            other.process_evidence(1, [claim(
                "C", subject="bob", stance=Stance.DENIES,
            )])
            self.assertFalse(other.status("door").conflict)
            self.assertEqual(other.history_count(), 1)
            self.assertEqual(self.host.history_count(), 1)
        finally:
            other.close()

    def test_epoch_isolation_on_same_database(self):
        self.host.process_evidence(1, [claim("A")])
        self.deliver()
        epoch = self.open(epoch="life-2")
        try:
            self.assertEqual(epoch.history_count(), 0)
            self.assertIsNone(epoch.status("door").topic)
        finally:
            epoch.close()

    def test_empty_tick_is_persisted(self):
        self.host.process_evidence(1, [])
        self.assertEqual(self.host.checkpoint().last_tick, 1)
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.pending_count(), 0)

    def test_fault_after_ledger_rolls_back_everything(self):
        with self.assertRaisesRegex(RuntimeError, "after ledger"):
            self.host.process_evidence(1, [claim("A")], fault="after_ledger")
        self.reopen()
        self.assertEqual(self.host.history_count(), 0)
        self.assertIsNone(self.host.status("door").topic)
        self.assertEqual(self.host.checkpoint().last_sequence, 0)
        self.assertEqual(self.host.pending_count(), 0)
        self.host.process_evidence(1, [claim("A")])

    def test_fault_before_commit_rolls_back_cursor_and_ledger(self):
        with self.assertRaisesRegex(RuntimeError, "before commit"):
            self.host.process_evidence(1, [claim("A")], fault="before_commit")
        self.reopen()
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.checkpoint().last_tick, -1)
        self.assertEqual(self.host.pending_count(), 0)

    def test_fault_after_commit_leaves_recoverable_experience(self):
        with self.assertRaisesRegex(RuntimeError, "after durable commit"):
            self.host.process_evidence(1, [claim("A")], fault="after_commit")
        self.reopen()
        self.assertEqual(self.host.history_count(), 1)
        self.assertEqual(self.host.checkpoint().last_sequence, 1)
        self.assertEqual(self.host.pending_count(), 1)
        self.assertIn("report", self.deliver())
        with self.assertRaises(ValueError):
            self.host.process_evidence(1, [claim("A")])

    def test_cross_subject_evidence_fails_before_transaction(self):
        with self.assertRaises(ValueError):
            self.host.process_evidence(1, [claim(subject="bob")])
        self.assertEqual(self.host.checkpoint().last_sequence, 0)

    def test_malformed_updates_rejected_without_state_change(self):
        for invalid in ("raw", {}, None):
            with self.subTest(value=repr(invalid)), self.assertRaises(TypeError):
                self.host.process_evidence(1, [invalid])
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.checkpoint().last_sequence, 0)

    def test_over_capacity_rolls_back_ledger_and_cursor(self):
        tiny = self.open(subject="tiny", policy=AccessPolicy(
            capacity=1, max_batch=2,
        ))
        try:
            with self.assertRaises(ValueError):
                tiny.process_evidence(1, [
                    claim("A", subject="tiny"),
                    claim("B", Stance.DENIES, subject="tiny"),
                ])
            self.assertEqual(tiny.history_count(), 0)
            self.assertEqual(tiny.checkpoint().last_sequence, 0)
        finally:
            tiny.close()

    def test_unsupported_ledger_schema_fails_closed(self):
        self.host.close()
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE epistemic_meta SET ledger_schema=99 WHERE "
                "subject_id='alice'"
            )
        with self.assertRaises(ValueError):
            self.open()
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE epistemic_meta SET ledger_schema=1 WHERE "
                "subject_id='alice'"
            )
        self.host = self.open()

    def test_retraction_requires_previously_encountered_active_source(self):
        with self.assertRaises(ValueError):
            self.host.process_evidence(1, [withdraw("unknown")])
        self.assertEqual(self.host.history_count(), 0)
        self.assertEqual(self.host.checkpoint().last_sequence, 0)

    def test_change_metadata_validation(self):
        with self.assertRaises(TypeError):
            EvidenceChange("alice", "A", "door", "the door",
                           operation="retract")
        with self.assertRaises(TypeError):
            EvidenceChange("alice", "A", "door", "the door",
                           attested="yes")
        with self.assertRaises(ValueError):
            EvidenceChange("alice", "A", "", "the door")


if __name__ == "__main__":
    unittest.main()
