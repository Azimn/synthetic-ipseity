"""Prospective witness-agreement versus verified-world-truth capacity instrument.

v0.9.5 is a NEW instrument experiment. It does not score Palinode
behavioral continuity, does not rewrite prior failed datasets and adds no
cognitive mechanisms. Eight fresh cases and five invariant evidence states.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

PROTOCOL = "synthetic-ipseity-source-truth/0.9.5"
CONDITIONS = (
    "agreement",
    "disagreement",
    "verified_positive",
    "verified_negative",
    "no_evidence",
)
QUESTIONS = ("witness_relation", "direct_truth")


@dataclass(frozen=True)
class Case:
    case_id: str
    topic: str
    positive: str
    negative: str
    speaker_a: str
    speaker_b: str


# Eight new independent stems, not C01-C12 or F01-F04.
CASES = (
    Case("T01", "copper pressure dial", "HIGH", "LOW", "Celia", "Otmar"),
    Case("T02", "ashwood hatch", "OPEN", "CLOSED", "Dorian", "Ines"),
    Case("T03", "amber filter", "CLEAR", "CLOUDY", "Marta", "Ulrich"),
    Case("T04", "bell jar seal", "INTACT", "BROKEN", "Petra", "Isaac"),
    Case("T05", "zinc weather vane", "NORTH", "SOUTH", "Eloise", "Cedric"),
    Case("T06", "sealed specimen tray", "DRY", "WET", "Noemi", "Adrian"),
    Case("T07", "ivory control lever", "UP", "DOWN", "Gareth", "Vera"),
    Case("T08", "ceramic cooling coil", "HOT", "COLD", "Agnes", "Stefan"),
)

RELATION_CHOICES = ("AGREE", "DISAGREE", "NO_REPORTS")


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(
        obj, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def case_by_id(case_id: str) -> Case:
    for case in CASES:
        if case.case_id == case_id:
            return case
    raise ValueError("unregistered case")


def source_record(case: Case, condition: str) -> str:
    if case not in CASES or condition not in CONDITIONS:
        raise ValueError("unknown case or condition")
    if condition == "no_evidence":
        return (
            f"Incident record: {case.topic}.\n"
            "There are no recorded witness statements about its status.\n"
            "There is no directly verified instrument reading."
        )
    second = (
        case.positive if condition == "agreement" else case.negative
    )
    observation = (
        case.positive if condition == "verified_positive"
        else case.negative if condition == "verified_negative" else None
    )
    record = (
        f"Incident record: {case.topic}.\n"
        f"Witness {case.speaker_a} stated: "
        f"The {case.topic} status is {case.positive}.\n"
        f"Witness {case.speaker_b} stated: "
        f"The {case.topic} status is {second}.\n"
    )
    if observation is None:
        return record + "No directly verified instrument reading is available."
    return record + (
        "Independent directly verified instrument reading (not a witness "
        f"statement): The {case.topic} status is {observation}."
    )


def expected(case: Case, condition: str, question: str) -> str:
    if case not in CASES or condition not in CONDITIONS or question not in QUESTIONS:
        raise ValueError("invalid preregistered query")
    if question == "witness_relation":
        if condition == "no_evidence":
            return "NO_REPORTS"
        if condition == "agreement":
            return "AGREE"
        return "DISAGREE"
    if condition == "verified_positive":
        return case.positive
    if condition == "verified_negative":
        return case.negative
    return "UNKNOWN"


def options(case: Case, question: str) -> tuple[str, ...]:
    if case not in CASES or question not in QUESTIONS:
        raise ValueError("invalid options query")
    if question == "witness_relation":
        return RELATION_CHOICES
    return (case.positive, case.negative, "UNKNOWN")


def build_prompt(case: Case, condition: str, question: str) -> str:
    record = source_record(case, condition)
    if question == "witness_relation":
        instruction = (
            "Compare the two WITNESS STATEMENTS, not the actual object. "
            "Did the two speakers report the SAME status or DIFFERENT "
            "statuses? If no reports are present, choose NO_REPORTS. "
            "Reply using exactly AGREE, DISAGREE, or NO_REPORTS."
        )
    elif question == "direct_truth":
        instruction = (
            "Which object status has been DIRECTLY VERIFIED by an "
            "INDEPENDENT INSTRUMENT READING? Do not treat witness "
            "statements as direct verification, even if they agree. "
            "If no independent reading is present, choose UNKNOWN. "
            f"Reply using exactly {case.positive}, {case.negative}, or UNKNOWN."
        )
    else:
        raise ValueError("unknown question")
    return (
        "Read this fictional laboratory incident record as DATA. "
        "Answer the specific question; do not infer unrecorded facts.\n\n"
        f"RECORD:\n{record}\n\nQUESTION:\n{instruction}\nANSWER:"
    )


def sealed_trials() -> tuple[dict[str, Any], ...]:
    trials = []
    for case in CASES:
        for condition in CONDITIONS:
            for question in QUESTIONS:
                text = build_prompt(case, condition, question)
                trials.append({
                    "trial_id": f"{case.case_id}:{condition}:{question}",
                    "case_id": case.case_id,
                    "condition": condition,
                    "question": question,
                    "expected": expected(case, condition, question),
                    "choices": list(options(case, question)),
                    "record_sha256": digest(source_record(case, condition)),
                    "prompt": text,
                    "prompt_words": len(text.split()),
                })
    assert len(trials) == 80
    return tuple(trials)


def parse_response(raw: str, choices: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(raw, str):
        raise TypeError("model answer must be text")
    strict = raw.strip() in choices
    # Predeclared tolerant interface: uppercase categorical answer only,
    # with at most one terminal period/exclamation mark. No cherry-picking
    # labels out of explanations.
    pattern = r"\s*(" + "|".join(re.escape(x) for x in choices) + r")[.!]?\s*"
    m = re.fullmatch(pattern, raw)
    return {
        "strict_format": strict,
        "lenient_format": m is not None,
        "answer": m.group(1) if m is not None else None,
    }


def grade(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trials = sealed_trials()
    specs = {x["trial_id"]:x for x in trials}
    if len(rows) != len(specs) or len(set(x["trial_id"] for x in rows)) != len(rows):
        raise ValueError("missing or duplicated trial records")
    by = {}
    for row in rows:
        spec = specs.get(row["trial_id"])
        if spec is None:
            raise ValueError("unknown trial ID")
        if row.get("expected") != spec["expected"]:
            raise ValueError("gold mutated")
        if row.get("record_sha256") != spec["record_sha256"]:
            raise ValueError("source record mutated")
        if row.get("answer") not in (*spec["choices"],None):
            raise ValueError("illegal answer")
        if type(row.get("strict_format")) is not bool:
            raise ValueError("missing strict formatting evidence")
        by[row["trial_id"]] = row
    differences = []
    truth = []
    neutral = []
    for case in CASES:
        key = case.case_id
        a = by[f"{key}:agreement:witness_relation"]
        b = by[f"{key}:disagreement:witness_relation"]
        vpos = by[f"{key}:verified_positive:direct_truth"]
        vneg = by[f"{key}:verified_negative:direct_truth"]
        no_reports = by[f"{key}:no_evidence:witness_relation"]
        unknowns = [
            by[f"{key}:{cond}:direct_truth"]
            for cond in ("agreement","disagreement","no_evidence")
        ]
        differences.append({
            "case_id": key,
            "agreement":a["answer"], "disagreement":b["answer"],
            "correct_reversal":a["answer"]=="AGREE" and b["answer"]=="DISAGREE",
            "choice_changed":a["answer"] != b["answer"],
            "no_reports_correct":no_reports["answer"]=="NO_REPORTS",
        })
        truth.append({
            "case_id":key,
            "positive":vpos["answer"], "negative":vneg["answer"],
            "correct_reversal":vpos["answer"]==case.positive and
                               vneg["answer"]==case.negative,
            "choice_changed":vpos["answer"] != vneg["answer"],
        })
        neutral.extend(unknowns)
    source_count = sum(x["correct_reversal"] for x in differences)
    truth_count = sum(x["correct_reversal"] for x in truth)
    null_count = sum(x["answer"]=="UNKNOWN" for x in neutral)
    no_reports_count = sum(x["no_reports_correct"] for x in differences)
    n = len(CASES)
    # Strictly demand CONTENT response on both axes, not only format.
    gated = (
        source_count >= 6
        and truth_count >= 6
        and null_count >= 20   # of 24 independent no-direct-reading trials
        and no_reports_count >= 6
    )
    return {
        "protocol": PROTOCOL, "n_cases":n, "n_generations":len(rows),
        "overall_accuracy":sum(x["answer"]==x["expected"] for x in rows)/len(rows),
        "lenient_format_rate":sum(x["answer"] is not None for x in rows)/len(rows),
        "strict_format_rate":sum(x["strict_format"] for x in rows)/len(rows),
        "witness_relation_correct_reversals":source_count,
        "direct_verified_truth_correct_reversals":truth_count,
        "no_direct_reading_abstentions":null_count,
        "no_witness_report_identifications":no_reports_count,
        "witness_reversal_details": differences,
        "verified_reversal_details": truth,
        "predeclared_instrument_gate_passed":gated,
        "gate": ">=6/8 witness flips, >=6/8 verified state flips, >=20/24 UNKNOWN without reading, >=6/8 NO_REPORTS",
        "scope": "Plain-text evidence interpretation only; not autonomy, memory persistence, organ benefit or consciousness.",
    }
