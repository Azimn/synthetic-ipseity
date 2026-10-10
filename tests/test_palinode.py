"""Palinode reflection gates, acknowledgement, and crash-recovery tests."""
from pathlib import Path
import sqlite3
import tempfile
import unittest

from synthetic_ipseity import (
    AccessPolicy, BeliefPosition, EpistemicClaim, EvidenceKind,
    ProvisionalBeliefRevision, Stance, SubjectOnlyRendererPort, render_frame,
)
from synthetic_ipseity.palinode import (
    PalinodeHost, ReflectionMode, ReflectionRequest,
)


def testimony(source, stance, *, subject="alice", topic="the western door"):
    return EpistemicClaim(
        subject, EvidenceKind.HEARD,
        "the door is locked" if stance is Stance.AFFIRMS else "the door is unlocked",
        source, acquired=True, attested=True, claim_key="door",
        topic=topic, stance=stance,
    )


def judgment(position, *sources, subject="alice"):
    return ProvisionalBeliefRevision(
        "door", position, "private ledger reason",
        tuple(sources), attested=True,
    )


def request(
    revision_id, mode=ReflectionMode.NOTICE, *,
    subject="alice", epoch="life-1",
    acquired=True, attested=True, salience=0.9,
):
    return ReflectionRequest(
        subject, epoch, revision_id, mode,
        acquired=acquired, attested=attested, salience=salience,
    )


class PalinodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "ipseity.db"
        self.host = self.open()
        self.host.process_evidence(
            1, [testimony("Henry", Stance.AFFIRMS)],
            belief_revisions=[
                judgment(BeliefPosition.AFFIRMS, "Henry"),
            ],
        )
        self.host.process_evidence(
            2, [testimony("Morgan", Stance.DENIES)],
            belief_revisions=[
                judgment(BeliefPosition.SUSPENDS, "Henry", "Morgan"),
            ],
        )
        self.revision_id = self.host.reconsideration_ids("door")[0]

    def tearDown(self):
        self.host.close()
        self.tmp.cleanup()

    def open(self, subject="alice", epoch="life-1", *, policy=None):
        return PalinodeHost(
            self.path, subject_id=subject, epoch_id=epoch,
            policy=policy or AccessPolicy(capacity=5),
        )

    def reopen(self):
        self.host.close()
        self.host = self.open()
        return self.host

    def drain_prior(self):
        # Deliver the earlier witnessed sources, without reflecting on them.
        while self.host.pending_count():
            lease = self.host.claim_next(now_ms=1)
            assert lease is not None
            self.host.ack_delivery(lease)

    def deliver_one(self, *, now=100):
        lease = self.host.claim_next(now_ms=now)
        self.assertIsNotNone(lease)
        text = self.host.read_subject_text(lease)
        self.host.ack_delivery(lease)
        return text

    def test_first_position_not_a_change_of_mind(self):
        first_id = self.revision_id - 1
        self.assertEqual(self.host.reconsideration_ids("door"), (self.revision_id,))
        with self.assertRaisesRegex(ValueError, "first position"):
            self.host.process_reflections(3, [request(first_id)])

    def test_internal_revision_does_not_auto_generate_reflection(self):
        self.assertFalse(self.host.reflection_status(self.revision_id).notice_issued)
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.SUSPENDS)
        self.assertEqual(self.host.checkpoint().last_sequence, 3)  # sources + conflict

    def test_reflection_is_admitted_first_person_not_raw_internal_ledger(self):
        self.drain_prior()
        result = self.host.process_reflections(3, [request(self.revision_id)])
        self.assertIsNotNone(result.outbox_id)
        text = self.deliver_one()
        self.assertIn("no longer certain", text)
        self.assertIn("the western door", text)
        self.assertNotIn("private ledger reason", text)
        self.assertNotIn("palinode:", text)
        self.assertNotIn("Morgan", text)
        self.assertNotIn("suspends", text)
        state = self.host.reflection_status(self.revision_id)
        self.assertTrue(state.notice_issued)
        self.assertTrue(state.notice_delivered)
        self.assertFalse(state.recall_issued)

    def test_no_recall_before_notice_was_rendered_and_acked(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        status = self.host.reflection_status(self.revision_id)
        self.assertTrue(status.notice_issued)
        self.assertFalse(status.notice_delivered)
        saved = self.host.checkpoint()
        with self.assertRaisesRegex(ValueError, "never delivered"):
            self.host.process_reflections(
                4, [request(self.revision_id, ReflectionMode.RECALL)]
            )
        self.assertEqual(self.host.checkpoint(), saved)
        self.assertEqual(self.host.pending_count(), 1)

    def test_recall_after_renderer_ack_has_provenance_and_no_factual_certainty(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        notice = self.deliver_one()
        self.assertIn("no longer certain", notice)
        self.reopen()
        out = self.host.process_reflections(
            4, [request(self.revision_id, ReflectionMode.RECALL)]
        )
        self.assertIsNotNone(out.outbox_id)
        memory = self.deliver_one()
        self.assertIn("recall having noticed", memory)
        self.assertIn("does not settle the facts", memory)
        state = self.host.reflection_status(self.revision_id)
        self.assertTrue(state.recall_issued)
        self.assertTrue(state.recall_delivered)

    def test_renderer_port_is_sole_reference_context_channel(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        seen = []
        port = SubjectOnlyRendererPort(
            self.host, lambda context: seen.append(context) or "I ought to check."
        )
        returned = port.deliver_next(now_ms=200)
        self.assertEqual(returned.response, "I ought to check.")
        self.assertEqual(len(seen), 1)
        self.assertNotIn("revision_id", seen[0])
        self.assertNotIn("Henry", seen[0])
        self.assertTrue(self.host.reflection_status(self.revision_id).notice_delivered)

    def test_default_denied_request_consumes_event_but_not_awareness(self):
        self.drain_prior()
        last = self.host.checkpoint().last_sequence
        outcome = self.host.process_reflections(3, [
            request(self.revision_id, acquired=False, attested=True)
        ])
        self.assertIsNone(outcome.outbox_id)
        self.assertEqual(self.host.checkpoint().last_sequence, last + 1)
        self.assertFalse(self.host.reflection_status(self.revision_id).notice_issued)
        self.assertEqual(self.host.pending_count(), 0)

    def test_unattested_reflection_cannot_issue_notice(self):
        self.drain_prior()
        result = self.host.process_reflections(3, [
            request(self.revision_id, acquired=True, attested=False)
        ])
        self.assertIsNone(result.outbox_id)
        self.assertFalse(self.host.reflection_status(self.revision_id).notice_issued)

    def test_attention_rejection_does_not_produce_lived_record(self):
        with self.open(epoch="silent", policy=AccessPolicy(capacity=0)) as silent:
            silent.process_evidence(1, [
                testimony("A", Stance.AFFIRMS),
            ], belief_revisions=[
                judgment(BeliefPosition.AFFIRMS, "A")
            ])
            silent.process_evidence(2, [
                testimony("B", Stance.DENIES),
            ], belief_revisions=[
                judgment(BeliefPosition.SUSPENDS, "A", "B")
            ])
            rid = silent.reconsideration_ids("door")[0]
            result = silent.process_reflections(3, [request(rid, epoch="silent")])
            self.assertIsNone(result.outbox_id)
            self.assertFalse(silent.reflection_status(rid).notice_issued)
            with self.assertRaisesRegex(ValueError, "never delivered"):
                silent.process_reflections(
                    4, [request(rid, ReflectionMode.RECALL, epoch="silent")]
                )

    def test_cross_subject_and_epoch_revision_ids_cannot_leak(self):
        with self.open(subject="bob") as other:
            with self.assertRaises(ValueError):
                other.process_reflections(
                    1, [request(self.revision_id, subject="bob")]
                )
        with self.open(epoch="life-2") as other_life:
            with self.assertRaises(ValueError):
                other_life.process_reflections(
                    1, [request(self.revision_id, epoch="life-2")]
                )
        self.assertIsNone(self.host.reflection_status(self.revision_id).notice_issued
                          and False or None)

    def test_reconsideration_cannot_replay_same_revision_after_ack(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        self.deliver_one()
        checkpoint = self.host.checkpoint()
        with self.assertRaisesRegex(ValueError, "already admitted"):
            self.host.process_reflections(4, [request(self.revision_id)])
        self.assertEqual(self.host.checkpoint(), checkpoint)

    def test_acknowledged_recall_cannot_be_created_twice(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        self.deliver_one()
        self.host.process_reflections(4, [request(self.revision_id, ReflectionMode.RECALL)])
        self.deliver_one()
        with self.assertRaisesRegex(ValueError, "already admitted"):
            self.host.process_reflections(5, [
                request(self.revision_id, ReflectionMode.RECALL)
            ])

    def test_rollback_before_commit_keeps_no_ticket_or_outbox(self):
        self.drain_prior()
        prior = self.host.checkpoint()
        with self.assertRaisesRegex(RuntimeError, "before commit"):
            self.host.process_reflections(
                3, [request(self.revision_id)], fault="before_commit"
            )
        self.reopen()
        self.assertEqual(self.host.checkpoint(), prior)
        self.assertFalse(self.host.reflection_status(self.revision_id).notice_issued)
        self.assertEqual(self.host.pending_count(), 0)

    def test_after_preview_failpoint_is_nonmutating(self):
        self.drain_prior()
        previous = self.host.checkpoint()
        with self.assertRaisesRegex(RuntimeError, "after preview"):
            self.host.process_reflections(
                3, [request(self.revision_id)], fault="after_preview"
            )
        self.assertEqual(previous, self.host.checkpoint())
        self.assertFalse(self.host.reflection_status(self.revision_id).notice_issued)

    def test_after_commit_uncertainty_keeps_pending_delivery(self):
        self.drain_prior()
        with self.assertRaisesRegex(RuntimeError, "after durable commit"):
            self.host.process_reflections(
                3, [request(self.revision_id)], fault="after_commit"
            )
        self.reopen()
        self.assertTrue(self.host.reflection_status(self.revision_id).notice_issued)
        self.assertFalse(self.host.reflection_status(self.revision_id).notice_delivered)
        self.assertIn("no longer certain", self.deliver_one())

    def test_pending_render_failure_does_not_enable_recall(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        def broken(_context):
            raise RuntimeError("renderer not available")
        with self.assertRaisesRegex(RuntimeError, "renderer not available"):
            SubjectOnlyRendererPort(self.host, broken).deliver_next(
                now_ms=100, lease_ms=100
            )
        with self.assertRaisesRegex(ValueError, "never delivered"):
            self.host.process_reflections(
                4, [request(self.revision_id, ReflectionMode.RECALL)]
            )
        self.assertIsNone(self.host.claim_next(now_ms=150))
        assert self.host.claim_next(now_ms=200) is not None

    def test_empty_reflection_tick_advances_without_inner_monologue(self):
        self.drain_prior()
        before = self.host.checkpoint()
        result = self.host.process_reflections(3, [])
        self.assertIsNone(result.outbox_id)
        self.assertEqual(self.host.checkpoint().last_tick, 3)
        self.assertEqual(self.host.checkpoint().last_sequence, before.last_sequence)
        self.assertEqual(self.host.pending_count(), 0)

    def test_structural_invalid_requests_fail_without_state_change(self):
        prior = self.host.checkpoint()
        invalid = (
            request(self.revision_id, subject="other"),
            request(self.revision_id, epoch="other"),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                self.host.process_reflections(3, [candidate])
        with self.assertRaises(TypeError):
            self.host.process_reflections(3, ["not a request"])
        with self.assertRaises(ValueError):
            self.host.process_reflections(3, [
                request(self.revision_id), request(self.revision_id)
            ])
        self.assertEqual(prior, self.host.checkpoint())

    def test_raw_reflection_and_engineer_status_cannot_render(self):
        for item in (
            request(self.revision_id),
            self.host.reflection_status(self.revision_id),
            self.host,
        ):
            with self.assertRaises(TypeError):
                render_frame(item)

    def test_revision_status_is_not_model_memory(self):
        self.drain_prior()
        self.host.process_reflections(3, [request(self.revision_id)])
        self.assertEqual(self.host.belief_position("door"), BeliefPosition.SUSPENDS)
        self.assertTrue(self.host.status("door").conflict)
        self.assertEqual(self.host.history_count(), 2)

    def test_bad_request_fields_rejected(self):
        with self.assertRaises(ValueError):
            request(0)
        with self.assertRaises(ValueError):
            request(True)
        with self.assertRaises(TypeError):
            request(self.revision_id, mode="notice")
        with self.assertRaises(TypeError):
            request(self.revision_id, attested="yes")
        with self.assertRaises(ValueError):
            request(self.revision_id, salience=float("nan"))

    def test_palinode_schema_disallows_future_version(self):
        self.host.close()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE palinode_meta SET schema_version=99")
        with self.assertRaises(ValueError):
            self.open()
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE palinode_meta SET schema_version=1")
        self.host = self.open()


if __name__ == "__main__":
    unittest.main()
