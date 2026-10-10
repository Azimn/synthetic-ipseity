"""One-question-at-a-time REAL CPU calibration of the v0.9 output floor.

This is a new, prospectively sealed protocol. It never edits or retroactively
scores the original v0.9 microstudy. It reports two independent measurements:
1. Semantic choice from model logits over a tiny one-token letter alphabet.
2. Greedy four-new-token generation's strict single-letter format compliance.

The first is constrained multiple-choice recognition, NOT free conversation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from synthetic_ipseity.behavioral_pilot import (
    SEED, canonical, matched_lines, sha256, trial_manifest, CASES as PARENT_CASES,
)
from synthetic_ipseity.format_probe import (
    ARMS, CASES, FIELDS, SCHEMA, build_prompt, grade_logits,
    parse_free_letter, question, select_trials, summarize,
)
from tools.cpu_model_smoke import CPUModel, MODELS


def probe_model(model: CPUModel, prompt: str, q, *, seed: int) -> dict:
    import torch
    tokenizer = model.tokenizer
    inputs = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True, tokenize=True,
        return_tensors="pt", return_dict=True,
    )
    token_choices = {}
    for label in q.label_map:
        ids = tokenizer.encode(label, add_special_tokens=False)
        if len(ids) != 1:
            raise ValueError(
                f"single-token candidate invariant failed: {model.model_id} "
                f"{label} -> {ids}"
            )
        token_choices[label] = ids[0]
    start = time.perf_counter()
    with torch.inference_mode():
        logits = model.model(**inputs).logits[0, -1]
    scores = {
        label: float(logits[token_id])
        for label, token_id in token_choices.items()
    }
    forced = grade_logits(scores, q)
    torch.manual_seed(seed)
    with torch.inference_mode():
        output = model.model.generate(
            **inputs, max_new_tokens=4, do_sample=False,
            pad_token_id=model.eos, use_cache=True,
        )
    raw = tokenizer.decode(
        output[0, inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True,
    )
    return {
        "forced": forced,
        "free": parse_free_letter(raw, q),
        "free_raw": raw,
        "input_tokens": int(inputs["input_ids"].shape[-1]),
        "elapsed_ms": round((time.perf_counter()-start)*1000, 1),
        "model_id": model.model_id,
        "model_revision": model.resolved_sha,
        "format_probe_kind": "next-token-logit-choice-plus-unconstrained-4-token-greedy",
    }


def run(outdir: Path):
    import torch
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    outdir.mkdir(parents=True, exist_ok=True)
    parent = trial_manifest(seed=SEED, replicates=1)
    selected = select_trials(parent)
    specs = []
    for trial in selected:
        for field in FIELDS:
            q = question(trial["case_id"], field, swap=trial["swap"])
            specs.append({
                "case_id": trial["case_id"],
                "arm": trial["arm"], "swap": trial["swap"],
                "field": field, "labels": dict(q.labels),
                "correct_label": q.correct_label,
                "trial_id": trial["trial_id"],
            })
    manifest = {
        "schema": SCHEMA,
        "parent_manifest_sha256": parent["manifest_sha256"],
        "models": list(MODELS),
        "trials": specs,
        "origins": ["handoff", "direct"],
        "scoring": "model's raw next-token logits for single-token labels, plus free generated letter validity",
        "no_posthoc_rescoring": True,
        "case_stems": list(CASES),
        "warning": "Two cases only, formatting calibration, not causal organ validation",
    }
    manifest["sha256"] = sha256(manifest)
    with (outdir/"calibration-manifest.json").open("x", encoding="utf-8") as f:
        f.write(canonical(manifest)+"\n")
    loaded = {m: CPUModel(m) for m in MODELS}
    rows = []
    with (outdir/"calibration-probes.jsonl").open("x", encoding="utf-8") as f:
        for i, trial in enumerate(selected):
            s = next(s for s in PARENT_CASES if s.case_id == trial["case_id"])
            base_seed = SEED + int(trial["case_id"][1:])*100
            # Original stage-one prompt and model, as in the real v0.9.1 run.
            handoff, handoff_meta = loaded[MODELS[0]].generate(
                trial["prompt"], case_seed=base_seed,
            )
            direct = "\n".join(matched_lines(s, trial["arm"]))
            consumer = MODELS[1] if trial["swap"] else MODELS[0]
            for origin, evidence in (("handoff", handoff), ("direct", direct)):
                for field in FIELDS:
                    q = question(trial["case_id"], field, swap=trial["swap"])
                    prompt = build_prompt(evidence, q)
                    outcome = probe_model(
                        loaded[consumer], prompt, q, seed=base_seed,
                    )
                    row = {
                        "trial_id": trial["trial_id"],
                        "case_id": trial["case_id"],
                        "arm": trial["arm"], "swap": trial["swap"],
                        "origin": origin, "field": field,
                        "question": prompt, "evidence_sha256": sha256(evidence),
                        "handoff_raw": handoff if origin == "handoff" else None,
                        "handoff_meta": handoff_meta if origin == "handoff" else None,
                        "manifest_sha256": manifest["sha256"],
                        **outcome,
                    }
                    rows.append(row)
                    f.write(canonical(row)+"\n")
                    f.flush()
                    print(
                        f"{len(rows)}/96 {trial['trial_id']} "
                        f"{origin}/{field} "
                        f"semantic={row['forced']['semantic_correct']} "
                        f"letter_valid={row['free']['format_valid']}",
                        file=sys.stderr, flush=True,
                    )
    report = summarize(rows)
    report.update({
        "run_kind": "real_cpu_transformers",
        "models": {m:loaded[m].resolved_sha for m in MODELS},
        "calibration_manifest_sha256": manifest["sha256"],
        "parent_manifest_sha256": parent["manifest_sha256"],
        "no_model_effect_claim": True,
        "n_model_calls_stage_one": len(selected),
        "n_logit_classifications": len(rows),
        "n_letter_generations": len(rows),
    })
    with (outdir/"calibration-report.json").open("x", encoding="utf-8") as f:
        f.write(canonical(report)+"\n")
    print("REAL FORMAT CALIBRATION SUMMARY "+canonical(report), flush=True)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir", type=Path, required=True)
    args = p.parse_args()
    run(args.outdir)


if __name__ == "__main__":
    main()
