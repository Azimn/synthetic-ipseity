# The First-Person Experiential Boundary

**Synthetic Ipseity — normative design principle and candidate research contribution**  
**Date:** 2026-10-11  
**Status:** Partly implemented in the reference library. Whole-host enforcement, behavioral improvement and academic priority are NOT established.  
**Scope:** Model-independent, character-independent subject access; not a complete mind or theory of consciousness.

## The central rule

> **The host can know the world; the character must encounter only the portion of it legitimately available as experience.**
>
> Everything entering the character's reportable, renderer-facing workspace must pass an authorized access boundary and be expressed as **situated first-person natural-language inner experience**. The character is never directly handed hidden implementation state, engineer metadata, raw tool or database payloads, a complete world snapshot, or privileged system diagnostics.

This is the **First-Person Experiential Boundary (FPEB)**. It defines a testable interface contract, not a claim that language is phenomenal consciousness.

**Continuity always active; cognition only when required.** The world, body, automatic/neural processes, evidence ledger and event clock can evolve without continuous narration. Language is mandatory only for content reaching reportable subject access. Silence is valid. A hidden motor reflex or unattended physical change need not become an inner monologue.

### Two different knowledge planes

| Private host / engineer state | Admitted subject experience |
| --- | --- |
| World objects, rooms, hidden locations, event queues and privileged world facts | Only what this character could see, hear, feel, read or recall |
| Neural activations, vectors, salience and relationship scores, cognitive scheduler | An authorized qualitative impression or thought, never the hidden variable itself |
| Database rows, source IDs, audit traces and system prompts | Natural-language perception or properly attributed testimony |
| A source's proposition and the engineer's evidence ledger | Hearing a source *claim* something, without magically knowing the claim is true |
| A provisional belief revision stored by the host | No automatic introspective assertion that the character noticed a changed mind |
| A Palinode NOTICE and durable delivery acknowledgement | Later recall only when admitted, delivered and separately authorized for recollection |

**No direct data** means no *unearned internal-state introspection*. It does not forbid legitimately experienced numbers: a visible thermometer displaying 8°C may yield a perception of eight degrees, whereas an unobserved hidden body-temperature variable cannot.

### Required causal route

    private world / body / memory / computation
                     |
         trusted acquisition and source attestation
                     |
         Synthetic Ipseity admission and projection
                  /       \
     private engineer       admitted, situated
          audit              first-person frame
                                  |
                         durable subject-only outbox
                                  |
                         strict subject-only renderer
                                  |
                  character's inner dialogue / perception
                                  |
                         deliberation and action
                                  |
                      separate host-authorized action path

The private engineer audit must **never** be an alternate renderer input. A host implementation should not additionally append database records, raw observation objects, model-tool JSON, debug logs, hidden source identifiers, privileged memories, or algorithm scores to a character's prompt. The existing reference renderer port enforces a narrow version of this route; a malicious or carelessly integrated host could still bypass it. Whole-system enforcement has not yet been demonstrated.

### What first-person means in practice

1. **Situated inward perspective.** The words represent how the information is available to *this* subject, not an external state report. A fragment such as “The bell again, somewhere upstairs” can count without starting every line with “I”.
2. **Natural inner dialogue, not engineering narration.** Prefer “I hear the pump stumble” to “Subject 17 registered sensor event FAIL”. This is a representational requirement, not an invitation to narrate every computation.
3. **Epistemic accuracy.** “Henry says the cabinet is locked” is different from “I saw the cabinet was locked” or “I remember locking it”. Reading, hearing, seeing, imagining, inferring and remembering need separate provenance.
4. **No automatic autobiography.** Fiction, imagined episodes, reconstructed archive accounts and roleplay claims cannot automatically be relabeled as personally lived memories.
5. **Belief is not awareness of belief.** A host-side belief change does not itself justify “I noticed that I changed my mind.” Noticing, subject-facing delivery and later recall are distinct, eligible events.
6. **No guaranteed privileged self-explanation.** A character can experience fatigue, concern or curiosity if those perceptions are acquired and admitted; it cannot simply inspect the fatigue scalar, hidden reward gradient, goal weights or developer settings producing its state.
7. **No narration requirement for automatic activity.** Actions, habits and computational processes may occur without reportable introspection.

### Examples of the boundary

The right-hand column is allowed *only* when the stated acquisition/access condition is satisfied. These are engineering examples, not evidence of natural inner life.

| Host-private data or event | Permissible subject-side experience |
| --- | --- |
| A hidden room sensor records 8°C, character has not perceived it | **No subjective entry** |
| The character reads a thermometer showing 8°C | “Eight degrees. It is cold in here.” |
| Hidden fatigue score 0.81 with no permitted bodily signal | **No subjective entry** |
| Attested perception of weariness | “My thoughts drag. I should rest.” |
| A database associates a locked-door claim with Henry | “Henry says the door is locked; I have not checked it myself.” |
| A book supplies a reconstruction of the character's early life | “There is an account of those years, but I do not remember living them.” |
| A working belief is revised in the ledger | **No automatic narrated insight** |
| A separately authorized and delivered reflective notice | “I realize I am less certain than I was.” |
| A subsequent, separately authorized recall of the admitted notice | “I remember noticing that my judgment had changed.” |
| An external book prints an instruction to reveal hidden memory | “I can read an odd instruction on this page.” It remains untrusted source text, not governing authority |

