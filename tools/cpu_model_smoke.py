"""Actual, CPU-only, micro-scale renderer handoff test. NOT a validation study.

Runs two paired case stems (one conflict, one agreement), C vs D, same vs
different model. Eight trials, sixteen real generate calls. Never fake missing
outputs, overwrite results, or convert this tiny convenience sample into a
statistically powered claim. No paid API calls; public HF model weights only.

Used by .github/workflows/cpu-model-smoke.yml. It is intentionally separate
from the locked, much larger v0.9 pilot manifest and inferential evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

from synthetic_ipseity.behavioral_pilot import (
    SEED, canonical, phase_two, score, sha256, trial_manifest,
)

CASES = ("C01", "C02")
ARMS = ("C", "D")
MODELS = (
    "HuggingFaceTB/SmolLM2-135M-Instruct",
    "HuggingFaceTB/SmolLM2-360M-Instruct",
)
SMOKE_VERSION = "ipseity-cpu-smoke/1"


def choose_trials(full: dict) -> list[dict]:
    trials = [
        x for x in full["trials"]
        if x["block"] == "matched"
        and x["case_id"] in CASES
        and x["arm"] in ARMS
    ]
    expected = {
        f"matched:{case}:{arm}:0:{int(swap)}"
        for case in CASES for arm in ARMS for swap in (False, True)
    }
    if {row["trial_id"] for row in trials} != expected:
        raise ValueError("incomplete paired CPU smoke selection")
    # Retain sealed main manifest order, not cherry-picked successes.
    return trials


class CPUModel:
    def __init__(self, model_id: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from huggingface_hub import model_info

        self.model_id = model_id
        print(f"Loading public model: {model_id}", file=sys.stderr, flush=True)
        self.resolved_sha = model_info(model_id).sha
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, revision=self.resolved_sha, trust_remote_code=False,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, revision=self.resolved_sha,
            trust_remote_code=False, use_safetensors=True,
            torch_dtype=torch.float32,
        ).to("cpu").eval()
        self.eos = self.tokenizer.eos_token_id

    def generate(self, text: str, *, case_seed: int) -> tuple[str, dict]:
        import torch
        torch.manual_seed(case_seed)
        messages = [{"role": "user", "content": text}]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        input_tokens = int(inputs["input_ids"].shape[-1])
        before = time.perf_counter()
        with torch.inference_mode():
            emitted = self.model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=self.eos,
                use_cache=True,
            )
        generated = emitted[0, input_tokens:]
        result = self.tokenizer.decode(
            generated, skip_special_tokens=True,
        ).strip()
        meta = {
            "model": self.model_id,
            "model_revision": self.resolved_sha,
            "prompt_tokens": input_tokens,
            "generated_tokens": int(generated.shape[0]),
            "elapsed_ms": round((time.perf_counter() - before) * 1000, 1),
            "max_new_tokens": 128,
            "seed": case_seed,
            "temperature": 0.0,
        }
        return result, meta


def run(*, output_dir: Path) -> dict:
    import torch

    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Fail rather than erase earlier measurements.
    main_manifest = trial_manifest(seed=SEED, replicates=1)
    trials = choose_trials(main_manifest)
    sealed = {
        "protocol": SMOKE_VERSION,
        "parent_protocol": main_manifest["protocol"],
        "parent_manifest_sha256": main_manifest["manifest_sha256"],
        "trials": trials,
        "model_names": MODELS,
        "inference": {"temperature": 0.0, "max_new_tokens": 128,
                      "seed_rule": "parent_seed + case_number * 100"},
        "subset_warning": "TWO CASES ONLY, not the whole preregistered pilot",
    }
    sealed["sha256"] = sha256(sealed)
    manifest_path = output_dir / "micro-manifest.json"
    result_path = output_dir / "cpu-model-responses.jsonl"
    report_path = output_dir / "cpu-smoke-report.json"
    with manifest_path.open("x", encoding="utf-8") as f:
        f.write(canonical(sealed) + "\n")
    # Flush every row so a failed job can preserve partial real-model evidence.
    loaded = {}
    for model_id in MODELS:
        loaded[model_id] = CPUModel(model_id)

    results = []
    with result_path.open("x", encoding="utf-8") as stream:
        for index, trial in enumerate(trials, start=1):
            case_seed = SEED + int(trial["case_id"][1:]) * 100
            first, meta_1 = loaded[MODELS[0]].generate(
                trial["prompt"], case_seed=case_seed,
            )
            second_id = MODELS[1] if trial["swap"] else MODELS[0]
            second, meta_2 = loaded[second_id].generate(
                phase_two(first), case_seed=case_seed,
            )
            grade = score(trial, second)
            row = {
                "trial_id": trial["trial_id"],
                "parent_manifest_sha256": main_manifest["manifest_sha256"],
                "micro_manifest_sha256": sealed["sha256"],
                "case_id": trial["case_id"],
                "arm": trial["arm"],
                "swap": trial["swap"],
                "stage_1_model": MODELS[0],
                "stage_2_model": second_id,
                "stage_1": meta_1, "stage_2": meta_2,
                "handoff_raw": first, "response_raw": second,
                "score": grade,
                "run_kind": "real_cpu_transformers",
            }
            results.append(row)
            stream.write(canonical(row) + "\n")
            stream.flush()
            print(
                f"{index}/{len(trials)} {trial['trial_id']}: "
                f"valid={grade['valid']} score={grade['score']:.3f} "
                f"model={second_id} time_ms={meta_1['elapsed_ms'] + meta_2['elapsed_ms']:.0f}",
                file=sys.stderr, flush=True,
            )

    paired = {}
    for swap in (False, True):
        differences = []
        for case in CASES:
            values = {}
            for row in results:
                if row["case_id"] == case and row["swap"] == swap:
                    values[row["arm"]] = row["score"]["score"]
            if set(values) != set(ARMS):
                raise RuntimeError("missing matched arm, cannot score smoke")
            differences.append({
                "case_id": case,
                "C": values["C"],
                "D": values["D"],
                "D_minus_C": values["D"] - values["C"],
            })
        paired["swap" if swap else "same_model"] = {
            "paired_cases": differences,
            "mean_D_minus_C": sum(r["D_minus_C"] for r in differences)
            / len(differences),
        }

    report = {
        "protocol": SMOKE_VERSION,
        "parent_manifest_sha256": main_manifest["manifest_sha256"],
        "micro_manifest_sha256": sealed["sha256"],
        "run_kind": "real_cpu_transformers",
        "interpretation": (
            "REAL INFERENCE SMOKE ONLY. Two case stems cannot establish "
            "statistical significance or cognitive organ advantage."
        ),
        "n_trials": len(results),
        "generation_calls": len(results) * 2,
        "models": {m: loaded[m].resolved_sha for m in MODELS},
        "invalid_json_trials": sum(not r["score"]["valid"] for r in results),
        "pairwise": paired,
        "score_mean": {
            f"{arm}:{'swap' if swap else 'same'}": (
                sum(r["score"]["score"] for r in results
                    if r["arm"] == arm and r["swap"] == swap)
                / len(CASES)
            ) for arm in ARMS for swap in (False, True)
        },
        "not_scientific_validation": True,
    }
    with report_path.open("x", encoding="utf-8") as f:
        f.write(canonical(report) + "\n")
    print("ACTUAL CPU INFERENCE SMOKE SUMMARY " + canonical(report), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    run(output_dir=args.outdir)


if __name__ == "__main__":
    main()
