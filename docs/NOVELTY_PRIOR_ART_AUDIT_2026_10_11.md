# Synthetic Ipseity: Prior-Art and Novelty Audit v0.1

**Date:** 2026-10-11  
**Status:** working, adversarial, non-exhaustive prior-art audit. **Novelty is unproven**; no survey can establish absolute priority. 
**Scope:** [Synthetic Ipseity](../docs/RESEARCH_CONTRACT.md) implementation through v0.9.7, not all adjacent Azimn cognitive repositories.
**Research objective:** identify an academically defensible contribution and stop claiming originality for known mechanisms.

## Executive verdict

The current package is a competent **engineering prototype of provenance-constrained, subject-scoped experience admission**, not yet a validated advance in character cognition. Source monitoring, reflection, narrative memory, epistemic state revision, durable event handling and data/control isolation are all established *ideas*. A potentially distinctive **system-level contribution** is an experimentally testable **Subject-Access Noninterference Contract (SANC)**:

> In an artificial character system, authoritative implementation-native data, source claims, provisional belief revisions and metacognitive exposure records remain separately governed. Only host-attested, subject-acquired observations cross a typed, capacity-limited boundary into first-person renderer input; the durable engineer-only state and visible subject history advance atomically, while a belief revision, noticing it, delivery, and subsequent recollection are independently gated. Unauthorized or merely imagined history must not become lived autobiography even after a restart or renderer swap.

This is a **candidate formulation**, NOT a claim that nobody has done it before. It combines patterns established elsewhere. The originality question is whether the **specific enforceable invariants, construction and controlled longitudinal behavioral tradeoffs** yield a new empirical/design result.

SANC names an existing package contract; do not implement a second organ, identity system or architecture simply to match the acronym. A more modest paper claim is "An open-source, audited subject-access boundary for persistent AI characters, with negative results on source-competence measurement."

## Nearest related work and the overlap we must concede

| Related work / primary reference | Established contribution overlapping ours | Not justified to claim as new | Potential differential test or claim |
| --- | --- | --- | --- |
| Johnson, Hashtroudi & Lindsay (1993), *Source Monitoring*, Psychological Bulletin, DOI 10.1037/0033-2909.114.1.3 | Distinguishing memory origins, experienced and imagined information and source misattribution is classic cognitive psychology | "We invented source monitoring" or a phenomenological theory | Engineering realization of strictly typed, subject-scoped source eligibility and a traceable denial path |
| Park et al. (2023), *Generative Agents: Interactive Simulacra of Human Behavior*, UIST, DOI 10.1145/3586183.3606763 | Agent memory stream, reflection, planning and believable simulated action | Memory + reflection + agency, introspective summaries | Independent gate controlling what is even *available* to a renderer as subject-accessible evidence; paired action tests |
| Packer et al. (2023), *MemGPT: Towards LLMs as Operating Systems*, arXiv:2310.08560 | Persistent memory tiers and controlled context movement | Persistent external memory, context paging or cross-session continuation | External storage and causal ledger separate from subject-first-person exposure, not merely a memory retrieval policy |
| Sumers et al. (2024), *Cognitive Architectures for Language Agents*, TMLR / arXiv:2309.02427 | Modular agent memory, state and action space as cognitive architecture | "First modular cognitive architecture for LLM agents" | Narrow auditable observer/subject interface as a replaceable subcomponent with proven local invariants |
| Shinn et al. (2023), *Reflexion*, NeurIPS / arXiv:2303.11366 | Linguistic self-reflection and stored feedback for subsequent choices | "Self-reflection leads to changed behavior" or a second-thought process | Gating separately (a) belief change, (b) attested notice, (c) acknowledged delivery and (d) future recall, each revocable/testable |
| Zhong et al. (2024), *MemoryBank*, AAAI, DOI 10.1609/aaai.v38i17.29946 | Long-term personalized companion memory, selective updating and reflection | Personality-continuity memory store or selective remembering | Preserve evidence history and prospective belief without replacing the autobiographical memory engine |
| Debenedetti et al. (2024), *AgentDojo*, NeurIPS / arXiv:2406.13352 | Untrusted agent tool content and prompt injection as testable security threat | "First separation of trusted instructions and external text" | Demonstrate actual renderer-ingress restrictions and negative introspection/cross-subject tests under attack |
| Debenedetti et al. (2025), *Defeating Prompt Injections by Design* (CaMeL), arXiv:2503.18813 | Control/data separation and capability-constrained flows around LLM agents | "First information-flow security architecture" or "provably injection-safe" | Scope the boundary to *subject-experience eligibility*, not exfiltration; acknowledge **trusted host** and no process-level bypass proof |
| Uddin et al. (2026), *From Recall to Forgetting: Benchmarking Long-Term Memory for Personalized Agents* (Memora), ACL Findings, DOI 10.18653/v1/2026.findings-acl.1337 | Temporal updates/obsolete-memory errors, remembering/reasoning and human-evaluated memory benchmark | "First memory revision or anti-obsolete-memory benchmark" | Evaluate experience admission + belief-vs-lived-recollection origin under model swaps, not only obsolete fact retrieval |

**Verified entry URLs** (primary sources):
- https://pubmed.ncbi.nlm.nih.gov/8346328/
- https://dl.acm.org/doi/10.1145/3586183.3606763
- https://arxiv.org/abs/2310.08560
- https://arxiv.org/abs/2309.02427
- https://papers.nips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html
- https://ojs.aaai.org/index.php/AAAI/article/view/29946
- https://arxiv.org/abs/2406.13352
- https://arxiv.org/abs/2503.18813
- https://aclanthology.org/2026.findings-acl.1337/

