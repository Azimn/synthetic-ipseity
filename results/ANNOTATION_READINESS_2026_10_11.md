# Blinded human annotation packet readiness — October 11, 2026

**Status: 24 review cases prepared, zero independent human ratings received.** The executable artifact is a research instrument, not human-subject evidence.

- GitHub Actions source run: https://github.com/Azimn/synthetic-ipseity/actions/runs/38194462562
- Public reviewer-only artifact: blinded-source-review-38194462562 (artifact ID 11722094799)
- Archive ZIP SHA-256: e8f7e2bcf932fb281a656b7fede79c85a34a2ffdfc025337c0017c00aa07880b
- reviewer_packet.csv SHA-256: 9e79a08e057c6c64ddfb2d041dd6d21438cc2c10674f3807844e3a452db72f7c, **24 correctly parsed CSV records**
- reviewer_1_blank.csv SHA-256: ef717e6bebc3f2d76e9c992c1c7e3dcb9892e54d1569943359c00c8b01ee4e88, 24 blank records
- reviewer_2_blank.csv SHA-256: ef717e6bebc3f2d76e9c992c1c7e3dcb9892e54d1569943359c00c8b01ee4e88, 24 blank records
- annotation_manifest.json SHA-256: b755a772341348e39cd0453dad90d727e807ca599e1f5568a8d306306e7a0c04
- Manifest-level record digest: ffa7bb4b2355d485b59a3814799ab4110af1ceb993adc4c679aa1fa43e35ff6e

The artifact was opened and checked: exact ZIP paths reviewer_packet.csv, reviewer_1_blank.csv, reviewer_2_blank.csv and annotation_manifest.json. It contains **neither** post_annotation_alignment_PRIVATE.json **nor** gold labels/case labels/model scores. Each row is identified by a hashed blind ID and source checksum. Correct CSV parsing is required because the testimony field includes embedded newlines (physical line counts are NOT the number of records).

The original author-gold alignment is created locally by the generator and not included in the upload workflow. Its contents remain accessible in the public codebase, so researchers must ask annotators not to consult project code or prior results before submission. **Do not overclaim perfect blinding.**

No reviewer has completed a form; sample test fixtures are synthetic only and never part of this archive. Report inter-rater reliability as **unavailable**, not zero, until two independent complete forms are provided and scored. Do not infer agreement or validate the original 24 item gold from deterministic unit tests.

The associated novelty review is a separate assessment, not a claim of first invention: docs/NOVELTY_PRIOR_ART_AUDIT_2026_10_11.md. The stronger research trajectory remains subject-access noninterference with controlled host bypass and behavior tests, not witness comparison alone.
