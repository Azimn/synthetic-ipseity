# Authorized laboratory action cycle — verified October 12, 2026

**Engineering result:** PASS on Python 3.11, 3.12, and 3.13. **Real language-model autonomy NOT tested.**

## Source and reproducibility

- Pull request: https://github.com/Azimn/synthetic-ipseity/pull/32
- Completed test run: https://github.com/Azimn/synthetic-ipseity/actions/runs/38208476124
- Real SQLite action gateway code: src/synthetic_ipseity/laboratory_action.py
- Reproducible scripted complete cycle: tools/laboratory_action_demo.py
- Negative controls, restart, denial and feedback tests: tests/test_laboratory_action.py
- Design and authorization protocol: docs/AUTHORIZED_LABORATORY_ACTION_V0_9_11.md
- Commands: python -m unittest discover -s tests -v; python tools/laboratory_action_demo.py --scripted

Each of the three CI jobs completed successfully. The main test suite ran **328 passing tests** per Python version. The separate actual scripted SQLite laboratory demonstration succeeded:

| Recorded engineering field | Result |
| --- | --- |
| Run type | scripted_offline_conformance |
| Action proposed | open_drawer |
| Host authorization | true |
| Drawer actually open after host effect | true |
| Durable actions journaled | 1 |
| Subject source events processed | 5 |
| Admitted subject-only frames delivered | 2 |

The original host frame contained observed temperature, a closed drawer and perceived action affordances. An unacquired engineer secret did NOT reach the renderer. A scripted action proposal was strictly validated and recorded as a real SQLite drawer-state change before the first admitted frame was acknowledged. Its result then became a NEW host-attested world observation projected through Synthetic Ipseity and delivered as a second first-person text frame.

## Additional tested failure surfaces

- Commands not in the allowlist, multiple JSON objects, extra keys, invalid JSON, shell-command attempts and prose pretending to be an action are denied without a drawer-state change.
- An action committed just before an injected crash is NOT repeated: the retry claims the same leased frame and returns the existing outbox-keyed result without invoking the model again.
- After an injected crash between host feedback commitment and journal feedback-marker update, replay verifies the reserved source cursor and actual first-person feedback frame and does not create a duplicate subjective observation.
- An unavailable renderer leaves the original frame pending for lease-expiry retry.
- Cross-subject events, missing matching host and invalid leases cannot perform laboratory actions.
- A drawer not opened remains opaque: the subject cannot see the specimen tray until an authorized open action occurs.
- Legitimately observed numbers remain available; engineer source identifiers and hidden tool secrets do not.

## Evidence boundary

This is NOT a simulated confirmation of cognitive superiority. A scripted callback demonstrated that the *architecture's mechanics* close the loop. It did NOT demonstrate a real LLM understanding the laboratory, a second mind, a persistent conscious stream, or a benefit over first-person prompts.

The action gateway is scoped to one trusted SQLite laboratory and a single writer during reserved feedback publication. Do not claim exactly-once network/physical effects, whole-host noninterference, general action intelligence or authenticated physical sensing from this test.

Next run the opt-in local Ollama adapter with the exact same allowed action interface, record raw proposals and host receipts, and measure real successes and denials separately. Model outputs are never automatically treated as autobiography.

This is a durable engineering milestone in the **existing** Synthetic Ipseity organ and can inform a later Pretorius Laboratory integration. It does not authorize transferring the system into a living character host without auditing that host's other model input and action routes.
