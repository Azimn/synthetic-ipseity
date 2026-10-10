"""Cross-tick provenance, atomic rollback, and belief-revision contract tests."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from synthetic_ipseity import (
    AccessPolicy, DurableIpseityHost, EpistemicClaim, EvidenceKind,
    Stance, SubjectOnlyRendererPort, render_frame,
)
from synthetic_ipseity.epistemic_ledger import (
    BeliefRevision, LongitudinalEpistemicHost, Position,
)


def source(
    ref="A", stance=Stance.AFFIRMS, *, subject="alice", key="door",
    topic="the western door", attested=True, acquired=True, text=None,
    kind=EvidenceKind.HEARD, verified=False, salience=0.8,
):
    return EpistemicClaim(
        subject, kind, text or ("The door is locked" if stance is Stance.AFFIRMS
                               else "The door is unlocked"),
        ref, acquired=acquired, attested=attested, salience=salience,
        claim_key=key, topic=topic, stance=stance, lived_verified=verified,
    )


def revise(position, *sources, key="door", attested=True, reason="new evidence"):
    return BeliefRevision(key, position, reason, tuple(sources), attested)


class LongitudinalLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "subject.db"
        self.host = self.open()

    def tearDown(self):
        self.host.close()
        self.tmp.cleanup()

    def open(self, subject="alice", epoch="life-1", policy=None):
        return LongitudinalEpistemicHost(
            self.path, subject_id=subject, epoch_id=epoch,
            policy=policy or AccessPolicy(capacity=5),
        )

    def restart(self):
        self.host.close()
        self.host = self.open()
        return self.host

    def deliver(self, host=None, now_ms=100):
        target = host or self.host
        lease = target.claim_next(now_ms=now_ms)
        if lease is None:
            return ""
        text = target.read_subject_text(lease)
        target.ack_delivery(lease)
        return text

    def test_cross_tick_conflict_detected_after_restart(self):
        first = self.host.process_claims(1, [source("A")])
        self.assertEqual(first.last_sequence, 1)
        self.assertFalse(self.host.epistemic_state("door").unresolved_conflict)
        self.assertNotIn("conflicting", self.deliver())
        self.restart()
        second = self.host.process_claims(
            2, [source("B", Stance.DENIES)],
        )
        self.assertEqual(second.last_sequence, 3)  # new source + projected conflict
        text = self.deliver()
        self.assertIn("conflicting indications", text)
        self.assertIn("cannot yet tell which is right", text)
        self.assertNotIn("A", text)
        self.assertNotIn("conflict:", text)
        state = self.host.epistemic_state("door")
        self.assertEqual(state.affirming_sources, ("A",))
        self.assertEqual(state.denying_sources, ("B",))
        self.assertTrue(state.unresolved_conflict)
        self.assertTrue(state.conflict_projected)

    def test_same_tick_conflict_and_restart_not_reannounced(self):
        self.host.process_claims(
            1, [source("A"), source("B", Stance.DENIES)]
        )
        self.assertEqual(self.host.checkpoint().last_sequence, 3)
        self.assertIn("conflicting", self.deliver())
        self.restart()
        self.host.process_claims(
            2, [source("C", Stance.AFFIRMS)]
        )
        self.assertEqual(self.host.checkpoint().last_sequence, 4)
        self.assertNotIn("conflicting", self.deliver())
        self.assertEqual(self.host.evidence_count(), 3)

    def test_duplicate_source_cannot_fake_independence_across_ticks(self):
        self.host.process_claims(1, [source("A")])
        self.deliver()
        self.host.process_claims(2, [source("A", Stance.DENIES)])
        self.assertEqual(self.host.checkpoint().last_sequence, 2)
        self.assertFalse(self.host.epistemic_state("door").unresolved_conflict)
        self.assertNotIn("conflicting", self.deliver())

    def test_denied_sources_are_not_ledger_evidence_or_conflict(self):
        self.host.process_claims(1, [source("A")])
        self.deliver()
        self.host.process_claims(
            2, [
                source("B", Stance.DENIES, acquired=False),
                source("C", Stance.DENIES, attested=False),
            ],
        )
        self.assertEqual(self.host.evidence_count(), 1)
        self.assertEqual(self.host.checkpoint().last_sequence, 3)
        self.assertEqual(self.deliver(), "")
        self.assertFalse(self.host.epistemic_state("door").unresolved_conflict)

    def test_unverified_lived_claim_is_not_contrast_evidence(self):
        self.host.process_claims(1, [source("A")])
        self.deliver()
        self.host.process_claims(
            2, [source("B", Stance.DENIES, kind=EvidenceKind.LIVED_RECALL)]
        )
        self.assertFalse(self.host.epistemic_state("door").unresolved_conflict)
        self.assertIn("uncertain impression", self.deliver())
        self.assertEqual(self.host.evidence_count(), 2)

    def test_verified_lived_claim_can_be_contrast_evidence(self):
        self.host.process_claims(1, [source("A")])
        self.deliver()
        self.host.process_claims(
            2, [source("B", Stance.DENIES, kind=EvidenceKind.LIVED_RECALL,
                       verified=True)]
        )
        self.assertTrue(self.host.epistemic_state("door").unresolved_conflict)
        self.assertIn("conflicting", self.deliver())

    def test_conflict_not_recorded_when_awareness_gate_drops_it(self):
        low_capacity = AccessPolicy(capacity=0)
        with self.open(epoch="silent", policy=low_capacity) as host:
            host.process_claims(1, [
                source("A", subject="alice"),
                source("B", Stance.DENIES, subject="alice"),
            ])
            state = host.epistemic_state("door")
            self.assertTrue(state.unresolved_conflict)
            self.assertFalse(state.conflict_projected)
            self.assertEqual(host.pending_count(), 0)
            self.assertEqual(host.checkpoint().last_sequence, 3)

    def test_unnoticed_conflict_can_surface_after_next_evidence(self):
        # Attention cap may prevent a conflict notice when one tick is full.
        with self.open(epoch="tight", policy=AccessPolicy(capacity=1)) as host:
            host.process_claims(1, [source("A"), source("B", Stance.DENIES)])
            initial = host.epistemic_state("door")
            self.assertTrue(initial.unresolved_conflict)
            # At capacity 1, the first source has equal or higher salience
            # and therefore wins the earlier index tie.
            self.assertFalse(initial.conflict_projected)
            lease = host.claim_next(now_ms=100)
            host.ack_delivery(lease)
            host.process_claims(2, [source("C", Stance.DENIES, salience=0.2)])
            text = host.read_subject_text(host.claim_next(now_ms=200))
            self.assertIn("conflicting", text)
            self.assertTrue(host.epistemic_state("door").conflict_projected)

    def test_invalid_cross_tick_topic_rolls_back_everything(self):
        self.host.process_claims(1, [source("A")])
        before = self.host.checkpoint()
        count = self.host.evidence_count()
        with self.assertRaises(ValueError):
            self.host.process_claims(
                2, [source("B", Stance.DENIES, topic="the ceiling")]
            )
        self.assertEqual(self.host.checkpoint(), before)
        self.assertEqual(self.host.evidence_count(), count)

    def test_precommit_failure_rolls_back_evidence_outbox_and_cursor(self):
        with self.assertRaisesRegex(RuntimeError, "before commit"):
            self.host.process_claims(
                1, [source("A")], fault="before_commit"
            )
        self.restart()
        self.assertEqual(self.host.checkpoint().last_sequence, 0)
        self.assertEqual(self.host.evidence_count(), 0)
        self.assertEqual(self.host.pending_count(), 0)
        self.host.process_claims(1, [source("A")])
        self.assertEqual(self.host.evidence_count(), 1)

    def test_after_preview_failure_unchanged(self):
        with self.assertRaisesRegex(RuntimeError, "after preview"):
            self.host.process_claims(
                1, [source("A")], fault="after_preview"
            )
        self.assertEqual(self.host.evidence_count(), 0)
        self.assertEqual(self.host.checkpoint().last_tick, -1)

    def test_after_commit_uncertainty_recovers_without_double_processing(self):
        with self.assertRaisesRegex(RuntimeError, "after durable commit"):
            self.host.process_claims(
                1, [source("A")], fault="after_commit"
            )
        self.restart()
        self.assertEqual(self.host.evidence_count(), 1)
        self.assertEqual(self.host.checkpoint().last_sequence, 1)
        self.assertEqual(self.host.pending_count(), 1)
        with self.assertRaises(ValueError):
            self.host.process_claims(2, [source("A")])

    def test_immutable_record_history_survives_position_revisions(self):
        self.host.process_claims(
            1, [source("A")],
            revisions=[revise(Position.AFFIRMS, "A", reason="first account")],
        )
        self.deliver()
        self.assertEqual(self.host.evidence_count(), 1)
        self.assertEqual(
            self.host.epistemic_state("door").provisional_position,
            Position.AFFIRMS,
        )
        self.host.process_claims(
            2, [source("B", Stance.DENIES)],
            revisions=[revise(Position.SUSPENDS, "A", "B",
                              reason="witness conflict")],
        )
        self.deliver()
        state = self.host.epistemic_state("door")
        self.assertEqual(state.provisional_position, Position.SUSPENDS)
        self.assertEqual(state.revision_count, 2)
        self.assertEqual(self.host.evidence_count(), 2)
        trail = self.host.revisions("door")
        self.assertEqual(tuple(r.current for r in trail),
                         (Position.AFFIRMS, Position.SUSPENDS))
        self.assertEqual(trail[0].previous, None)
        self.assertEqual(trail[1].previous, Position.AFFIRMS)
        self.assertEqual(trail[0].reason, "first account")
        self.restart()
        self.assertEqual(self.host.revisions("door"), trail)

    def test_can_revise_provisional_stance_without_erasing_conflict(self):
        self.host.process_claims(1, [source("A"), source("B", Stance.DENIES)])
        self.deliver()
        self.host.process_claims(
            2, [], revisions=[revise(Position.DENIES, "B")],
        )
        state = self.host.epistemic_state("door")
        self.assertEqual(state.provisional_position, Position.DENIES)
        self.assertTrue(state.unresolved_conflict)
        self.assertTrue(state.conflict_projected)
        self.assertEqual(self.host.evidence_count(), 2)
        self.assertEqual(self.host.pending_count(), 0)

    def test_unattested_revision_cannot_write_new_position(self):
        self.host.process_claims(1, [source("A")])
        checkpoint = self.host.checkpoint()
        with self.assertRaises(ValueError):
            self.host.process_claims(
                2, [], revisions=[revise(Position.AFFIRMS, "A", attested=False)]
            )
        self.assertEqual(self.host.checkpoint(), checkpoint)
        self.assertEqual(self.host.revisions("door"), ())

    def test_revision_cannot_cite_inaccessible_or_unknown_sources(self):
        self.host.process_claims(1, [source("A")])
        for basis in ("unseen", "B"):
            with self.subTest(basis=basis), self.assertRaises(ValueError):
                self.host.process_claims(
                    2, [], revisions=[revise(Position.AFFIRMS, basis)]
                )
        self.assertEqual(self.host.revisions("door"), ())

    def test_revision_requires_stance_matched_evidence(self):
        self.host.process_claims(1, [source("A", Stance.AFFIRMS)])
        with self.assertRaises(ValueError):
            self.host.process_claims(
                2, [], revisions=[revise(Position.DENIES, "A")]
            )
        self.assertEqual(self.host.revisions("door"), ())

    def test_duplicate_position_rejected_without_history_mutation(self):
        self.host.process_claims(
            1, [source("A")],
            revisions=[revise(Position.AFFIRMS, "A")],
        )
        with self.assertRaises(ValueError):
            self.host.process_claims(
                2, [], revisions=[revise(Position.AFFIRMS, "A")]
            )
        self.assertEqual(self.host.epistemic_state("door").revision_count, 1)
        self.assertEqual(self.host.checkpoint().last_tick, 1)

    def test_revision_only_tick_advances_without_subject_narration(self):
        self.host.process_claims(1, [source("A")])
        self.deliver()
        prior = self.host.checkpoint()
        receipt = self.host.process_claims(
            2, [], revisions=[revise(Position.AFFIRMS, "A")],
        )
        self.assertIsNone(receipt.outbox_id)
        self.assertEqual(receipt.last_tick, 2)
        self.assertEqual(receipt.last_sequence, prior.last_sequence)
        self.assertEqual(self.host.pending_count(), 0)

    def test_separate_subjects_and_epochs_do_not_share_beliefs(self):
        self.host.process_claims(1, [source("A")])
        with self.open(subject="bob") as other:
            other.process_claims(1, [
                source("X", subject="bob", stance=Stance.DENIES)
            ])
            self.assertEqual(other.epistemic_state("door").affirming_sources, ())
            self.assertEqual(self.host.epistemic_state("door").denying_sources, ())
            self.assertEqual(other.evidence_count(), 1)
        with self.open(epoch="life-2") as later:
            with self.assertRaises(KeyError):
                later.epistemic_state("door")

    def test_renderer_cannot_render_ledger_state_or_revision_log(self):
        self.host.process_claims(
            1, [source("A")],
            revisions=[revise(Position.AFFIRMS, "A")],
        )
        for engineer in (
            self.host.epistemic_state("door"),
            self.host.revisions("door"),
            self.host,
        ):
            with self.assertRaises(TypeError):
                render_frame(engineer)

    def test_model_port_can_consume_ledger_outbox_through_base_host(self):
        self.host.process_claims(
            1, [source("A"), source("B", Stance.DENIES)]
        )
        seen = []
        with DurableIpseityHost(
            self.path, subject_id="alice", epoch_id="life-1",
            policy=AccessPolicy(capacity=5),
        ) as safe_host:
            port = SubjectOnlyRendererPort(
                safe_host, lambda context: seen.append(context) or "Acknowledged"
            )
            outcome = port.deliver_next(now_ms=100)
            self.assertEqual(outcome.response, "Acknowledged")
        self.assertEqual(len(seen), 1)
        self.assertIn("conflicting indications", seen[0])
        self.assertNotIn("source_ref", seen[0])
        self.assertNotIn("A", seen[0])

    def test_does_not_store_raw_evidence_text_in_ledger(self):
        sensitive = "private biography text secret 12345"
        self.host.process_claims(
            1, [source("A", text=sensitive)],
        )
        with sqlite3.connect(self.path) as db:
            rows = db.execute(
                "SELECT kind, source_ref, claim_key, topic, "
                "content_digest FROM epistemic_evidence"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertNotIn(sensitive, str(rows))
            self.assertNotIn("12345", str(rows))
            # Source identifiers remain engineer-only in storage.
            self.assertEqual(rows[0][1], "A")
        # The admitted subjective text can of course legitimately describe
        # the personally heard message. This is not a secure enclave.
        self.assertIn(sensitive, self.deliver())

    def test_direct_world_processing_does_not_fabricate_evidence_history(self):
        # Explicitly verify that the older direct API is not silently
        # interpreted as provenance-verified ledger evidence.
        from synthetic_ipseity import Channel, Kind, Observation, SourceSignal
        self.host.process(1, [Observation(
            1, 1, "life-1", Channel.BODY,
            SourceSignal("alice", Kind.COLD, 0.9, acquired=True),
            attested=True,
        )])
        self.assertEqual(self.host.evidence_count(), 0)

    def test_many_ticks_without_spurious_conflict_reannouncement(self):
        self.host.process_claims(1, [source("A"), source("B", Stance.DENIES)])
        for tick in range(2, 32):
            self.host.process_claims(
                tick, [source(f"witness-{tick}", Stance.AFFIRMS)]
            )
        self.assertEqual(self.host.evidence_count(), 32)
        self.assertEqual(self.host.checkpoint().last_sequence, 33)
        self.assertTrue(self.host.epistemic_state("door").conflict_projected)

    def test_invalid_tampered_epistemic_schema_is_not_accepted(self):
        self.host.close()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE epistemic_version SET version=999")
        with self.assertRaises(ValueError):
            self.open()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE epistemic_version SET version=1")
        self.host = self.open()


if __name__ == "__main__":
    unittest.main()
