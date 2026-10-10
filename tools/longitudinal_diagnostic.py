"""Standalone longitudinal epistemic continuity demonstration, no LLM."""
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    AccessPolicy, EvidenceChange, EpistemicClaim, EvidenceKind,
    LongitudinalEpistemicHost, Stance,
)


def reading(source, stance):
    return EpistemicClaim(
        "example", EvidenceKind.HEARD, "a statement about the blue cabinet",
        source, acquired=True, attested=True,
        claim_key="cabinet-closed", topic="the blue cabinet",
        stance=stance,
    )


def run():
    with tempfile.TemporaryDirectory() as home:
        path = Path(home) / "ledger.db"
        def open_host():
            return LongitudinalEpistemicHost(
                path, subject_id="example", epoch_id="first-life",
                policy=AccessPolicy(capacity=8),
            )
        with open_host() as host:
            host.process_evidence(1, [reading("witness-a", Stance.AFFIRMS)])
        with open_host() as host:
            second = host.process_evidence(
                2, [reading("witness-b", Stance.DENIES)]
            )
            assert second.derived_transitions == ("conflict_opened",)
            assert host.status("cabinet-closed").conflict
            assert host.history_count() == 2
        with open_host() as host:
            third = host.process_evidence(3, [
                EvidenceChange(
                    "example", "witness-b", "cabinet-closed",
                    "the blue cabinet", acquired=True, attested=True,
                )
            ])
            assert third.derived_transitions == ("conflict_ceased",)
            assert not host.status("cabinet-closed").conflict
            assert host.history_count() == 3
        # Each committed first-person frame is recoverable after a restart.
        with open_host() as host:
            texts = []
            now = 100
            while (lease := host.claim_next(now_ms=now)) is not None:
                texts.append(host.read_subject_text(lease))
                host.ack_delivery(lease)
                now += 1
            output = "\n".join(texts)
            assert "conflicting indications" in output
            assert "no longer conflict" in output
            assert "does not prove" in output
            assert "witness-a" not in output
            assert "witness-b" not in output
            assert host.checkpoint().last_sequence == 5
            assert host.pending_count() == 0
            print("SUBJECT EXPERIENCES ACROSS THREE RESTARTS:")
            print(output)
            print("\nAPPEND-ONLY HISTORY, CONSISTENCY AND REPLAY: PASS")


if __name__ == "__main__":
    run()
