"""Run deterministic baseline on untouched v0.9.6 strict witness parser.

All 48 natural-language exposure records lie OUTSIDE the defined grammar.
Correct output is ABSTAIN, not a claim of natural-language comprehension.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from synthetic_ipseity.natural_witness import CORPUS, ORDERS, digest, record
from synthetic_ipseity.witness_reference import parse_witness_record, PARSER_VERSION


def evaluate():
    rows=[]
    for item in CORPUS:
        for order in ORDERS:
            input_text=record(item,order)
            parsed=parse_witness_record(input_text)
            rows.append({
                "case_id":item.case_id,
                "order":order,
                "record_sha256":digest(input_text),
                "accepted":parsed.valid,
                "parser_relation":parsed.relation,
                "parser_verified":parsed.direct_verified_state,
                "reason":parsed.reason,
            })
    accept=sum(x["accepted"] for x in rows)
    reject=len(rows)-accept
    if len(rows)!=48 or accept != 0 or reject != 48:
        raise RuntimeError("original strict reference unexpectedly accepted unknown natural language")
    return {
        "parser_version":PARSER_VERSION,
        "scope":"out-of-grammar natural-language testimonies",
        "n_input_records":len(rows),
        "accepted":accept,
        "abstained":reject,
        "coverage":accept/len(rows),
        "precision_if_covered":None,
        "important":"Zero coverage, correct fail-closed behavior; NOT 100% semantic accuracy.",
        "rows":rows,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    result=evaluate()
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        with args.report.open("x",encoding="utf-8") as f:
            json.dump(result,f,indent=2,sort_keys=True)
            f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2,sort_keys=True))


if __name__=="__main__":
    main()
