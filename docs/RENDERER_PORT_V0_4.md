# Subject-Only Renderer Port v0.4

Status: deterministic, opt-in reference renderer boundary. This is a library-level integration contract, not an isolation guarantee for every host. No real LLM or paid provider is required for testing.

## The trusted path

A host-owned adapter must create `Observation` values from acquired world, body, memory, or tool evidence. The standalone organ transforms eligible values into a derived first-person frame and persists it through the v0.3 durable host. A `SubjectOnlyRendererPort` consumes only the previously committed text from a validated delivery lease. The model callback is invoked with exactly one string argument.

```python
from synthetic_ipseity import DurableIpseityHost, SubjectOnlyRendererPort

def fake_model(first_person_context: str) -> str:
    return "I wonder what I should examine next."

with DurableIpseityHost(
    "subject.db", subject_id="example", epoch_id="life-1",
) as host:
    port = SubjectOnlyRendererPort(host, fake_model)
    delivery = port.deliver_next(now_ms=1000)
    if delivery:
        print(delivery.response)
```

The model callback receives no `Observation`, `SourceSignal`, `OrganCheckpoint`, numeric salience, policy score, audit record, object identifier, durable host instance, lease metadata, or world truth through this reference API. It receives only already admitted first-person experience content. The callback's generated response is not automatically recorded as lived memory or enacted as an external action. Those require later host-authorized perception, action, and provenance steps.

A successful, nonempty string response causes an acknowledgement. Exceptions or invalid responses preserve the pending outbox entry for retry after the lease expires. Rendering can happen more than once after a crash between external response emission and acknowledgement. The renderer callback is a trusted integration surface; prompts, provider API request construction, and memory ingestion in any actual consumer must still be audited.

## Rejected claims

This contract does not make an LLM treat quoted hostile instructions as harmless; it only preserves their subject-facing source context. It does not inspect hidden state in a renderer's own process, prevent callers using a raw model client, prove that a perceived world fact is true, or prevent an externally injected prompt from overriding control instructions. Those questions require whole-host trust separation and adversarial prompt-injection tests. Neither a first-person sentence nor a successful callback establishes that the organism experienced consciousness.

## Acceptance

The independent `tests/test_renderer_port.py` battery records exactly what a fake model receives and verifies that hidden telemetry, engineer source references, unattested tool returns, absent sensory inputs and reconstructed biography are handled through the existing access contract. It also tests restart handoff, failed rendering, at-least-once retry, output validation and the absence of automatic memory creation.

A production consumer is not authorized to claim a *no-bypass* integration until its actual prompt assembly, tools, scheduler, memory writes, outbound actions and model-provider control plane pass an independent end-to-end audit. See Issue #8.
