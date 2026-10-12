"""Checks that preprojected subject language survives the organ unchanged."""
import unittest
from synthetic_ipseity import Kind, SourceSignal, render_frame
from synthetic_ipseity.organ import AccessPolicy, Channel, Observation, SyntheticIpseityOrgan

def make(sequence=1, *, tick=1, acquired=True, attested=True,
         subject="pretorius", epoch="lab", channel=Channel.COGNITION):
    return Observation(
        sequence=sequence, tick=tick, epoch_id=epoch, channel=channel,
        signal=SourceSignal(
            subject_id=subject, kind=Kind.PROJECTED_SUBJECT_EVENT,
            value="I recall looking at the laboratory balance.",
            acquired=acquired, salience=1.0, source_ref="internal-receipt"),
        attested=attested)

class TrustedProjectionTests(unittest.TestCase):
    def test_verbatim_subject_language(self):
        organ = SyntheticIpseityOrgan("pretorius", epoch_id="lab")
        output = organ.step(1, [make()])
        self.assertEqual(render_frame(output.frame), make().signal.value)
        self.assertNotIn("internal-receipt", render_frame(output.frame))

    def test_denial_and_capacity(self):
        organ = SyntheticIpseityOrgan("pretorius", epoch_id="lab",
                                      policy=AccessPolicy(capacity=1))
        output = organ.step(1, [make(acquired=False), make(2)])
        self.assertEqual(len(output.frame.lines), 1)
        self.assertEqual(output.receipts[0].decision, "not_acquired")

    def test_restarted_cursor_cannot_replay(self):
        organ = SyntheticIpseityOrgan("pretorius", epoch_id="lab")
        organ.step(1, [make()])
        restored = SyntheticIpseityOrgan.restore(organ.checkpoint().to_dict())
        with self.assertRaises(ValueError):
            restored.step(2, [make(tick=2)])
        with self.assertRaises(ValueError):
            restored.step(2, [make(2, tick=2, subject="other")])
        self.assertEqual(restored.step(2, [make(2, tick=2)]).frame.lines,
                         (make().signal.value,))

    def test_wrong_channel_rejected(self):
        with self.assertRaises(ValueError):
            make(channel=Channel.WORLD)

if __name__ == "__main__":
    unittest.main()
