"""Prospective evidence-ablation test of v0.9.2 letter-position bias.

Three exposure conditions keep question, choice labels and models fixed:
- original record from the canonical organ or first-person control
- counterfactual identical topic and witnesses with opposite report polarity
- neutral no-evidence text

A content-sensitive classifier should sometimes change its selected option
under a real change in evidence. No prompt-format or continuity claims follow.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from synthetic_ipseity.behavioral_pilot import (
    CASES as OLD_CASES, matched_lines,
)
from synthetic_ipseity.format_probe import (
    ARMS, CASES, FIELDS, build_prompt, grade_logits, question,
)

SCHEMA="ipseity-evidence-ablation/0.9.3"
NEUTRAL=(
    "There is no testimony or observation about any laboratory object. "
    "No earlier belief, change of mind or reflective memory has been provided."
)
POLARITY_FIELDS=("stance","evidence","noticed_change",
                 "recalls_notice","next_action")


def source_records(case_id: str, arm: str) -> dict[str,str]:
    if case_id not in CASES or arm not in ARMS:
        raise ValueError("only original frozen C01/C02 and C/D permitted")
    s=next(x for x in OLD_CASES if x.case_id==case_id)
    counterfactual=replace(s,conflict=not s.conflict)
    original="\n".join(matched_lines(s,arm))
    opposite="\n".join(matched_lines(counterfactual,arm))
    if original==opposite:
        raise AssertionError("counterfactual did not alter evidence")
    return {"original":original,
            "reversed":opposite,
            "neutral":NEUTRAL}


def ablation_questions() -> tuple[dict[str,Any],...]:
    """144 preregistered contrastive input conditions; immutable ordering."""
    rows=[]
    for case in CASES:
        for arm in ARMS:
            records=source_records(case,arm)
            for swap in (False,True):
                for field in FIELDS:
                    q=question(case,field,swap=swap)
                    for origin in ("original","reversed","neutral"):
                        rows.append({
                            "case_id":case,"arm":arm,"swap":swap,
                            "field":field,"origin":origin,
                            "prompt":build_prompt(records[origin],q),
                            "correct_original":q.correct_label,
                            "label_map":q.label_map,
                        })
    assert len(rows)==144
    return tuple(rows)


def score_ablation(rows: list[dict[str,Any]]) -> dict[str,Any]:
    """Compare paired letter choices, never count items as independent cases."""
    expected={(case,arm,swap,field,origin) for case in CASES
              for arm in ARMS for swap in (False,True)
              for field in FIELDS for origin in ("original","reversed","neutral")}
    by_key={}
    for row in rows:
        key=(row["case_id"],row["arm"],row["swap"],row["field"],row["origin"])
        if key not in expected or key in by_key:
            raise ValueError("duplicate or unknown ablation row")
        if row["predicted"] not in row["label_map"]:
            raise ValueError("invalid choice label")
        by_key[key]=row
    if set(by_key)!=expected:raise ValueError("incomplete ablation")
    groups={}
    for arm in ARMS:
        for swap in (False,True):
            pair=[]
            for case in CASES:
                for field in FIELDS:
                    key=(case,arm,swap,field)
                    original=by_key[(*key,"original")]
                    reverse=by_key[(*key,"reversed")]
                    neutral=by_key[(*key,"neutral")]
                    s=next(x for x in OLD_CASES if x.case_id==case)
                    rev_s=replace(s,conflict=not s.conflict)
                    expected_original=s.expected[field]
                    expected_reverse=rev_s.expected[field]
                    if isinstance(expected_original,bool):
                        expected_original="yes" if expected_original else "no"
                        expected_reverse="yes" if expected_reverse else "no"
                    mapped=original["label_map"]
                    if any(r["label_map"]!=mapped for r in (reverse,neutral)):
                        raise ValueError("options changed across evidence conditions")
                    pair.append({
                        "case_id":case,"field":field,
                        "original_correct":mapped[original["predicted"]]==expected_original,
                        "reversed_correct":mapped[reverse["predicted"]]==expected_reverse,
                        "letter_changed":original["predicted"]!=reverse["predicted"],
                        "different_from_neutral":original["predicted"]!=neutral["predicted"],
                        "exact_correct_reversal":(
                            mapped[original["predicted"]]==expected_original
                            and mapped[reverse["predicted"]]==expected_reverse
                            and field in POLARITY_FIELDS
                        ),
                        "original":original["predicted"],
                        "reversed":reverse["predicted"],
                        "neutral":neutral["predicted"],
                    })
            shifting=[item for item in pair if item["field"] in POLARITY_FIELDS]
            groups[f"{arm}:{int(swap)}"]={
                "n_case_stems":len(CASES),
                "n_fields":len(pair),
                "original_accuracy":sum(x["original_correct"] for x in pair)/len(pair),
                "counterfactual_accuracy":sum(x["reversed_correct"] for x in pair)/len(pair),
                "polarity_flip_rate":sum(x["letter_changed"] for x in shifting)/len(shifting),
                "correct_polarity_reversal_rate":sum(
                    x["exact_correct_reversal"] for x in shifting
                )/len(shifting),
                "changed_vs_neutral_rate":sum(
                    x["different_from_neutral"] for x in pair
                )/len(pair),
                "details":pair,
            }
    return {
        "schema":SCHEMA,"n_real_classifications":len(rows),
        "groups":groups,"not_character_continuity_evidence":True,
        "interpretation":(
            "Evidence-ablation instrument check: choice flips and "
            "correct counterfactual reversals measure content responsiveness, "
            "not identity persistence or subjective awareness."
        ),
    }
