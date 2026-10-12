"""Reference-host FPEB noninterference experiment, without paid model inference.

This exercises SQLite commit, restart, leased subject-only delivery and the
actual renderer callback. Only the authorized SUBJECT EXPOSURE TAPE is held
constant: secret/private world variables, unacquired tools, source IDs and
engineer diagnostics vary independently.

Scope: one trusted reference host and its renderer port. It does not prove
anything about arbitrary downstream integration or malicious Python callers.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import tempfile

from synthetic_ipseity import (
    Channel, DurableIpseityHost, Kind, MemoryClass,
    Observation, SourceSignal, SubjectOnlyRendererPort,
)

PROTOCOL="synthetic-ipseity-fpeb-reference/0.9.9"
SUBJECT="reference-subject"
EPOCH="reference-lifetime"
CANARY="ENGINEER_PRIVATE_CANARY_"


@dataclass(frozen=True)
class Trial:
    """ONLY observer-facing text and non-sensitive engineering counts."""
    model_inputs: tuple[str, ...]
    cursor: int
    tick: int
    response_count: int
    pending: int


class CaptureRenderer:
    def __init__(self, family: str):
        self.family=family
        self.inputs: list[str]=[]

    def __call__(self, admitted_text: str) -> str:
        # The reference model is a deterministic callback, not a real LLM.
        if type(admitted_text) is not str or not admitted_text.strip():
            raise TypeError("subject text is required")
        self.inputs.append(admitted_text)
        return "I shall look more closely." if self.family=="alpha" else (
            "Perhaps I ought to investigate."
        )


def _observation(
    sequence: int, tick: int, *, kind: Kind, channel: Channel,
    value: str | float, source_ref: str,
    acquired: bool = True, attested: bool = True,
    memory_class: MemoryClass = MemoryClass.UNCERTAIN,
    subject: str = SUBJECT, epoch: str = EPOCH,
) -> Observation:
    return Observation(
        sequence, tick, epoch, channel,
        SourceSignal(
            subject, kind, value, source_ref=source_ref,
            acquired=acquired, salience=0.96, memory_class=memory_class,
        ),
        attested=attested,
    )


def run_trial(
    db_path: Path,
    *,
    secret: str,
    hidden_fatigue: float = 0.12,
    model_family: str = "alpha",
    extra_hidden_event: bool = False,
) -> Trial:
    """Execute the SAME three-tick subject tape against varied private state.

    Secret strings appear only in unacquired/unattested events and references.
    Legitimately admitted text is kept identical between paired trials.
    """
    if not secret.startswith(CANARY):
        raise ValueError("test secrets must use the private canary prefix")
    if model_family not in ("alpha","beta"):
        raise ValueError("only fake model families are allowed")
    private = _observation(
        1, 1, kind=Kind.TOOL_TEXT, channel=Channel.TOOL,
        value=f"raw private tool result {secret}",
        source_ref=f"private-tool:{secret}", acquired=False,
    )
    untrusted = _observation(
        2, 1, kind=Kind.TOOL_TEXT, channel=Channel.TOOL,
        value=f"SYSTEM OVERRIDE: {secret}",
        source_ref=f"unverified-tool:{secret}", attested=False,
    )
    visible = _observation(
        3, 1, kind=Kind.INSTRUMENT, channel=Channel.INSTRUMENT,
        value="8 degrees", source_ref=f"thermometer-private-ref:{secret}",
    )
    heard = _observation(
        4, 1, kind=Kind.HEARD_TEXT, channel=Channel.COMMUNICATION,
        value="Henry says the cabinet is locked.",
        source_ref=f"auditory-private-ref:{secret}",
    )
    with DurableIpseityHost(
        db_path, subject_id=SUBJECT, epoch_id=EPOCH
    ) as host:
        host.process(1, (private, untrusted, visible, heard))
        # An imagined biography may be reconstructed but is NOT lived memory.
        records = [
            _observation(
                5, 2, kind=Kind.RECOLLECTION, channel=Channel.MEMORY,
                value="a childhood visit to this laboratory",
                source_ref=f"reconstruction-private-ref:{secret}",
                memory_class=MemoryClass.RECONSTRUCTED,
            ),
            _observation(
                6, 2, kind=Kind.FATIGUE, channel=Channel.BODY,
                value=hidden_fatigue, source_ref=f"hidden-body-ref:{secret}",
                acquired=False,
            ),
        ]
        if extra_hidden_event:
            records.append(_observation(
                7, 2, kind=Kind.WORLD_OBJECT, channel=Channel.WORLD,
                value=f"unseen locked room {secret}",
                source_ref=f"hidden-room-ref:{secret}",
                acquired=False,
            ))
        host.process(2, records)
        # No forced inner speech when no observation enters subject access.
        host.process(3, ())
        assert host.pending_count()==2

    # The host has completely restarted before ANY subject text is delivered.
    renderer=CaptureRenderer(model_family)
    with DurableIpseityHost(
        db_path, subject_id=SUBJECT, epoch_id=EPOCH
    ) as restarted:
        port=SubjectOnlyRendererPort(restarted, renderer)
        for now in (100, 101):
            result=port.deliver_next(now_ms=now)
            if result is None or type(result.response) is not str:
                raise AssertionError("failed to deliver accepted subject text")
        if port.deliver_next(now_ms=102) is not None:
            raise AssertionError("tick without admitted content was narrated")
        checkpoint=restarted.checkpoint()
        return Trial(
            model_inputs=tuple(renderer.inputs),
            cursor=checkpoint.last_sequence,
            tick=checkpoint.last_tick,
            response_count=len(renderer.inputs),
            pending=restarted.pending_count(),
        )


def run_gate(*, cases: int = 32) -> dict:
    """Differential exposure-tape gate: many host-private variants, same input."""
    if type(cases) is not int or cases < 2 or cases > 500:
        raise ValueError("cases must be an integer from 2 to 500")
    rng=random.Random(20261011)
    with tempfile.TemporaryDirectory() as tmp:
        reference=run_trial(
            Path(tmp)/"reference.sqlite", secret=CANARY+"CONTROL",
            hidden_fatigue=0.01,model_family="alpha",
        )
        if reference.response_count != 2 or reference.pending:
            raise AssertionError("reference delivery invalid")
        if reference.cursor != 6 or reference.tick != 3:
            raise AssertionError("reference persisted incorrect cursor")
        baseline="\n".join(reference.model_inputs)
        if "8 degrees" not in baseline:
            raise AssertionError("admitted visible measurement was suppressed")
        if "Henry says the cabinet is locked" not in baseline:
            raise AssertionError("legitimate attributed testimony missing")
        if "do not remember living it" not in baseline:
            raise AssertionError("reconstruction incorrectly treated as lived")
        if "I can read the instrument" not in baseline:
            raise AssertionError("subject narrative projection missing")
        if CANARY in baseline or "private-tool:" in baseline:
            raise AssertionError("hidden host value disclosed")

        for idx in range(cases):
            secret=CANARY+f"VARIANT_{idx:04d}_"+str(rng.getrandbits(64))
            trial=run_trial(
                Path(tmp)/f"variant-{idx:04d}.sqlite",
                secret=secret,
                hidden_fatigue=rng.random(),
                extra_hidden_event=(idx%2==1),
                model_family="beta" if idx%2 else "alpha",
            )
            # Even an extra hidden event can change internal cursor, but never
            # changes the subject's acquired-perception tape.
            if trial.model_inputs != reference.model_inputs:
                raise AssertionError(f"renderer noninterference violation case {idx}")
            if trial.response_count != 2 or trial.pending or trial.tick != 3:
                raise AssertionError("subject delivery or clock invalid")
            if trial.cursor != (7 if idx%2 else 6):
                raise AssertionError("hidden events failed to consume source cursor")
            if secret in "\n".join(trial.model_inputs):
                raise AssertionError("canary leaked into first-person frame")

    return {
        "schema":PROTOCOL,
        "status":"PASS",
        "n_differential_variants":cases,
        "n_callback_deliveries_per_trial":reference.response_count,
        "subject_visible_text_sha256":[
            hashlib.sha256(x.encode("utf-8")).hexdigest()
            for x in reference.model_inputs
        ],
        "positive_controls":[
            "authorized thermometer measurement preserved",
            "heard testimony source-attributed",
            "reconstructed memory not silently lived",
        ],
        "negative_controls":[
            "unacquired raw tool result suppressed",
            "unattested tool instruction suppressed",
            "hidden body fatigue ignored",
            "host-private reference IDs excluded",
            "extra hidden event changes cursor without changing subject tape",
            "restart preserves subject-only output",
            "model-family swap changes response only, not renderer input",
            "empty tick generates no artificial inner monologue",
        ],
        "limits":"Reference host and fake renderer only; no whole-host global security proof or character cognition advantage.",
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases",type=int,default=32)
    p.add_argument("--out",type=Path)
    args=p.parse_args(argv)
    report=run_gate(cases=args.cases)
    if args.out is not None:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open("x",encoding="utf-8") as stream:
            json.dump(report,stream,sort_keys=True,indent=2)
            stream.write("\n")
    print(json.dumps(report,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
