"""Real Qwen2.5-1.5B Q4_K_M CPU content-responsiveness capacity experiment.

This script is explicit and unbilled local inference using official public
GGUF weights. It records every raw output, before computing any statistic.
A failure stops the job without manufacturing missing measurements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from synthetic_ipseity.qwen_capacity import (
    MODEL_REPO, MODEL_FILENAME, PROTOCOL, ARMS, CASES,
    make_record, parse_answer, report, sealed_probes, sha256,
)


def canonical(obj: object) -> str:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )


def load_model():
    from huggingface_hub import hf_hub_download, model_info
    from llama_cpp import Llama

    revision = model_info(MODEL_REPO).sha
    print(f"Model repository {MODEL_REPO}@{revision}", file=sys.stderr, flush=True)
    path = hf_hub_download(
        repo_id=MODEL_REPO, filename=MODEL_FILENAME, revision=revision,
    )
    # A readable SHA-256 of actual GGUF bytes, not merely a repository name.
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(4 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    sha = digest.hexdigest()
    model = Llama(
        model_path=path, n_ctx=2048, n_threads=2, n_batch=256,
        n_gpu_layers=0, verbose=False, seed=20261010,
    )
    return model, revision, sha


def run(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    trials = sealed_probes()
    manifest = {
        "protocol": PROTOCOL,
        "model_repo": MODEL_REPO,
        "model_filename": MODEL_FILENAME,
        "cases": [c.case_id for c in CASES],
        "arms": ARMS,
        "n_questions": len(trials),
        "question_contract": "one unambiguous YES / NO / UNKNOWN question, no positional labels",
        "model_settings": {"temperature": 0.0, "max_tokens": 8,
                           "context_tokens": 2048, "cpu_threads": 2},
        "trials": trials,
        "negative_warning": "Four case stems only. This tests content responsiveness, not character persistence.",
    }
    manifest["sha256"] = sha256(manifest)
    with (outdir / "capacity-manifest.json").open("x", encoding="utf-8") as f:
        f.write(canonical(manifest) + "\n")

    model, revision, model_digest = load_model()
    rows: list[dict] = []
    with (outdir / "capacity-raw.jsonl").open("x", encoding="utf-8") as stream:
        for index, item in enumerate(trials, start=1):
            start = time.perf_counter()
            generation = model.create_chat_completion(
                messages=[{"role": "user", "content": item["input"]}],
                temperature=0.0, max_tokens=8,
                top_p=1.0, stream=False,
            )
            content = generation["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("model response was not text")
            parsed = parse_answer(content)
            record = {
                "trial_id": item["trial_id"],
                "case_id": item["case_id"],
                "arm": item["arm"],
                "condition": item["condition"],
                "question": item["question"],
                "expected": item["expected"],
                "record_sha256": item["record_sha256"],
                "prompt_sha256": sha256(item["input"]),
                "input_words": item["input_words"],
                "raw_response": content,
                **parsed,
                "model_repo": MODEL_REPO,
                "model_commit": revision,
                "gguf_sha256": model_digest,
                "manifest_sha256": manifest["sha256"],
                "response_usage": generation.get("usage"),
                "elapsed_ms": round((time.perf_counter() - start)*1000, 1),
            }
            rows.append(record)
            stream.write(canonical(record) + "\n")
            stream.flush()
            if index % 8 == 0:
                print(f"{index}/{len(trials)} real Qwen generation calls completed",
                      file=sys.stderr, flush=True)

    scored = report(rows)
    scored.update({
        "manifest_sha256": manifest["sha256"],
        "gguf_sha256": model_digest,
        "model_revision": revision,
        "run_kind": "real_qwen15b_gguf_cpu",
        "not_a_behavioral_effect": True,
        "response_count": len(rows),
    })
    with (outdir / "capacity-report.json").open("x", encoding="utf-8") as file:
        file.write(canonical(scored) + "\n")
    # Keep console output compact; raw records are stored in the artifact.
    synopsis = {
        "model_revision": revision,
        "gguf_sha256": model_digest,
        "gate": scored["response_gate_passed"],
        "n": len(rows),
        "groups": {k:{p:v for p,v in x.items() if p!="case_details"}
                  for k,x in scored["groups"].items()},
    }
    print("REAL QWEN CAPACITY SUMMARY " + canonical(synopsis), flush=True)
    return scored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    run(args.outdir)


if __name__ == "__main__":
    main()
