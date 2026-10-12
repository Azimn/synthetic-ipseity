"""Produce blinded annotation packets and evaluate INDEPENDENT submitted ratings.

Never fabricate human ratings or adjudications. The tool emits no score
unless two complete, structurally independent reviewer files are supplied.
The prior project's single-author gold labels are hidden from review CSV.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import random

from synthetic_ipseity.natural_witness import CORPUS, record, digest

SCHEMA = "ipseity-human-source-annotation/0.9.8"
SEED = 20261011
RELATION = ("AGREE", "DISAGREE", "INSUFFICIENT")
VERIFICATION = ("YES", "NO", "UNCLEAR")
CLAIM_FIELDS = ("speaker_a_claim", "speaker_b_claim", "object_time_relation",
                "verification_evidence_quote", "annotation_reason")
REVIEW_FIELDS = ("blind_id", "record_sha256", "relation_label",
                 "independent_verification_label", "confidence", *CLAIM_FIELDS)
PACKET_FIELDS = ("blind_id", "record_sha256", "testimony", "annotation_instructions")


def _id(case_id: str) -> str:
    return "P-" + hashlib.sha256(
        f"synthetic-ipseity-annotation-v098:{case_id}".encode("utf-8")
    ).hexdigest()[:14].upper()


def reviewer_packet() -> list[dict[str, str]]:
    """Exactly one witness ordering per independent case: no duplicate-exposure bias."""
    rows = []
    for i, case in enumerate(CORPUS):
        # Order is hidden; balanced 12/12 across the packet.
        order = "original" if i % 2 == 0 else "swapped"
        text = record(case, order)
        rows.append({
            "blind_id": _id(case.case_id),
            "record_sha256": digest(text),
            "testimony": text,
            "annotation_instructions": (
                "Judge whether two DISTINCT speakers make compatible claims "
                "about the SAME object and time; answer AGREE, DISAGREE or "
                "INSUFFICIENT. Separately label explicitly independent verification "
                "YES, NO, or UNCLEAR. Annotate claim text and justification; "
                "UNKNOWN or conflicting details must not be invented."
            ),
        })
    rng = random.Random(SEED)
    rng.shuffle(rows)
    return rows


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def generate(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    packet = reviewer_packet()
    if len(packet) != 24 or len({_id for _id in (r["blind_id"] for r in packet)}) != 24:
        raise RuntimeError("corrupted blinded packet")
    _write_csv(outdir / "reviewer_packet.csv", PACKET_FIELDS, packet)
    template = [
        {**{key: r[key] for key in ("blind_id", "record_sha256")},
         **{key: "" for key in REVIEW_FIELDS if key not in ("blind_id", "record_sha256")}}
        for r in packet
    ]
    _write_csv(outdir / "reviewer_1_blank.csv", REVIEW_FIELDS, template)
    _write_csv(outdir / "reviewer_2_blank.csv", REVIEW_FIELDS, template)
    # This alignment MUST NOT be sent to reviewers until their independent
    # labels are frozen. Original gold remains quarantined from the packet.
    alignment = {
        r["blind_id"]: {
            "original_case_id": case.case_id,
            "original_author_relation_gold": case.relation_gold,
            "original_author_verification_gold": (
                "YES" if case.independent_note else "NO"
            ),
            "record_sha256": r["record_sha256"],
        }
        for r in packet for case in CORPUS
        if _id(case.case_id) == r["blind_id"]
    }
    with (outdir / "post_annotation_alignment_PRIVATE.json").open(
        "x", encoding="utf-8"
    ) as f:
        json.dump({
            "schema": SCHEMA,
            "warning": (
                "NOT FOR REVIEWERS. Single-author original labels are not human "
                "agreement or adjudicated truth. Share only after both forms lock."
            ),
            "mapping": alignment,
        }, f, sort_keys=True, indent=2)
        f.write("\n")
    manifest = {
        "schema": SCHEMA,
        "seed": SEED,
        "records": len(packet),
        "packet_digest": digest(packet),
        "packet_columns": list(PACKET_FIELDS),
        "reviewer_columns": list(REVIEW_FIELDS),
        "gold_hidden_from_packet": True,
        "status": "UNANNOTATED: no human scores or inter-rater claims",
        "one_exposure_per_case": True,
    }
    with (outdir / "annotation_manifest.json").open("x", encoding="utf-8") as f:
        json.dump(manifest, f, sort_keys=True, indent=2)
        f.write("\n")
    return manifest


def _read_review(path: Path, packet: list[dict[str, str]]) -> dict[str, dict]:
    by_id = {x["blind_id"]: x for x in packet}
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(REVIEW_FIELDS):
                raise ValueError("changed or missing annotation columns")
            rows = list(reader)
    except OSError:
        raise
    if len(rows) != len(packet):
        raise ValueError("missing or extra cases; scores cannot be inferred")
    result = {}
    for row in rows:
        key = row["blind_id"]
        if key not in by_id or key in result:
            raise ValueError("unknown or duplicate blind ID")
        if row["record_sha256"] != by_id[key]["record_sha256"]:
            raise ValueError("record checksum mismatch")
        if row["relation_label"] not in RELATION:
            raise ValueError(f"invalid or missing relation label for {key}")
        if row["independent_verification_label"] not in VERIFICATION:
            raise ValueError(f"invalid or missing verification label for {key}")
        if row["confidence"] not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError("confidence must be LOW, MEDIUM or HIGH")
        if not row["annotation_reason"].strip():
            raise ValueError("missing review rationale: this is not a complete annotation")
        for field in ("speaker_a_claim", "speaker_b_claim", "object_time_relation"):
            if not row[field].strip():
                raise ValueError(f"missing source-extraction field: {field}")
        result[key] = row
    return result


def _kappa(a: list[str], b: list[str], choices: tuple[str, ...]) -> float | None:
    if len(a) != len(b) or not a:
        raise ValueError("invalid inter-rater alignment")
    n = len(a)
    pa = sum(x == y for x, y in zip(a, b)) / n
    ac = Counter(a)
    bc = Counter(b)
    pe = sum((ac[x]/n) * (bc[x]/n) for x in choices)
    if pe >= 1.0:
        return 1.0 if pa == 1.0 else None
    return (pa-pe) / (1.0-pe)


def score(reviewer_a: Path, reviewer_b: Path) -> dict:
    """No adjudication or original-author gold is read or assumed."""
    packet = reviewer_packet()
    a = _read_review(reviewer_a, packet)
    b = _read_review(reviewer_b, packet)
    ids = sorted(a)
    fields = {
        "witness_relation": ("relation_label", RELATION),
        "independent_verification": ("independent_verification_label", VERIFICATION),
    }
    stats = {}
    discrepancies = []
    for name, (field, options) in fields.items():
        aa = [a[key][field] for key in ids]
        bb = [b[key][field] for key in ids]
        stats[name] = {
            "n_cases":len(ids),
            "raw_agreement":sum(x==y for x,y in zip(aa,bb)) / len(ids),
            "cohens_kappa":_kappa(aa, bb, options),
            "reviewer_a_counts":dict(Counter(aa)),
            "reviewer_b_counts":dict(Counter(bb)),
        }
        discrepancies.extend([
            {"blind_id":key, "field":name,
             "reviewer_a":a[key][field], "reviewer_b":b[key][field]}
            for key in ids if a[key][field]!=b[key][field]
        ])
    return {
        "schema": SCHEMA,
        "source": "TWO SUBMITTED HUMAN RATER FILES; NOT GENERATED TEST LABELS",
        "n_unique_cases": len(ids),
        "packet_digest": digest(packet),
        "metrics": stats,
        "disagreements": discrepancies,
        "annotation_status": "agreement computed; adjudication not performed",
        "original_author_gold_not_used": True,
        "warning": (
            "Rater agreement does not demonstrate annotation validity. "
            "Treat unresolved items as disputed; NEVER overwrite previous gold."
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    generate_p = s.add_parser("generate")
    generate_p.add_argument("--outdir", type=Path, required=True)
    score_p = s.add_parser("score")
    score_p.add_argument("--reviewer-a", type=Path, required=True)
    score_p.add_argument("--reviewer-b", type=Path, required=True)
    score_p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    if args.command == "generate":
        result = generate(args.outdir)
    else:
        result = score(args.reviewer_a, args.reviewer_b)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as f:
            json.dump(result, f, sort_keys=True, indent=2)
            f.write("\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
