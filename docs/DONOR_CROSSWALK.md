# Existing work and ownership crosswalk

Verified against connected repositories on 2026-10-10. This inventory records *existing design and tests*, not an assertion that donor production paths are fully integrated.

| Donor | Existing surface | What standalone Synthetic Ipseity should learn | What it must not copy |
|---|---|---|---|
| [DUCK](https://github.com/Azimn/DUCK) | `duck/access.py` SubjectAccessFirewall; `duck/subjective.py` SubjectiveMoment; `tests/test_subjective_access.py` | Numerical state becomes bounded first-person feelings; introspectively inaccessible causes stay hidden; cognition can operate without inner speech | DUCK's subject state, character history, and goal system |
| [The Doctor Lives](https://github.com/Azimn/The-Doctor-Lives) | `doctor_lives/phenomenology.py` PhenomenalEvent; `doctor_lives/projection.py` deterministic projectors; `doctor_lives/awareness.py` gating; `PHENOMENAL_PROJECTION_CONTRACT.md` | Typed representations, separate objective provenance and subjective source, attentional arbitration, no-bypass contract | Pretorius biography, production-state schema, developmental model |
| [The Doctor Lives](https://github.com/Azimn/The-Doctor-Lives) | `FIRST_PERSON_SUBJECT_INTERFACE_CONTRACT.md` | Strengthen exclusion of raw render request fields, internal thought leakage, and fake provenance; integrate by adapter only | Treating planned production integration as already complete |
| [Pretorius Laboratory](https://github.com/Azimn/Pretorius-Laboratory) | `pretorius_lab/perception.py` host-attested structured observations | A strong objective evidence source and future spatial continuity trial | Assuming raw observation dictionaries are themselves conscious experience |
| [Artificial Life Research Journal](https://github.com/Azimn/Artificial-Life-Research-Journal) | `research-questions/RQ-004-subjective-access.md` | Align isolated empirical program with subjective-access question | Conflating philosophical working principle with validated improvement |

## Integration strategy

The standalone package owns its contract and tests. External projects supply small **adapters** from their existing signals to this package's supported inputs, then consume only `SubjectFrame` in the subject channel. Hosts retain their own sources of truth, memory models, action systems, policy rules, and audit trails.

Do not swap production UPPB implementation for this much smaller prototype. Run equivalence and anti-leak comparisons first, including cases where donor behavior is more expressive. Integration requires an opt-in pull request in the downstream project and its own no-bypass audit.

## Historical priority

The research contribution is the independently specified, enforced, ablated subject-access architecture and its empirical consequences. It is not a claim to have invented the first-person perspective, subjectivity, cognitive access control, or any single psychological mechanism.
