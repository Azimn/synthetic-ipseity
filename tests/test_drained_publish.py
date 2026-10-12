"""Transaction gate for one pending subjective presentation at a time."""
from pathlib import Path
import tempfile
import unittest

from synthetic_ipseity import (
    Channel, Kind, Observation, SourceSignal, DurableIpseityHost
)


def observation(sequence, tick):
    return Observation(
        sequence=sequence, tick=tick, epoch_id="life",
        channel=Channel.BODY,
        signal=SourceSignal(
            subject_id="subject", kind=Kind.COLD, value=0.7,
            acquired=True,
        ),
        attested=True,
    )


class DrainedPublishTests(unittest.TestCase):
    def test_pending_and_leased_output_refuse_next_publish_without_moving_cursor(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "subject.db"
            with DurableIpseityHost(
                path, subject_id="subject", epoch_id="life"
            ) as host:
                host.process(1, [observation(1, 1)], require_drained=True)
                state = host.checkpoint()
                with self.assertRaisesRegex(RuntimeError, "outstanding subject frame"):
                    host.process(2, [observation(2, 2)], require_drained=True)
                self.assertEqual(host.checkpoint(), state)
                lease = host.claim_next(now_ms=100, lease_ms=100)
                self.assertIsNotNone(lease)
                with self.assertRaisesRegex(RuntimeError, "outstanding subject frame"):
                    host.process(2, [observation(2, 2)], require_drained=True)
                self.assertEqual(host.checkpoint(), state)
                host.ack_delivery(lease)
                host.process(2, [observation(2, 2)], require_drained=True)
                self.assertEqual(host.checkpoint().last_sequence, 2)

    def test_competing_host_observes_same_guard_and_can_resume(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "subject.db"
            with DurableIpseityHost(
                path, subject_id="subject", epoch_id="life"
            ) as first:
                first.process(1, [observation(1, 1)], require_drained=True)
                with DurableIpseityHost(
                    path, subject_id="subject", epoch_id="life"
                ) as second:
                    with self.assertRaisesRegex(RuntimeError, "outstanding subject frame"):
                        second.process(2, [observation(2, 2)], require_drained=True)
                    lease = second.claim_next(now_ms=1000)
                    second.ack_delivery(lease)
                    second.process(2, [observation(2, 2)], require_drained=True)

    def test_legacy_default_still_accepts_multiple_pending_frames(self):
        with tempfile.TemporaryDirectory() as td:
            with DurableIpseityHost(
                Path(td) / "subject.db", subject_id="subject", epoch_id="life"
            ) as host:
                host.process(1, [observation(1, 1)])
                host.process(2, [observation(2, 2)])
                self.assertEqual(host.pending_count(), 2)
                with self.assertRaises(TypeError):
                    host.process(3, [], require_drained="yes")
                self.assertEqual(host.checkpoint().last_tick, 2)


if __name__ == "__main__":
    unittest.main()
