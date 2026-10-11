"""v0.9.7 real local Qwen3B CPU natural-language source interpretation study.

Source prompts, pair/order and scoring froze before inference. A model must
be read-only on this corpus. No paid API, no new cognitive organ, no automatic
retry/cherry-picking or retroactive change to earlier instrument results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from synthetic_ipseity.natural_witness import (
    CORPUS, MODEL_FILE, MODEL_REPO, MODEL_REVISION, MODEL_SHA256,
    PROTOCOL, digest, grade, parse_answer, sealed_probes,
)
from tools.natural_witness_reference import evaluate as reference_evaluate

def canonical(x: object) -> str:
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)


def load_model():
    from huggingface_hub import hf_hub_download,model_info
    from llama_cpp import Llama

    metadata=model_info(MODEL_REPO,revision=MODEL_REVISION)
    if metadata.sha!=MODEL_REVISION:
        raise RuntimeError("model revision mismatch")
    path=hf_hub_download(repo_id=MODEL_REPO,filename=MODEL_FILE,revision=MODEL_REVISION)
    h=hashlib.sha256()
    with open(path,"rb") as reader:
        while True:
            chunk=reader.read(4*1024*1024)
            if not chunk:break
            h.update(chunk)
    if h.hexdigest()!=MODEL_SHA256:
        raise RuntimeError("actual model-file checksum differs from preregistered v0.9.5 Qwen3B")
    model=Llama(model_path=path,n_ctx=2048,n_threads=2,n_batch=256,
                n_gpu_layers=0,seed=20261011,verbose=False)
    return model,metadata.sha,h.hexdigest()


def run(outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    trials=sealed_probes()
    manifest={
        "protocol":PROTOCOL,
        "case_ids":[x.case_id for x in CORPUS],
        "model_repository":MODEL_REPO,"model_commit":MODEL_REVISION,
        "model_file":MODEL_FILE,"model_sha256":MODEL_SHA256,
        "temperature":0.0,"max_new_tokens":12,"cpu_threads":2,
        "n_ctx":2048,"trial_count":len(trials),
        "trials":trials,
        "warning":"24 case stems, not blinded human-annotated; not an organ behavior study",
    }
    manifest["sha256"]=digest(manifest)
    with (outdir/"natural-manifest.json").open("x",encoding="utf-8") as f:
        f.write(canonical(manifest)+"\n")

    # Deterministic baseline is separately evaluated and preserved.
    baseline=reference_evaluate()
    with (outdir/"natural-strict-reference.json").open("x",encoding="utf-8") as f:
        f.write(canonical(baseline)+"\n")

    model,revision,file_sha=load_model()
    rows=[]
    with (outdir/"natural-model-raw.jsonl").open("x",encoding="utf-8") as f:
        for idx,trial in enumerate(trials,1):
            start=time.perf_counter()
            answer=model.create_chat_completion(
                messages=[{"role":"user","content":trial["prompt"]}],
                temperature=0.0,max_tokens=12,stream=False,
            )
            raw=answer["choices"][0]["message"]["content"]
            if not isinstance(raw,str):
                raise RuntimeError("model did not return a text answer")
            parsed=parse_answer(raw,trial["question"])
            item={
                "trial_id":trial["trial_id"],
                "case_id":trial["case_id"],
                "order":trial["order"],
                "question":trial["question"],
                "expected":trial["expected"],
                "record_sha256":trial["record_sha256"],
                "prompt_sha256":digest(trial["prompt"]),
                "input_words":trial["prompt_words"],
                "raw_output":raw,
                **parsed,
                "model_revision":revision,
                "model_sha256":file_sha,
                "manifest_sha256":manifest["sha256"],
                "runtime_ms":round(1000*(time.perf_counter()-start),1),
                "usage":answer.get("usage"),
            }
            rows.append(item)
            f.write(canonical(item)+"\n")
            f.flush()
            if idx%8==0:
                print(f"{idx}/{len(trials)} real Qwen3B calls complete",file=sys.stderr,flush=True)
    report=grade(rows)
    report.update({
        "model_revision":revision,
        "model_sha256":file_sha,
        "manifest_sha256":manifest["sha256"],
        "baseline_coverage":baseline["coverage"],
        "run_kind":"real_cpu_qwen3b_natural_prose",
    })
    with (outdir/"natural-report.json").open("x",encoding="utf-8") as f:
        f.write(canonical(report)+"\n")
    print("NATURAL WITNESS REAL SUMMARY "+canonical({
        k:v for k,v in report.items() if k!="case_details"
    }),flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir",type=Path,required=True)
    run(p.parse_args().outdir)


if __name__=="__main__":
    main()
