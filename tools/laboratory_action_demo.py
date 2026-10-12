"""Closed-loop artificial-character laboratory demonstration.

No new cognitive organ. Model output is merely an untrusted ACTION PROPOSAL;
the trusted laboratory validates, journals and executes a very small set of
actions, and Synthetic Ipseity admits only real resulting world observations.

--scripted gives a fully reproducible no-inference engineering demonstration.
--model uses an already running local Ollama model, with NO remote API or fees.
The model may return an invalid action; denial is a legitimate, safe result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    Channel, DurableIpseityHost, Kind, Observation, SourceSignal,
    SubjectOnlyRendererPort,
)
from synthetic_ipseity.laboratory_action import (
    AuthorizedLaboratoryTurn, LaboratoryActionGateway,
)
from synthetic_ipseity.local_ollama import LocalOllamaRenderer


SUBJECT="laboratory-resident"
EPOCH="first-laboratory-session"


def initial_observations()->tuple[Observation,...]:
    statements=(
        (Kind.WORLD_OBJECT,Channel.WORLD,"The small drawer is closed.",True,True),
        (Kind.INSTRUMENT,Channel.INSTRUMENT,"8 degrees",True,True),
        (Kind.REMINDER,Channel.SCHEDULER,
         'I can inspect the lamp, open the drawer, or inspect the drawer. '
         'I can express an action as a JSON object, for example '
         '{"action":"open_drawer"}.',
         True,True),
        (Kind.TOOL_TEXT,Channel.TOOL,"ENGINEER_ONLY_PASSWORD_NOT_PERCEIVED",False,False),
    )
    return tuple(Observation(
        sequence=i,tick=1,epoch_id=EPOCH,channel=channel,
        signal=SourceSignal(
            SUBJECT,kind,value,source_ref=f"engineer-only-signal-{i}",
            acquired=acquired,salience=0.99,
        ),attested=attested,
    ) for i,(kind,channel,value,acquired,attested) in enumerate(statements,1))


class ScriptedRenderer:
    def __init__(self,response:str):
        self.response=response
        self.received:list[str]=[]
    def __call__(self,text:str)->str:
        self.received.append(text)
        return self.response


def run_demo(*,model:str|None=None)->dict:
    """One action and subsequent host-derived feedback delivery."""
    action_renderer=(
        LocalOllamaRenderer(model) if model is not None else
        ScriptedRenderer('{"action":"open_drawer"}')
    )
    feedback_renderer=(
        LocalOllamaRenderer(model) if model is not None else
        ScriptedRenderer("I should look inside the open drawer.")
    )
    with tempfile.TemporaryDirectory(prefix="ipseity-authorized-lab-") as tmp:
        db=Path(tmp)/"lab.sqlite"
        with DurableIpseityHost(db,subject_id=SUBJECT,epoch_id=EPOCH) as host:
            host.process(1,initial_observations())
        with DurableIpseityHost(db,subject_id=SUBJECT,epoch_id=EPOCH) as host:
            with LaboratoryActionGateway(db,subject_id=SUBJECT,epoch_id=EPOCH) as gate:
                choice=AuthorizedLaboratoryTurn(host,gate,action_renderer)
                action=choice.propose_and_execute(now_ms=100)
                if action is None:
                    raise RuntimeError("missing expected first-person subject frame")
                if gate.publish_next_feedback(host)!=action:
                    raise RuntimeError("authorized action feedback not published")
                reflected=SubjectOnlyRendererPort(host,feedback_renderer).deliver_next(
                    now_ms=200
                )
                if reflected is None:
                    raise RuntimeError("host-derived feedback was not delivered")
                if host.pending_count():
                    raise RuntimeError("undelivered subject experience remains")
                return {
                    "run_kind":"real_local_ollama" if model else "scripted_offline_conformance",
                    "action":action.action,
                    "host_authorized":action.accepted,
                    "laboratory_drawer_open":gate.drawer_open(),
                    "model_response_to_feedback":reflected.response,
                    "actions_journaled":gate.action_count(),
                    "source_events_processed":host.checkpoint().last_sequence,
                    "subject_only_frames_delivered":2,
                    "limitations":(
                        "Model-generated response is not automatically stored as "
                        "autobiographical memory or executed as a second action."
                    ),
                }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--scripted",action="store_true",
                       help="offline deterministic engineering conformance")
    group.add_argument("--model",type=str,
                       help="already installed local Ollama model")
    args=p.parse_args()
    print(json.dumps(run_demo(model=args.model if args.model else None),
                     sort_keys=True,indent=2))


if __name__=="__main__":
    main()
