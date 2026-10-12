"""Authorized laboratory cognition-action-feedback cycle, failure and scope."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from synthetic_ipseity import (
    Channel, DurableIpseityHost, Kind, Observation, SourceSignal,
    SubjectOnlyRendererPort,
)
from synthetic_ipseity.laboratory_action import (
    ALLOWED_ACTIONS, AuthorizedLaboratoryTurn, LabActionReceipt,
    LaboratoryActionGateway,
)


SUBJECT="character-subject"
EPOCH="lifetime-1"


class ScriptedRenderer:
    def __init__(self,*responses:str):
        self.responses=list(responses)
        self.inputs=[]
    def __call__(self,subject_text:str)->str:
        self.inputs.append(subject_text)
        if not self.responses:
            raise RuntimeError("scripted responses exhausted")
        return self.responses.pop(0)


def first_frame(*,subject=SUBJECT,epoch=EPOCH)->list[Observation]:
    data=(
        (Kind.TOOL_TEXT,Channel.TOOL,"ENGINEER_SECRET_DO_NOT_RENDER",False,False),
        (Kind.INSTRUMENT,Channel.INSTRUMENT,"8 degrees",True,True),
        (Kind.WORLD_OBJECT,Channel.WORLD,"The drawer is closed.",True,True),
        (Kind.REMINDER,Channel.SCHEDULER,"I can inspect the lamp, open the drawer, or inspect the drawer.",True,True),
    )
    return [Observation(
        i,1,epoch,channel,
        SourceSignal(subject,kind,value,source_ref=f"private-record:{i}",
                     acquired=acquired,salience=0.98),
        attested=attested,
    ) for i,(kind,channel,value,acquired,attested) in enumerate(data,1)]


class LaboratoryActionCycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"laboratory.sqlite"
        self.host=DurableIpseityHost(
            self.path,subject_id=SUBJECT,epoch_id=EPOCH,
        )
        self.host.process(1,first_frame())
        self.gateway=LaboratoryActionGateway(
            self.path,subject_id=SUBJECT,epoch_id=EPOCH,
        )

    def tearDown(self):
        self.gateway.close()
        self.host.close()
        self.temp.cleanup()

    def turn(self,renderer,*,now=100,lease_ms=50, fault=None):
        return AuthorizedLaboratoryTurn(
            self.host,self.gateway,renderer,
        ).propose_and_execute(now_ms=now,lease_ms=lease_ms,fault=fault)

    def test_host_executes_one_allowlisted_action_then_admits_perceived_feedback(self):
        model=ScriptedRenderer('{"action":"open_drawer"}')
        receipt=self.turn(model)
        self.assertEqual(receipt.action,"open_drawer")
        self.assertTrue(receipt.accepted)
        self.assertTrue(self.gateway.drawer_open())
        self.assertEqual(self.gateway.action_count(),1)
        self.assertEqual(self.host.pending_count(),0)
        self.assertEqual(len(model.inputs),1)
        prompt=model.inputs[0]
        self.assertIn("I notice",prompt)
        self.assertIn("8 degrees",prompt)
        self.assertNotIn("ENGINEER_SECRET",prompt)
        self.assertNotIn("private-record",prompt)
        self.assertNotIn('"drawer_open":',prompt)
        self.assertEqual(self.host.pending_count(),0)
        posted=self.gateway.publish_next_feedback(self.host)
        self.assertEqual(receipt,posted)
        self.assertIsNone(self.gateway.feedback_receipt())
        response=ScriptedRenderer("I might look inside.")
        result=SubjectOnlyRendererPort(self.host,response).deliver_next(now_ms=150)
        self.assertEqual(result.response,"I might look inside.")
        self.assertEqual(len(response.inputs),1)
        self.assertIn("The drawer opens.",response.inputs[0])
        self.assertIn("I notice",response.inputs[0])
        self.assertNotIn('"action"',response.inputs[0])
        self.assertNotIn("host-action-receipt",response.inputs[0])
        self.assertEqual(self.host.pending_count(),0)

    def test_action_effect_is_replayed_only_once_on_retry_after_commit_fault(self):
        model=ScriptedRenderer('{"action":"open_drawer"}')
        with self.assertRaisesRegex(RuntimeError,"injected crash"):
            self.turn(model,fault="after_action_commit")
        self.assertTrue(self.gateway.drawer_open())
        self.assertEqual(self.gateway.action_count(),1)
        self.assertEqual(len(model.inputs),1)
        self.assertEqual(self.host.pending_count(),1)
        # Lease remains held, so the first retry cannot re-render.
        self.assertIsNone(self.turn(model,now=149))
        # Lease expiry returns existing receipt and SKIPS model.
        result=self.turn(model,now=150)
        self.assertTrue(result.accepted)
        self.assertEqual(self.gateway.action_count(),1)
        self.assertEqual(len(model.inputs),1)
        self.assertEqual(self.host.pending_count(),0)

    def test_durable_restart_between_action_and_ack_skips_new_model_call(self):
        scripted=ScriptedRenderer('{"action":"open_drawer"}')
        with self.assertRaises(RuntimeError):
            self.turn(scripted,fault="after_action_commit")
        self.gateway.close()
        self.host.close()
        self.host=DurableIpseityHost(
            self.path,subject_id=SUBJECT,epoch_id=EPOCH,
        )
        self.gateway=LaboratoryActionGateway(
            self.path,subject_id=SUBJECT,epoch_id=EPOCH,
        )
        different=ScriptedRenderer('{"action":"inspect_lamp"}')
        receipt=self.turn(different,now=151)
        self.assertEqual(receipt.action,"open_drawer")
        self.assertTrue(self.gateway.drawer_open())
        self.assertEqual(self.gateway.action_count(),1)
        self.assertEqual(different.inputs,[])
        self.gateway.publish_next_feedback(self.host)
        self.assertEqual(self.host.checkpoint().last_sequence,5)
        self.assertEqual(self.host.checkpoint().last_tick,2)

    def test_publishing_feedback_recovers_after_organ_commit_but_before_marker(self):
        model=ScriptedRenderer('{"action":"inspect_lamp"}')
        self.turn(model)
        with self.assertRaisesRegex(RuntimeError,"after durable commit"):
            self.gateway.publish_next_feedback(self.host,fault="after_feedback_commit")
        cp=self.host.checkpoint()
        self.assertEqual((cp.last_tick,cp.last_sequence),(2,5))
        self.assertEqual(self.host.pending_count(),1)
        receipt=self.gateway.publish_next_feedback(self.host)
        self.assertEqual(receipt.action,"inspect_lamp")
        self.assertIsNone(self.gateway.feedback_receipt())
        self.assertEqual(self.host.checkpoint(),cp)
        self.assertEqual(self.host.pending_count(),1)
        text=ScriptedRenderer("I will carry on.")
        SubjectOnlyRendererPort(self.host,text).deliver_next(now_ms=180)
        self.assertIn("The lamp is lit.",text.inputs[0])

    def test_disallowed_actions_and_extra_keys_never_affect_world(self):
        invalid=[
            '{"action":"delete_database"}',
            '{"action":"open_drawer","shell":"rm -rf"}',
            '{"action":1}',
            '{"action":"open_drawer","target":"private"}',
            "I open the drawer",
            "",
            "[]",
            '{"action":"OPEN_DRAWER"}',
            '{"action":"open_drawer"}\n{"action":"open_drawer"}',
            '{"action":"open_drawer"}'*1000,
        ]
        for candidate in invalid:
            with self.subTest(candidate=candidate[:60]):
                with tempfile.TemporaryDirectory() as temp:
                    db=Path(temp)/"lab.sqlite"
                    with DurableIpseityHost(db,subject_id=SUBJECT,epoch_id=EPOCH) as host:
                        host.process(1,first_frame())
                        with LaboratoryActionGateway(db,subject_id=SUBJECT,epoch_id=EPOCH) as gate:
                            model=ScriptedRenderer(candidate)
                            result=AuthorizedLaboratoryTurn(
                                host,gate,model,
                            ).propose_and_execute(now_ms=100)
                            self.assertFalse(result.accepted)
                            self.assertEqual(result.action,"REJECTED")
                            self.assertFalse(gate.drawer_open())
                            self.assertEqual(gate.action_count(),1)
                            gate.publish_next_feedback(host)
                            reply=ScriptedRenderer("I understand.")
                            SubjectOnlyRendererPort(host,reply).deliver_next(now_ms=170)
                            self.assertIn("not recognized or permitted",reply.inputs[0])
                            self.assertNotIn("delete_database",reply.inputs[0])
                            self.assertNotIn("rm -rf",reply.inputs[0])

    def test_two_turn_chain_can_inspect_actual_open_drawer(self):
        first=ScriptedRenderer('{"action":"open_drawer"}')
        self.turn(first)
        self.gateway.publish_next_feedback(self.host)
        second=ScriptedRenderer('{"action":"inspect_drawer"}')
        result=self.turn(second,now=200)
        self.assertEqual(result.action,"inspect_drawer")
        self.assertTrue(result.accepted)
        self.assertIn("specimen tray",result.feedback)
        self.gateway.publish_next_feedback(self.host)
        feedback=ScriptedRenderer("I see it now.")
        SubjectOnlyRendererPort(self.host,feedback).deliver_next(now_ms=250)
        self.assertIn("specimen tray",feedback.inputs[0])
        self.assertEqual(self.gateway.action_count(),2)
        self.assertEqual(self.host.checkpoint().last_sequence,6)

    def test_inspection_of_closed_drawer_does_not_invent_visible_contents(self):
        self.turn(ScriptedRenderer('{"action":"inspect_drawer"}'))
        self.assertFalse(self.gateway.drawer_open())
        self.gateway.publish_next_feedback(self.host)
        heard=ScriptedRenderer("I cannot see inside yet.")
        SubjectOnlyRendererPort(self.host,heard).deliver_next(now_ms=180)
        self.assertIn("cannot see inside",heard.inputs[0])
        self.assertNotIn("specimen tray",heard.inputs[0])

    def test_renderer_failure_does_not_journal_or_ack_untrusted_output(self):
        error_model=ScriptedRenderer()
        with self.assertRaisesRegex(RuntimeError,"responses exhausted"):
            self.turn(error_model,lease_ms=50)
        self.assertEqual(self.gateway.action_count(),0)
        self.assertEqual(self.host.pending_count(),1)
        recovered=ScriptedRenderer('{"action":"inspect_lamp"}')
        self.assertIsNone(self.turn(recovered,now=149))
        self.assertTrue(self.turn(recovered,now=150).accepted)
        self.assertEqual(self.gateway.action_count(),1)

    def test_cross_subject_gateway_and_lease_refused(self):
        with self.assertRaises(ValueError):
            AuthorizedLaboratoryTurn(
                self.host,
                LaboratoryActionGateway(self.path,subject_id=SUBJECT,epoch_id="other"),
                ScriptedRenderer('{"action":"open_drawer"}')
            )
        with self.assertRaises(TypeError):
            self.gateway.receipt_before_model(
                type("FakeLease",(),{"outbox_id":1,"token":"fake"})()
            )
        self.assertFalse(self.gateway.drawer_open())
        self.assertEqual(self.gateway.action_count(),0)

    def test_scripted_demo_runs_one_full_action_feedback_cycle(self):
        from tools.laboratory_action_demo import run_demo
        report=run_demo()
        self.assertEqual(report["run_kind"],"scripted_offline_conformance")
        self.assertEqual(report["action"],"open_drawer")
        self.assertTrue(report["host_authorized"])
        self.assertTrue(report["laboratory_drawer_open"])
        self.assertEqual(report["actions_journaled"],1)
        self.assertEqual(report["source_events_processed"],5)
        self.assertEqual(report["subject_only_frames_delivered"],2)
        self.assertEqual(report["model_response_to_feedback"],
                         "I should look inside the open drawer.")

    def test_only_allowlisted_effects_and_small_surface(self):
        self.assertEqual(ALLOWED_ACTIONS,{
            "inspect_lamp","open_drawer","inspect_drawer",
        })
        with self.assertRaises(ValueError):
            self.gateway.publish_next_feedback(self.host,fault="bad_fault")
        self.assertIsNone(self.gateway.publish_next_feedback(self.host))

    def test_unauthorized_foreign_outbox_does_not_execute_and_epoch_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            foreign_db=Path(tmp)/"another.sqlite"
            with DurableIpseityHost(
                foreign_db,subject_id=SUBJECT,epoch_id=EPOCH
            ) as second:
                second.process(1,first_frame())
                other_lease=second.claim_next(now_ms=100)
                with self.assertRaises(ValueError):
                    self.gateway.record_action(other_lease,'{"action":"open_drawer"}')
                self.assertEqual(self.gateway.action_count(),0)

    def test_no_feedback_claim_without_valid_actual_subject_host(self):
        self.turn(ScriptedRenderer('{"action":"open_drawer"}'))
        with tempfile.TemporaryDirectory() as tmp:
            with DurableIpseityHost(
                Path(tmp)/"alien.sqlite",subject_id="alien",epoch_id="alien-epoch"
            ) as alien:
                with self.assertRaises(ValueError):
                    self.gateway.publish_next_feedback(alien)
        self.assertIsNotNone(self.gateway.feedback_receipt())


if __name__=="__main__":
    unittest.main()
