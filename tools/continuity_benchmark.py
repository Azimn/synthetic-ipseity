"""Local, API-free behavioral pilot CLI. No cloud service or subscription.

prepare: write a sealed randomized A/B/C/D manifest
simulate: generate explicitly synthetic scores to test the measurement pipeline
run: execute with local Ollama at 127.0.0.1:11434 (not in CI)
evaluate: validate complete answers, compute matched and boundary reports
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from urllib import request

from synthetic_ipseity.behavioral_pilot import (
    PROTOCOL, SEED, canonical, evaluate, score, sha256, trial_manifest,
)


def read_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    sig = data.get("manifest_sha256")
    payload = {k: v for k, v in data.items() if k != "manifest_sha256"}
    if not isinstance(sig, str) or sha256(payload) != sig:
        raise ValueError("manifest integrity mismatch")
    if data.get("protocol") != PROTOCOL:
        raise ValueError("unsupported pilot protocol")
    return data


def save_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # x mode forbids silently clobbering a preregistered manifest/results.
    with path.open("x", encoding="utf-8") as f:
        f.write(content)


def rows_to_jsonl(rows) -> str:
    return "".join(canonical(row) + "\n" for row in rows)


def simulated_rows(manifest: dict, *, strategy: str) -> list[dict]:
    if strategy not in ("oracle", "bad", "leaky"):
        raise ValueError("invalid simulation")
    rows = []
    for t in manifest["trials"]:
        expected = t["expected"]
        if t["block"] == "boundary":
            value = (
                t["sentinel"] if strategy == "leaky" and t["arm"] == "A"
                else "UNKNOWN"
            )
            response = canonical({"diagnostic_tag": value})
        elif strategy == "bad":
            response = "NOT_JSON"
        else:
            response = canonical(expected)
        rows.append({
            "trial_id": t["trial_id"],
            "manifest_sha256": manifest["manifest_sha256"],
            "response": response,
            "handoff": "SIMULATED_ONLY_NOT_MODEL_INFERENCE",
            "run_kind": "fixture_simulation_not_empirical",
            "model_1": "none",
            "model_2": "none",
        })
    return rows


def query_ollama(prompt: str, model: str, *, seed: int,
                 temperature: float, timeout: int) -> tuple[str, dict]:
    if not model or not model.strip():
        raise ValueError("local Ollama model name required")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "seed": seed,
            "temperature": temperature,
            "num_predict": 220,
        },
    }
    http = request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=canonical(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    began = time.perf_counter()
    with request.urlopen(http, timeout=timeout) as response:
        result = json.load(response)
    elapsed = (time.perf_counter() - began) * 1000
    if not isinstance(result, dict) or not isinstance(result.get("response"), str):
        raise ValueError("unexpected Ollama response structure")
    meta = {
        "elapsed_ms": round(elapsed, 1),
        "prompt_eval_count": result.get("prompt_eval_count"),
        "eval_count": result.get("eval_count"),
        "done_reason": result.get("done_reason"),
    }
    return result["response"], meta


def model_rows(manifest: dict, *, model_a: str, model_b: str,
               temperature: float, timeout: int, limit: int | None) -> list[dict]:
    if isinstance(temperature, bool) or not 0 <= temperature <= 2:
        raise ValueError("temperature must be 0..2")
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    rows = []
    trials = manifest["trials"] if limit is None else manifest["trials"][:limit]
    for i, t in enumerate(trials, start=1):
        # Use paired generation seeds across conditions of the same case.
        seed = manifest["seed"] + (
            int(t["case_id"][1:]) * 100 + t["replicate"]
        )
        if t["block"] == "matched":
            handoff, meta1 = query_ollama(
                t["prompt"], model_a, seed=seed,
                temperature=temperature, timeout=timeout,
            )
            next_model = model_b if t["swap"] else model_a
            from synthetic_ipseity.behavioral_pilot import phase_two
            answer, meta2 = query_ollama(
                phase_two(handoff), next_model,
                seed=seed, temperature=temperature, timeout=timeout,
            )
        else:
            handoff = ""
            meta1 = None
            next_model = model_a
            answer, meta2 = query_ollama(
                t["prompt"], next_model, seed=seed,
                temperature=temperature, timeout=timeout,
            )
        rows.append({
            "trial_id": t["trial_id"],
            "manifest_sha256": manifest["manifest_sha256"],
            "handoff": handoff,
            "response": answer,
            "run_kind": "local_ollama",
            "model_1": model_a,
            "model_2": next_model,
            "temperature": temperature,
            "seed": seed,
            "stage_1": meta1,
            "stage_2": meta2,
        })
        print(f"{i}/{len(trials)} {t['trial_id']}", file=sys.stderr)
    return rows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--seed", type=int, default=SEED)
    prep.add_argument("--replicates", type=int, default=1)
    prep.add_argument("--no-boundary", action="store_true")

    sim = commands.add_parser("simulate")
    sim.add_argument("--manifest", type=Path, required=True)
    sim.add_argument("--out", type=Path, required=True)
    sim.add_argument("--strategy", choices=["oracle", "bad", "leaky"],
                     default="oracle")

    live = commands.add_parser("run")
    live.add_argument("--manifest", type=Path, required=True)
    live.add_argument("--out", type=Path, required=True)
    live.add_argument("--model-a", required=True)
    live.add_argument("--model-b", required=True)
    live.add_argument("--temperature", type=float, default=0.0)
    live.add_argument("--timeout", type=int, default=120)
    live.add_argument("--limit", type=int, default=None)

    ev = commands.add_parser("evaluate")
    ev.add_argument("--manifest", type=Path, required=True)
    ev.add_argument("--responses", type=Path, required=True)
    ev.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.command == "prepare":
        manifest = trial_manifest(
            seed=args.seed, replicates=args.replicates,
            include_boundary=not args.no_boundary,
        )
        save_new(args.out, canonical(manifest) + "\n")
        print(f"Manifest {manifest['manifest_sha256']}, {len(manifest['trials'])} trials")
    elif args.command == "simulate":
        manifest = read_manifest(args.manifest)
        rows = simulated_rows(manifest, strategy=args.strategy)
        save_new(args.out, rows_to_jsonl(rows))
        print(f"SIMULATION ONLY: {len(rows)} artificial response rows")
    elif args.command == "run":
        manifest = read_manifest(args.manifest)
        rows = model_rows(
            manifest, model_a=args.model_a, model_b=args.model_b,
            temperature=args.temperature, timeout=args.timeout, limit=args.limit,
        )
        save_new(args.out, rows_to_jsonl(rows))
        print(f"LOCAL MODEL CALLS ONLY: {len(rows)} collected response rows")
    else:
        manifest = read_manifest(args.manifest)
        rows = [
            json.loads(line)
            for line in args.responses.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        kinds = {row.get("run_kind") for row in rows}
        if len(kinds) != 1 or not kinds <= {
            "fixture_simulation_not_empirical", "local_ollama"
        }:
            raise ValueError("mixed, unsigned or unknown response provenance")
        report = evaluate(manifest, rows)
        report["run_kind"] = next(iter(kinds))
        report["empirical_model_run"] = next(iter(kinds)) == "local_ollama"
        report["interpretation"] = (
            "DIAGNOSTIC ONLY. Simulated fixture; never cite as behavioral evidence."
            if not report["empirical_model_run"] else
            "Model outputs from local Ollama. Report paired nulls and "
            "validate information parity before any causal claim."
        )
        result = canonical(report) + "\n"
        if args.out:
            save_new(args.out, result)
        print(result, end="")


if __name__ == "__main__":
    main()
