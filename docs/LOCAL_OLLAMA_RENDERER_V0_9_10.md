# v0.9.10: Local Ollama First-Person Renderer Adapter

**Engineering status:** Optional library adapter, standard-library-only, offline-testable.  
**Purpose:** Run the existing durable subject-only experiences through a real local inference engine **without a paid API or a raw host-data channel**.  
**Scientific status:** No actual model inference has been run in GitHub CI for this adapter. No claim of improved behavior, human-like inner life, consciousness, or whole-platform security.

## Trust boundary and permitted data

The reference path is:

    acquired/attested SourceSignal
      -> SyntheticIpseityOrgan
      -> atomic SQLite subject frame outbox
      -> SubjectOnlyRendererPort
      -> LocalOllamaRenderer(one admitted text string)
      -> Ollama on 127.0.0.1:11434/api/generate

The adapter sends a **single-frame stateless prompt** equal to the permitted subject-only text. Inference payload fields are limited to a model name, that prompt, a fixed non-streaming flag and a fixed temperature-zero setting. There are **no** hidden host state, private source IDs, engineer audit fields, raw tools, world snapshots, conversational history or user-controlled system prompts inserted in this path.

A local response is a model-generated text string, **not an attested new memory, inner experience or authorized world action**. It must be separately checked and admitted before it can become part of the simulated character's future subjective record.

The endpoint is **fixed** at http://127.0.0.1:11434/api/generate (not a user-supplied URL), with proxies and redirects disabled. Model names are validated against a small identifier grammar, rejecting URL-like and traversal-like forms. No API credentials, paid inference keys or remote HTTP providers are supported. The adapter has a response size bound, configurable timeout and strict nonblank JSON response validation.

This is only one trusted process-local integration path. Host code with its own database or model client remains able to violate the boundary. A malicious retrieved source can still influence real language-model outputs even when framed as first-person perceived text; quotation is not a universal prompt-injection defense.

## Running locally

**Requirements:** Python 3.11+, installed package, Ollama running locally and a model already downloaded in Ollama.

    python -m pip install -e .
    ollama pull qwen3:1.5b
    python tools/ollama_subject_demo.py --model qwen3:1.5b

The demo uses a temporary fictional subject and SQLite database. It creates a hidden secret tool result (denied), an observed instrument reading (“8 degrees”), a heard statement by Henry, and a reconstructed account of childhood. It commits the event cursor, closes the host, reopens the durable record, and then gives the local Ollama renderer **only** the subject frame.

To try another already installed model, use --model llama3.2:3b or another local model tag. Do not infer that renderer changes are psychologically meaningful from a single response. The default model is an example only; this repository does not download weights or test the user's local model availability.

## Regression evidence required

The adapter's tests simulate the transport (NO actual internet or local server needed). They inspect each JSON request to ensure the subject text is the **only** contextual material; a hidden tool secret and source IDs do not enter the request. Other controls test lawful visible numbers, spoofed system instructions *as quoted seen content*, transport errors, invalid replies, lease retry after renderer failure, model tag validation and same subject prompt across different model choices.

The end-to-end [reference host FPEB invariance gate](FPEB_END_TO_END_GATE_V0_9_9.md) still runs 32 hidden-state variants through the real SQLite host/restart/callback path. This is a privacy/integration conformance test, not a real Ollama behavior experiment.

## Next engineering and scientific blockers

1. Run the demo against a real local Qwen/Llama checkpoint and archive actual consent-safe prompts and model output with checksums.
2. Audit the actual game/agent host wiring, especially any **other** prompt assembly, tool-result injection, retrieval, action feedback, persistent context or model invocation that bypasses this library path. Without that inventory, no global no-bypass guarantee is defensible.
3. Implement authorized action-feedback delivery and explicit optional model-output memory review; never automatically certify a generated assertion as observed truth.
4. Test actual renderer swaps with an adequate case corpus and fair information-matched first-person prompt-only controls.
5. Complete independent human source annotations for natural-language semantic validation.

The first-person requirement is **input admission**, not a language-generation guarantee. Even a local model may reply in third person, hallucinate details or follow hostile quoted instructions. A future response-form validator would require a separate test and protocol; do not quietly score every text response as an authentic subjective thought.

No novel cognitive organ is added. This adapter makes the already-existing organ **directly executable with free local inference** when the user's host has Ollama installed.