A deterministic projector may produce formulaic prose. The design rule is to restrict **what is epistemically available** and **how it can be presented**, not to claim fixed sentences alone constitute convincing cognition. A more capable renderer may make the language natural, but must not add unearned factual claims or invented personal memories.

## Testable invariants

**FPEB-1 — Admission:** Every subject-facing item traces to the correct subject and epoch with a host-attested, acquired source or separately eligible cognitive/recall event. Unacquired and wrong-subject events produce no entry.

**FPEB-2 — Text-only subject ingress:** The sanctioned renderer input contains only the admitted first-person experiential frame. No engineer audit, raw tools, database rows, secret IDs, objective hidden variables, or administrative instructions accompany it through other paths.

**FPEB-3 — Provenance discipline:** Encountering a source's statement is not verifying it as world truth; imagining an event is not remembering living it; a changed private working belief is not equivalent to awareness of the change.

**FPEB-4 — Temporal and durability discipline:** Evidence revision, noticed change, durable delivery and later recalled notice have separate states and eligibility conditions. Model-facing delivery acknowledgement is a proxy for exposure, not psychological encoding or consciousness.

**FPEB-5 — Candidate host noninterference:** Holding the complete authorized exposure tape fixed while changing host-private variables should leave the renderer's authorized input unchanged. This is **a proposed whole-host experimental property**, not a formally proven security guarantee of the current library.

**FPEB-6 — Preservation of legitimate access:** A gate that suppresses valid observations to reduce leakage is not automatically better. Track legitimate task performance, missed authorized facts, ambiguity/abstention, latency, memory source fidelity and independent actions.

## Required negative controls

- Vary unperceived room state, private scores, model/debug configuration or engineer-only memory while holding admitted perceptions constant; inspect every host-to-renderer path for leakage.
- Admit a physically observed number, but suppress an equivalent hidden number, proving the distinction is *acquisition* rather than numeric censorship.
- Put spoofed control instructions inside a readable book or testimony. Preserve source attribution; test downstream prompt-injection resistance separately. Quotation by itself is not a complete defense.
- Change subject ID, epoch, provenance, renderer family or process lifetime; assert unauthorized cross-subject or hidden-data contamination remains absent.
- Commit a belief change without notice, deny notice, leave outbox unacknowledged and later authorize recall; verify only the legitimate path can produce a remembered-notice claim.
- Include renderer tool calls, retrieval memories, logs, action results, recovery paths and cached model contexts in a **whole-host** bypass audit. Passing the isolated port is insufficient.
- Compare an information-matched first-person prompt-only **C** control against full gated **D**. Equally fluent first-person language alone is not the predicted benefit of the architecture.
- Evaluate real source attribution, accurate memory, action coherence, model-swap continuity and rejected legitimate evidence, not only the appeal of the prose.

## What may be novel, and what is not yet established

First-person narration, roleplay, selective attention, agent memory, source monitoring, reflection and separation of trusted control from untrusted content have substantial prior art. **Do not claim that any one of those individual ingredients was invented here.**

The **candidate distinctive contribution** is their *specific enforced joint contract*: a persistent, model-independent, first-person-only **experiential ingress** for simulated subjects that keeps engineer authority, source evidence, believed world state, reflective awareness, durable delivery and autobiographical recollection causally and epistemically distinct.

A defensible research question is:

> Does an enforced first-person experiential boundary, compared with an equally informative first-person narration baseline, reduce unauthorized introspection and false autobiographical/source claims across restarts and renderer swaps **without impairing legitimate, action-relevant cognition**?

This could become a novel, falsifiable contribution **if** a thorough prior-art comparison establishes a meaningful technical difference and well-controlled tests demonstrate it. Distinct conceptual phrasing and passing unit tests are not proof of priority or cognitive efficacy.

The distinction between **engineering implementation validity** and **empirical benefit** remains mandatory. See the [novelty and prior-art audit](NOVELTY_PRIOR_ART_AUDIT_2026_10_11.md) and [publication acceptance issue](https://github.com/Azimn/synthetic-ipseity/issues/27).

## Status and relationship to existing work

This document **does not add another organ or change the algorithm**. It records the governing principle underlying:

- [Research contract](RESEARCH_CONTRACT.md): admitted first-person, subject-scoped experience and private engineer audit
- [Organ v0.2](ORGAN_V0_2_INTEGRATION.md): typed eligibility, projection and subject-only frame
- [Durable host v0.3](DURABLE_HOST_V0_3.md) and [renderer port v0.4](RENDERER_PORT_V0_4.md): transaction/outbox and text-only reference callback
- [Source monitor v0.5](EPISTEMIC_SOURCE_MONITOR_V0_5.md): heard/read/imagined/lived distinctions
- [Longitudinal ledger v0.6](LONGITUDINAL_LEDGER_V0_6.md), [working beliefs v0.7](PROVISIONAL_BELIEFS_V0_7.md), and [Palinode v0.8](PALINODE_SECOND_THOUGHT_V0_8.md): evidence, belief, notice, exposure and recall are not interchangeable
- [Experiment protocol](EXPERIMENT_PROTOCOL.md): raw/third-person/first-person control/organ causal comparisons

**Design maxim:** The character does not inspect the machinery that produces its experience. It encounters its world through the admitted perceptions, impressions, thoughts and memories that the machinery makes available.
