"""Demonstrate that a source correction is not a character's change of mind."""
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    AccessPolicy, BeliefPosition, EpistemicClaim, EvidenceKind,
    LongitudinalEpistemicHost, ProvisionalBeliefRevision, Stance,
)


def heard(name, words, stance):
    return EpistemicClaim(
        "test-character", EvidenceKind.HEARD, words, name,
        acquired=True, attested=True,
        claim_key="door", topic="the western door", stance=stance,
    )


def main():
    with tempfile.TemporaryDirectory() as directory:
        file = Path(directory) / "character.db"
        policy = AccessPolicy(capacity=6)
        with LongitudinalEpistemicHost(
            file, subject_id="test-character", epoch_id="life-a", policy=policy,
        ) as host:
            host.process_evidence(1, [
                heard("Henry", "The door is locked", Stance.AFFIRMS),
            ], belief_revisions=[
                ProvisionalBeliefRevision(
                    "door", BeliefPosition.AFFIRMS, "first witness",
                    ("Henry",), attested=True,
                ),
            ])
        with LongitudinalEpistemicHost(
            file, subject_id="test-character", epoch_id="life-a", policy=policy,
        ) as recovered:
            recovered.process_evidence(2, [
                heard("Morgan", "The door is not locked", Stance.DENIES),
            ], belief_revisions=[
                ProvisionalBeliefRevision(
                    "door", BeliefPosition.SUSPENDS, "conflicting reports",
                    ("Henry", "Morgan"), attested=True,
                ),
            ])
            assert recovered.history_count() == 2
            assert recovered.status("door").conflict
            assert recovered.belief_position("door") is BeliefPosition.SUSPENDS
            trail = recovered.belief_revisions("door")
            assert len(trail) == 2 and trail[-1].previous is BeliefPosition.AFFIRMS
            print("EVIDENCE COUNT (original sources preserved):", recovered.history_count())
            print("ENGINEER-ONLY PROVISIONAL BELIEF:", recovered.belief_position("door").value)
            messages = []
            while recovered.pending_count():
                lease = recovered.claim_next(now_ms=1000)
                assert lease is not None
                messages.append(recovered.read_subject_text(lease))
                recovered.ack_delivery(lease)
            text = "\n".join(messages)
            assert "conflicting indications" in text
            assert "first witness" not in text
            assert "conflicting reports" not in text
            print("SUBJECT-ACCESSIBLE OBSERVATIONS:", text)
            print("ATOMIC PROVISIONAL BELIEF AND HISTORY: PASS")


if __name__ == "__main__":
    main()
