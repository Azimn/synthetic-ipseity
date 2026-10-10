"""Palinode: revised stance -> noticed experience -> delivered -> later recall."""
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    AccessPolicy, BeliefPosition, DurableIpseityHost,
    EpistemicClaim, EvidenceKind, PalinodeHost,
    ProvisionalBeliefRevision, ReflectionMode, ReflectionRequest,
    Stance, SubjectOnlyRendererPort,
)


def claim(source, polarity):
    return EpistemicClaim(
        "example", EvidenceKind.HEARD, "an account of the western door", source,
        acquired=True, attested=True, claim_key="door",
        topic="the western door", stance=polarity,
    )


def revision(position, *refs):
    return ProvisionalBeliefRevision(
        "door", position, "engineer-only change reason", refs, attested=True,
    )


def main():
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "palinode.db"
        policy = AccessPolicy(capacity=5)
        with PalinodeHost(
            path, subject_id="example", epoch_id="life-1", policy=policy,
        ) as host:
            host.process_evidence(1, [claim("Henry", Stance.AFFIRMS)],
                belief_revisions=[revision(BeliefPosition.AFFIRMS, "Henry")])
            host.process_evidence(2, [claim("Morgan", Stance.DENIES)],
                belief_revisions=[
                    revision(BeliefPosition.SUSPENDS, "Henry", "Morgan")
                ])
            rid = host.reconsideration_ids("door")[-1]
            assert not host.reflection_status(rid).notice_issued
            host.process_reflections(3, [ReflectionRequest(
                "example", "life-1", rid, ReflectionMode.NOTICE,
                acquired=True, attested=True,
            )])
            assert host.reflection_status(rid).notice_issued
            assert not host.reflection_status(rid).notice_delivered
            try:
                host.process_reflections(4, [ReflectionRequest(
                    "example", "life-1", rid, ReflectionMode.RECALL,
                    acquired=True, attested=True,
                )])
            except ValueError:
                print("RECALL BEFORE ACK: DENIED")
            else:
                raise AssertionError("undelivered reconsideration became memory")
        seen = []
        with DurableIpseityHost(
            path, subject_id="example", epoch_id="life-1", policy=policy,
        ) as safe:
            port = SubjectOnlyRendererPort(
                safe, lambda context: seen.append(context) or "I should check the door."
            )
            while safe.pending_count():
                result = port.deliver_next(now_ms=1000)
                assert result is not None
        with PalinodeHost(
            path, subject_id="example", epoch_id="life-1", policy=policy,
        ) as host:
            assert host.reflection_status(rid).notice_delivered
            host.process_reflections(4, [ReflectionRequest(
                "example", "life-1", rid, ReflectionMode.RECALL,
                acquired=True, attested=True,
            )])
        with DurableIpseityHost(
            path, subject_id="example", epoch_id="life-1", policy=policy,
        ) as safe:
            port = SubjectOnlyRendererPort(
                safe, lambda context: seen.append(context) or "I will remember to verify."
            )
            assert port.deliver_next(now_ms=2000) is not None
        assert any("no longer certain" in line for line in seen)
        assert any("recall having noticed" in line for line in seen)
        assert all("palinode:" not in line for line in seen)
        assert all("engineer-only" not in line for line in seen)
        print("\nMODEL-SAFE FIRST-PERSON DELIVERY:")
        print("\n".join(seen[-2:]))
        print("\nPALINODE REFLECTION, ACK-GATED RECALL AND RESTART: PASS")


if __name__ == "__main__":
    main()
