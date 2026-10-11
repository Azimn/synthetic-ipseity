"""No-paid-API CPU capacity run for v0.9.5 source/truth separation.

Uses official Qwen2.5-3B-Instruct GGUF Q4_K_M; discovers the single exact
quantization file in the pinned model repo. Every output and checksum is
retained before grading. This is NOT a character efficacy experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from synthetic_ipseity.source_truth_capacity import (
    PROTOCOL, CASES, digest, grade, parse_response, sealed_trials,
)

MODEL_REPO="Qwen/Qwen2.5-3B-Instruct-GGUF"
INFERENCE={
    "n_ctx":2048,
    "n_threads":2,
    "n_gpu_layers":0,
    "temperature":0.0,
    "max_tokens":12,
}


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",",":"), allow_nan=False)


def model_resource():
    from huggingface_hub import HfApi, hf_hub_download
    from llama_cpp import Llama

    api=HfApi()
    metadata=api.model_info(MODEL_REPO)
    if not metadata.sha:
        raise ValueError("Hugging Face model revision could not be pinned")
    entries=api.list_repo_files(MODEL_REPO, revision=metadata.sha)
    matches=[name for name in entries if name.lower().endswith(".gguf")
             and "q4_k_m" in name.lower()
             and not ("-000" in name.lower() and "-of-" in name.lower())]
    if len(matches)!=1:
        raise ValueError(f"Expected exactly one Q4_K_M GGUF model, got {matches}")
    filename=matches[0]
    path=hf_hub_download(repo_id=MODEL_REPO,filename=filename,revision=metadata.sha)
    checksum=hashlib.sha256()
    with open(path,"rb") as f:
        while True:
            b=f.read(4*1024*1024)
            if not b:break
            checksum.update(b)
    print(f"MODEL {MODEL_REPO}@{metadata.sha} file={filename} sha256={checksum.hexdigest()}",
          file=sys.stderr,flush=True)
    model=Llama(model_path=path,verbose=False,seed=20261010,
                n_ctx=INFERENCE["n_ctx"],n_threads=INFERENCE["n_threads"],
                n_gpu_layers=0,n_batch=256)
    return model,metadata.sha,filename,checksum.hexdigest()


def run(outdir:Path):
    outdir.mkdir(parents=True,exist_ok=True)
    trials=sealed_trials()
    prereg={
        "protocol":PROTOCOL,
        "case_ids":[c.case_id for c in CASES],
        "model":MODEL_REPO,
        "quantization":"Q4_K_M",
        "settings":INFERENCE,
        "primary_endpoints":["witness_relation_correct_reversals",
                             "direct_verified_truth_correct_reversals"],
        "trials":trials,
        "not_organ_comparison":True,
    }
    prereg["sha256"]=digest(prereg)
    with (outdir/"source-truth-manifest.json").open("x",encoding="utf-8") as f:
        f.write(canonical(prereg)+"\n")

    model,revision,filename,model_sha=model_resource()
    rows=[]
    with (outdir/"source-truth-raw.jsonl").open("x",encoding="utf-8") as f:
        for n,spec in enumerate(trials,1):
            start=time.perf_counter()
            result=model.create_chat_completion(
                messages=[{"role":"user","content":spec["prompt"]}],
                temperature=INFERENCE["temperature"],
                max_tokens=INFERENCE["max_tokens"],stream=False,
            )
            content=result["choices"][0]["message"]["content"]
            if not isinstance(content,str):
                raise ValueError("model did not return a string")
            parsed=parse_response(content,tuple(spec["choices"]))
            row={
                "trial_id":spec["trial_id"],
                "case_id":spec["case_id"],
                "condition":spec["condition"],
                "question":spec["question"],
                "expected":spec["expected"],
                "choices":spec["choices"],
                "record_sha256":spec["record_sha256"],
                "prompt_sha256":digest(spec["prompt"]),
                "prompt_words":spec["prompt_words"],
                "raw_response":content,
                **parsed,
                "model":MODEL_REPO,
                "model_revision":revision,
                "model_filename":filename,
                "gguf_sha256":model_sha,
                "manifest_sha256":prereg["sha256"],
                "usage":result.get("usage",{}),
                "elapsed_ms":round(1000*(time.perf_counter()-start),1),
            }
            rows.append(row)
            f.write(canonical(row)+"\n")
            f.flush()
            if n%8==0:
                print(f"{n}/{len(trials)} real Qwen3B CPU calls",file=sys.stderr,flush=True)
    scored=grade(rows)
    scored.update({
        "run_kind":"real_cpu_gguf_qwen2_5_3b",
        "model_repository":MODEL_REPO,
        "model_revision":revision,
        "model_filename":filename,
        "gguf_sha256":model_sha,
        "manifest_sha256":prereg["sha256"],
    })
    with (outdir/"source-truth-report.json").open("x",encoding="utf-8") as f:
        f.write(canonical(scored)+"\n")
    print("REAL SOURCE TRUTH SUMMARY "+canonical({
        k:v for k,v in scored.items()
        if k not in ("witness_reversal_details","verified_reversal_details")
    }),flush=True)
    return scored


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir",type=Path,required=True)
    run(p.parse_args().outdir)


if __name__=="__main__":
    main()
