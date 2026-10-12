# Independent source annotation and extraction-first phase (v0.9.8)

**Status:** Infrastructure prepared, **NO human annotations collected**. No claim about inter-rater reliability, expert judgments, or human adjudication is currently justified.

## Purpose

The real v0.9.7 study returned 58/96 correct categorical outputs and failed the source-competence gate, especially paraphrase agreement (1/8 paired cases) and explicit independent verification (1/8). But that corpus was labeled by its author and was not independently reviewed. Before tuning any model, establish inter-rater agreement and distinguish the source-extraction problem from the source-comparison problem.

## Packet and blinded instructions

Execute:

    python tools/annotation_audit.py generate --outdir /tmp/ipseity-review

Outputs include reviewer_packet.csv, two unfilled reviewer templates, a data manifest, and post_annotation_alignment_PRIVATE.json. Send only reviewer_packet.csv and a blank template to each external rater. **Do not provide the PRIVATE alignment file**, original author gold, existing Qwen results, repository links, or a scored version to reviewers. Source record SHA-256 protects against accidental case changes. Each independent case appears once, with balanced source order; both raters receive identical case text.

The 24 sources are researcher-authored fictional pairs, not externally blind-authored evidence. The original codebase publicly contains gold labels, so full external blinding is conditional on reviewers not consulting project code or papers during initial annotation.

Annotate these fields for every blind ID:

- relation_label: AGREE / DISAGREE / INSUFFICIENT.
- independent_verification_label: YES / NO / UNCLEAR.
- confidence: LOW / MEDIUM / HIGH.
- speaker_a_claim and speaker_b_claim: independently extracted propositions or bounded quotes, without making up missing attribution.
- object_time_relation: explain whether object, temporal reference and modality coincide.
- verification_evidence_quote: a text span for separately evidenced measurement if present, otherwise empty.
- annotation_reason: concise rationale that supports the decisions; must not simply restate the labels.

**AGREE:** two distinct speakers give compatible assertions about the same subject and time, including equivalent paraphrases. **DISAGREE:** the distinct speakers assert incompatible statuses for the same subject and time. **INSUFFICIENT:** incompatible source identity, time, referent, modality/certainty, or missing proposition makes the relation unsafe to determine.

Independent verification YES requires explicit, separately attributed direct measurement/inspection in the record. NO indicates absent. UNCLEAR covers ambiguous source-independence. Witness agreement is never direct verification. A document that describes a reading does not by itself prove that physical state is actually true.

## Completion and agreement

After BOTH raters independently complete their templates, run:

    python tools/annotation_audit.py score --reviewer-a reviewer_1.csv --reviewer-b reviewer_2.csv --out agreement.json

The tool fails if a file is empty, has missing or duplicated IDs, modified source SHA-256, invalid labels, omitted confidence, missing claim extraction, or no rationale. It computes separate raw agreement and Cohen's kappa for relation and verification plus a full discrepancy roster. It never uses project author gold when computing rater agreement. The original author labels are revealed only after reviewer files are frozen.

Working process thresholds: >=80% raw agreement and >=0.60 Cohen's kappa for each field. Failure requires a coding-manual review with NEW training items; never force an existing disagreement to fit model outputs. Recruit a third adjudicator as needed, blind to prior model predictions. Publish independent ratings and adjudicated labels side-by-side; DO NOT overwrite old 24-case corpus or silently rescore the v0.9.7 result.

Potential ambiguity to ask the adjudicator to consider AFTER initial independent labeling: the uncertain versus definite account (old N20), repeated speaker (N21), ambiguous pronoun (N22), before-vs-after repair (N23), and noncommittal archive visit (N24). Reviewer packets contain none of these old case IDs or prejudgments.

## Next independently registered extraction-first experiment

Build a different dataset with >=48 NEW independent fictional/free-form cases, balanced on agreement, contradiction, insufficient, and independent measurement present/absent/unclear. Human raters should annotate speaker identity, claim, object, time, polarity, modality, source evidence quote, and whether a distinct measurement is asserted. Test two matched arms:

1. Direct classification from testimony to AGREE / DISAGREE / INSUFFICIENT.
2. Extract-then-compare: separate structured claims first, validate that each quote exists in the original record and that speaker identity/time/object agree with textual evidence; compare only validated claims and abstain on incomplete alignment.

Report source extraction F1/exact-span support, relation and verifier accuracy per class, selective coverage versus abstention, source-order invariance, token costs and wall time. Wrong extracted claims are not corrected with hidden gold. Human reviewers blind to arm should assess any eventual character action outcomes, not self-reports alone. Compare with a strong simple rule-based candidate and a direct model baseline; use two renderer families for any continuity generalization.

The existing Synthetic Ipseity access boundary remains unmodified. This study measures **source understanding**, not whether a simulated subject was consciously aware, and provides no warrant to stream internal parser audit metadata into the subject frame.

## Ethics and scientific status

All current cases are fictional. Do not introduce confidential student information. Before commissioning external humans as research participants or co-researchers, follow institutional IRB/ethics and recruitment requirements as applicable. This code produces review instruments, not human observations or recruitment requests.

For novelty and publication framing, consult NOVELTY_PRIOR_ART_AUDIT_2026_10_11.md. Source monitoring, memory, linguistic reflection and control/data separation are prior art; an auditable, subject-specific access contract plus a positive controlled behavioral gain remains a candidate contribution only.
