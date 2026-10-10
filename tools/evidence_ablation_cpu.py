"""Run v0.9.3 three-way evidence-ablation real CPU instrument test.

No paid APIs. Record 144 next-token decisions using the exact same labels
for original evidence, reversed evidence, and missing evidence. This is a
separate prospective study; v0.9 and v0.9.2 results remain intact.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from synthetic_ipseity.behavioral_pilot import canonical
from synthetic_ipseity.evidence_ablation import (
    SCHEMA,ablation_questions,score_ablation,
)
from synthetic_ipseity.format_probe import sha256
from tools.cpu_model_smoke import CPUModel,MODELS


def classify(model:CPUModel,prompt:str,labels:dict[str,str])->dict:
    import torch
    tok=model.tokenizer
    tokens=tok.apply_chat_template(
        [{"role":"user","content":prompt}],
        add_generation_prompt=True,tokenize=True,
        return_dict=True,return_tensors="pt",
    )
    ids={}
    for label in labels:
        one=tok.encode(label,add_special_tokens=False)
        if len(one)!=1:
            raise ValueError("non-single-token letter; no biased scoring permitted")
        ids[label]=one[0]
    start=time.perf_counter()
    with torch.inference_mode():
        logits=model.model(**tokens).logits[0,-1]
    values={k:float(logits[v]) for k,v in ids.items()}
    picked=sorted(values,key=lambda k:(-values[k],k))[0]
    return {
        "predicted":picked,
        "letter_logits":{k:round(v,6) for k,v in values.items()},
        "input_tokens":int(tokens["input_ids"].shape[-1]),
        "elapsed_ms":round((time.perf_counter()-start)*1000,1),
    }


def run(outdir:Path)->dict:
    import torch
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    outdir.mkdir(parents=True,exist_ok=True)
    questions=ablation_questions()
    manifest={
        "schema":SCHEMA,
        "n_questions":len(questions),
        "questions":list(questions),
        "model_ids":list(MODELS),
        "algorithm":"single-token next-token raw-logit choice; fixed letters within original/reversed/neutral",
        "primary_outcome":"correct_polarity_reversal_rate",
        "case_stems":["C01","C02"],
        "not_original_v0_9":True,
    }
    manifest["sha256"]=sha256(manifest)
    with (outdir/"ablation-manifest.json").open("x",encoding="utf-8") as f:
        f.write(canonical(manifest)+"\n")
    models={m:CPUModel(m) for m in MODELS}
    rows=[]
    with (outdir/"ablation-raw.jsonl").open("x",encoding="utf-8") as f:
        for idx,q in enumerate(questions,1):
            m_id=MODELS[1] if q["swap"] else MODELS[0]
            model=models[m_id]
            result=classify(model,q["prompt"],q["label_map"])
            row={**{key:q[key] for key in ("case_id","arm","swap","field",
                                         "origin","correct_original","label_map")},
                 **result,
                 "model_id":m_id,"model_sha":model.resolved_sha,
                 "question_sha256":sha256(q["prompt"]),
                 "manifest_sha256":manifest["sha256"],
                 "run_kind":"real_cpu_next_token_logits"}
            rows.append(row)
            f.write(canonical(row)+"\n")
            f.flush()
            if idx%12==0:
                print(f"{idx}/144 completed",file=sys.stderr,flush=True)
    report=score_ablation(rows)
    report.update({
        "manifest_sha256":manifest["sha256"],
        "model_commits":{m:models[m].resolved_sha for m in MODELS},
        "run_kind":"real_cpu_next_token_logits",
    })
    with (outdir/"ablation-report.json").open("x",encoding="utf-8") as f:
        f.write(canonical(report)+"\n")
    print("REAL EVIDENCE ABLATION SUMMARY "+canonical(report),flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir",type=Path,required=True)
    run(p.parse_args().outdir)


if __name__=="__main__":
    main()
