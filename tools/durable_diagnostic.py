"""End-to-end SQLite restart and outbox demonstration. No LLM needed."""
import tempfile
from pathlib import Path

from synthetic_ipseity import (
    Channel, DurableIpseityHost, Kind, Observation, SourceSignal,
)


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "organ.db"
        observation = Observation(
            sequence=1, tick=1, epoch_id="life-1", channel=Channel.BODY,
            signal=SourceSignal(
                "demo-subject", Kind.COLD, 0.9,
                source_ref="private thermometer telemetry", acquired=True,
            ),
            attested=True,
        )
        with DurableIpseityHost(
            path, subject_id="demo-subject", epoch_id="life-1",
        ) as first:
            try:
                first.process(1, [observation], fault="after_commit")
            except RuntimeError as err:
                assert "after durable commit" in str(err)
            assert first.checkpoint().last_sequence == 1
        with DurableIpseityHost(
            path, subject_id="demo-subject", epoch_id="life-1",
        ) as restarted:
            assert restarted.pending_count() == 1
            lease = restarted.claim_next(now_ms=100, lease_ms=100)
            text = restarted.read_subject_text(lease)
            assert text == "I feel deeply chilled."
            assert "thermometer telemetry" not in text
            print("FIRST-PERSON SUBJECT DELIVERY:", text)
            # Simulate failed acknowledgement. Lease expires.
            new_lease = restarted.claim_next(now_ms=200)
            assert new_lease.outbox_id == lease.outbox_id
            assert new_lease.token != lease.token
            restarted.ack_delivery(new_lease)
            assert restarted.pending_count() == 0
            print("DURABLE COMMIT, RESTART AND RETRY: PASS")
            try:
                restarted.process(2, [observation])
            except ValueError:
                print("DUPLICATE SOURCE EVENT AFTER RESTART: BLOCKED")
            else:
                raise AssertionError("duplicate source event accepted")


if __name__ == "__main__":
    main()
