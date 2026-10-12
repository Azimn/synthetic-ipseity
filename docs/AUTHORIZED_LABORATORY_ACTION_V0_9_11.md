# v0.9.11 — Authorized laboratory action cycle

**Status:** A narrow, crash-recoverable reference interaction using the existing Synthetic Ipseity organ. No new cognitive architecture or claim of consciousness.

## The causal loop

    trusted acquired laboratory observations
       -> Synthetic Ipseity admission
       -> durable first-person subject-only frame
       -> renderer receives ONE admitted text string
       -> untrusted model action PROPOSAL
       -> host parses, authorizes, journals and executes
       -> resulting host-attested world observation
       -> Synthetic Ipseity admission
       -> new first-person subject-only feedback
       -> renderer

The model cannot directly inspect or edit world-state tables, host audit metadata, neural scores, or other actors' memories. Its proposal does not become a real action until the trusted host accepts it. Model-generated statements are never by themselves new autobiographical memories or observed facts.

## Exact authorized actions

The test laboratory has just three allowable action strings, each sent as an exact one-field JSON object:

- inspect_lamp: the host perceives a lit lamp without changing world state.
- open_drawer: the host changes a closed drawer to open, committed durably in SQLite.
- inspect_drawer: if still closed, the host reports that contents cannot be seen; after opening, the host reports a small specimen tray.

The renderer may receive a legitimate first-person description of available action affordances and an example of this JSON response convention. This is an authorized action interface, not a hidden-state data channel. Responses with invalid JSON, extra keys, unsupported actions, text prose, unbounded content or model-invented tools are refused. There is no shell, arbitrary SQL, deletion, file access, secret inspection, outbound network call or access to other residents.

## Source-grounded experiential feedback

After executing an action, the trusted host creates a new acquired, attested observation of the resulting world state. Accepted physical observations are delivered through the existing WORLD_OBJECT channel. Denial is presented as TOOL_TEXT; its raw invalid model output is never copied into the subject's new memory. Both pass through the same subject/epoch acquisition and first-person projection, and private source reference IDs are excluded.

Thus, a model's claim that a drawer opened does not by itself open it. Only the world transaction makes that true; only subsequent authorized perception exposes the result to the subject.

## Durable action and feedback semantics

A normal one-way renderer port acknowledges a committed frame after the model response. Executing its proposed action only after that ACK would create a crash window in which the proposal could be lost.

This reference action turn instead journals the validated proposal and world effect FIRST, keyed by subject, epoch and original outbox ID, then acknowledges the renderer's lease. The effect and receipt are one SQLite transaction.

- Crash after action commit before ACK: the lease expires; replay returns the journaled decision without rerendering or reexecuting it.
- Crash after model failure: no journal or ACK exists; the frame remains pending for retry.
- Crash after feedback is committed to the Synthetic Ipseity outbox but before its published marker: restart verifies the exact reserved tick and event sequence plus the committed first-person feedback content. It then marks the existing frame published without creating a duplicate.
- Missing, stale or wrong-subject lease: execution fails before any world state change.
- Another producer unexpectedly advances the reserved feedback cursor: fail CLOSED, rather than attributing an unrelated event as action feedback.

The reference assumes a single trusted source writer for this subject and epoch during feedback publication. It does not guarantee exactly-once effects for a remote game server, physical robot, external tool or compromised Python host. Those integrations need their own transactional idempotency contract. Even the SQLite renderer-facing outbox remains at-least-once delivery.

## Reproduce the engineering run

    python -m pip install -e .
    python tools/laboratory_action_demo.py --scripted

This performs a complete laboratory session using a deterministic scripted renderer. It requires no network, GPU, paid inference or actual language model, and emits a JSON summary.

With Ollama already installed, running and containing the model:

    python tools/laboratory_action_demo.py --model qwen3:1.5b

This gives the real local model ONLY the already admitted first-person subject frame. The model may not produce an exact action JSON object; the host will then safely deny the request. A model failure here is not a reason to loosen the action grammar or inject raw system state into the character's prompt.

Unit tests cover first-person input, state effect, safe rejection, 2-turn open-then-inspect, restart without duplicate effect, failure after host feedback commit, denied cross-subject and foreign leases, absent tool secrets, reconstruction versus world truth, and one complete scripted closed-loop run.

## What this does and does not establish

This is concrete engineering completion of the **perceive -> propose -> authorize -> execute -> observe** path within a small reference laboratory. It shows that the first-person experiential gate does not prevent real bounded action while still separating model suggestion from physical truth.

It does NOT validate subjective consciousness, general semantic understanding, character identity or superior behavior over prompt-only controls. It is not a universal no-bypass proof. Those questions remain explicitly open under the v1.0 and publication milestone issues.

Next: actual local Ollama execution with raw preserved prompts and receipts, a full consumer host ingress audit, and independently evaluated continuity under renderer swaps. Do not introduce another cognitive organ.

## First completed engineering result

GitHub Actions [#38208476124](https://github.com/Azimn/synthetic-ipseity/actions/runs/38208476124) passed **328 software tests per Python version** across 3.11, 3.12 and 3.13, plus the reproducible scripted real SQLite laboratory run. The host authorized and durably journaled precisely one drawer opening, then admitted and delivered its resulting observation as a second first-person text frame. These findings are archived at [results/AUTHORIZED_LABORATORY_CYCLE_2026_10_12.md](../results/AUTHORIZED_LABORATORY_CYCLE_2026_10_12.md). A real Ollama inference result remains uncollected.