This search is not exhaustive. Before a journal submission, add backward/forward citation tracking of these works, published 2025–2026 agents, and system-level verified noninterference security architectures. Do not present absence from this short list as proof of invention.

## Claimed-versus-measured matrix

| Candidate manuscript claim | Current status | Acceptance test needed |
| --- | --- | --- |
| A narrow first-person subject-only projection and audit-plane separation can be implemented | **Demonstrated in the standalone reference** by unit tests, typed frames and renderer API | Independent hostile-review integration: enumerate *all* host-to-model paths, including logs, retrieval, tools and retries |
| Durable ledger retains source revisions without promoting source reports to truth | **Demonstrated in local reference construction/tests** | Crash/restart isolation tests with *real* host action side effects and attacker-supplied source text |
| Belief changes, noticing changes and recalling noticed changes are distinct state transitions | **Implemented** as separate host-attested/delivery-gated records | Real renderer with blind evaluations of whether subject behavior follows these states; no claim of spontaneous realization |
| Organ improves identity continuity beyond matched first-person prompting | **NOT SHOWN** | Multi-model, information/token-matched C-vs-D ablation; blinded action coherence/recollection provenance; enough independent episodes |
| Current natural-language semantic measurement is adequate for the behavioral comparison | **FAILED gate**: v0.9.7 Qwen3B 58/96 (60.4%), paired agreement 1/8, contradiction 6/8, insufficient 3/8, independent verifier 1/8 | Independent annotators and new blind data; extraction-then-compare baseline; verified source attribution |
| The system enforces security against compromised integration | **NOT SHOWN**; trusted-host contract only | Threat model, host audit, OS/process privilege separation and prompt-injection/intent laundering tests |
| Synthetic Ipseity causes subjective consciousness | **NOT CLAIMED or measurable here** | Excluded as a scientific claim from this program |

## Falsifiable novelty hypotheses

**H-N1: Subject-access leakage reduction.** Against information-matched C (first-person textual control), D prevents more unauthorized internal-state disclosure, cross-subject contamination and false lived-recall attribution *without* unacceptable semantic-task degradation. Outcome: attack success per independent episode, preserved legitimate performance and latency; not word count alone.

**H-N2: Source-history attribution across renderer swaps.** In longitudinal multi-claim settings, D improves accurate speaker/source attribution and abstention when the renderer checkpoint changes, compared with C with the same evidence/tokens. Include copied autobiographies of other subjects, hostile source text and corrections; report false-personal-memory rate and refused legitimate experiences.

**H-N3: Metacognitive exposure fidelity.** Given an attested belief revision, D distinguishes merely changing a working view from noticing it, and from later acknowledged-recall eligibility. This should yield fewer invented reflective memories *in subsequent action/case reasoning* than a baseline given equivalent facts. The Palinode transport code by itself does not establish the behavioral finding.

**Failure conditions:** no D-over-C incremental effect; material loss of legitimate experience; higher hallucination/avoidance or verbosity; results disappear at token parity or under a renderer swap; source parser cannot support independently adjudicated natural-language cases. Negative findings must remain published.

## Why the current pilot series is valuable but not evidence of efficacy

The research notebook has unusually detailed *negative* engineering observations (schema floor, letter-position priors, source-versus-world-truth ambiguity, natural-language agreement/verification failures). A methodological contribution may be a reproducible **evaluation and adversarial validation suite**, provided it is redesigned with independent annotations and proves diagnostic sensitivity. Do not relabel known grammar parsing (80/80 and 320/320) as natural-language semantic intelligence.

v0.9.7 observed a highly asymmetric local-model deficit. Before any model-assisted source extraction is treated as a "fix", register a new extraction-first study on *fresh* heldout examples; show each speaker/object/time/modality extraction, ambiguous/unknown abstention, comparison accuracy and calibrated coverage separately. Do not optimize against the publicly seen 24 examples.

## Publication pathway and recommendations

1. **Most defensible near-term paper:** an **artifact/system-design report** on subject-access noninterference, source/provisional-belief/reflective-recall provenance, crash-consistent delivery and renderer serialization. Be explicit that isolated unit tests are evidence of engineering conformance, not universal security.
2. **Needed for a stronger cognition paper:** a validated reference reader or independently double-annotated corpus, blinded comparison of source and belief attribution across *real model swaps*, C/D information parity, and action consequences. A small passing result on 24 researcher-labeled cases would not suffice.
3. **Optional architecture paper hypothesis:** articulate host-side subject-access privileges as a *separate system contract* from agent memory retrieval or code execution control. This may be a distinctive framing/combination, but remains unproven as priority or added value until contrasted experimentally with CoALA, MemGPT/Letta, CaMeL and equivalent first-person prompting.
4. **Do not:** claim a new memory science, self-awareness, independent source truth detector, first prompt-injection defense, proprietary security guarantee, or consciousness from current evidence.

**Decision:** Keep the stand-alone organ architecture frozen. Put engineering work into whole-path noninterference tests and sound measurements. The strongest potential contribution is the *precise, auditable separation between objective states, admitted subjective experiences and the formation of apparently autobiographical recollection*, plus controlled proof of its utility beyond plain language reformulation. This audit is a research judgment as of 2026-10-11, not a priority certification.
