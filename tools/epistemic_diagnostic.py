"""Offline, character-agnostic source-monitor diagnostic with durable replay."""
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    DurableIpseityHost, EpistemicClaim, EpistemicSourceMonitor,
    EvidenceKind, Stance,
)


def main():
    monitor = EpistemicSourceMonitor()
    claims = (
        EpistemicClaim(
            "sample", EvidenceKind.HEARD, "The western door is locked",
            "private-source-17", attested=True, acquired=True,
            source_name="Visitor", claim_key="door", topic="the western door",
            stance=Stance.AFFIRMS,
        ),
        EpistemicClaim(
            "sample", EvidenceKind.READ, "The western door is unlocked",
            "private-source-18", attested=True, acquired=True,
            source_name="Ledger", claim_key="door", topic="the western door",
            stance=Stance.DENIES,
        ),
    )
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "epistemics.db"
        with DurableIpseityHost(
            db, subject_id="sample", epoch_id="life-1",
        ) as host:
            result = monitor.project(
                subject_id="sample", epoch_id="life-1",
                tick=1, start_sequence=1, claims=claims,
            )
            assert result.count == 3
            host.process(1, result.observations)
        with DurableIpseityHost(
            db, subject_id="sample", epoch_id="life-1",
        ) as recovered:
            lease = recovered.claim_next(now_ms=1000)
            assert lease is not None
            text = recovered.read_subject_text(lease)
            assert "conflicting indications" in text
            assert "cannot yet tell which is right" in text
            assert "private-source-17" not in text
            assert "private-source-18" not in text
            print("SUBJECT-ACCESSIBLE EXPERIENCE:")
            print(text)
            recovered.ack_delivery(lease)
            assert recovered.checkpoint().last_sequence == 3
            assert recovered.pending_count() == 0
            print("\nEPISTEMIC SOURCE MONITOR AND RESTART: PASS")


if __name__ == "__main__":
    main()
