"""Reproducible cross-day epistemic persistence with a renderer-only boundary."""
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    AccessPolicy, BeliefRevision, DurableIpseityHost, EpistemicClaim,
    EvidenceKind, LongitudinalEpistemicHost, Position, Stance,
    SubjectOnlyRendererPort,
)


def report(ref, words, stance):
    return EpistemicClaim(
        "example-subject", EvidenceKind.HEARD, words, ref,
        acquired=True, attested=True,
        claim_key="door", topic="the western door", stance=stance,
    )


def main():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "organ.db"
        policy = AccessPolicy(capacity=5)
        with LongitudinalEpistemicHost(
            path, subject_id="example-subject",
            epoch_id="lifetime-1", policy=policy,
        ) as host:
            host.process_claims(
                1, [report("henry", "The western door is locked", Stance.AFFIRMS)],
                revisions=[
                    BeliefRevision("door", Position.AFFIRMS,
                                   "first account", ("henry",), attested=True)
                ],
            )
        with LongitudinalEpistemicHost(
            path, subject_id="example-subject",
            epoch_id="lifetime-1", policy=policy,
        ) as restarted:
            restarted.process_claims(
                2, [report("morgan", "The western door is unlocked", Stance.DENIES)],
                revisions=[
                    BeliefRevision("door", Position.SUSPENDS,
                                   "conflicting reports",
                                   ("henry", "morgan"), attested=True)
                ],
            )
            state = restarted.epistemic_state("door")
            assert state.unresolved_conflict
            assert state.conflict_projected
            assert state.provisional_position is Position.SUSPENDS
            assert restarted.evidence_count() == 2
            assert restarted.checkpoint().last_sequence == 3
        heard = []
        with DurableIpseityHost(
            path, subject_id="example-subject",
            epoch_id="lifetime-1", policy=policy,
        ) as safe:
            renderer = SubjectOnlyRendererPort(
                safe, lambda context: heard.append(context) or "I need to check the door."
            )
            while safe.pending_count():
                receipt = renderer.deliver_next(now_ms=1000)
                assert receipt is not None
            assert any("conflicting indications" in item for item in heard)
            assert all("henry" not in item and "morgan" not in item for item in heard)
        print("STANDALONE FIRST-PERSON CONTEXT:")
        print("\n".join(heard))
        print("\nCROSS-DAY EVIDENCE, REVISED POSITION, RESTART: PASS")


if __name__ == "__main__":
    main()
