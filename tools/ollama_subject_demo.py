"""Optional local, no-paid-API demonstration of a complete subject-frame loop.

Precondition: Ollama running at http://127.0.0.1:11434 and the chosen model
already downloaded. Nothing is transmitted to a remote inference service.
The temporary SQLite database is removed at the end of this demonstration.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

from synthetic_ipseity import (
    Channel, DurableIpseityHost, Kind, MemoryClass,
    Observation, SourceSignal, SubjectOnlyRendererPort,
)
from synthetic_ipseity.local_ollama import LocalOllamaRenderer


def example_observations() -> tuple[Observation,...]:
    examples=(
        (Kind.TOOL_TEXT, Channel.TOOL, "ENGINEER_SECRET_NEVER_SHOW", False, False,
         MemoryClass.UNCERTAIN),
        (Kind.INSTRUMENT, Channel.INSTRUMENT, "8 degrees", True, True,
         MemoryClass.UNCERTAIN),
        (Kind.HEARD_TEXT, Channel.COMMUNICATION,
         "Henry says the cabinet is locked.", True, True, MemoryClass.UNCERTAIN),
        (Kind.RECOLLECTION, Channel.MEMORY,
         "spending childhood in this laboratory", True, True, MemoryClass.RECONSTRUCTED),
    )
    return tuple(Observation(
        i, 1, "example-epoch", channel,
        SourceSignal(
            "example-subject", kind, value, source_ref=f"private-engineer-row-{i}",
            acquired=acquired, memory_class=memory_class,
        ),
        attested=attested,
    ) for i,(kind,channel,value,acquired,attested,memory_class)
    in enumerate(examples,1))


def demo(model: str) -> str:
    with tempfile.TemporaryDirectory(prefix="ipseity-demo-") as directory:
        path=Path(directory)/"life.sqlite"
        with DurableIpseityHost(
            path,subject_id="example-subject",epoch_id="example-epoch",
        ) as host:
            host.process(1, example_observations())
            if host.pending_count()!=1:
                raise RuntimeError("expected a first-person frame, not raw data")
        # Deliberate restart of the host object before real model inference.
        with DurableIpseityHost(
            path,subject_id="example-subject",epoch_id="example-epoch",
        ) as host:
            renderer=LocalOllamaRenderer(model)
            result=SubjectOnlyRendererPort(host,renderer).deliver_next(
                now_ms=1000,
            )
            if result is None or host.pending_count()!=0:
                raise RuntimeError("no confirmed admitted experience was delivered")
            return result.response


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",default="qwen3:1.5b",
                   help="already-installed Ollama model; default qwen3:1.5b")
    args=p.parse_args()
    print(demo(args.model))


if __name__=="__main__":
    main()
