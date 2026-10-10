"""Run simple independent scenarios. No model inference or experimental claims."""
from synthetic_ipseity import (
    Ipseity, Kind, MemoryClass, SourceSignal, render_frame,
)

def main() -> None:
    organ = Ipseity(capacity=3)
    inputs = [
        SourceSignal("sample-subject", Kind.COLD, 0.88,
                     source_ref="hidden_body_reading"),
        SourceSignal("sample-subject", Kind.INSTRUMENT, "61 degrees",
                     source_ref="seen_instrument"),
        SourceSignal("sample-subject", Kind.RECOLLECTION, "a glass beaker on the shelf",
                     source_ref="reconstruction_42",
                     memory_class=MemoryClass.RECONSTRUCTED),
        SourceSignal("sample-subject", Kind.REMINDER, "check the shelf",
                     source_ref="hidden_scheduler", acquired=False),
    ]
    result = organ.process("sample-subject", inputs)
    print("SUBJECT FRAME (safe reference serializer)")
    print(render_frame(result.frame))
    print("\nENGINEER AUDIT (never send this to a renderer)")
    for record in result.audit.records:
        print(f"{record.kind.value}: {record.decision}; raw={record.raw_value!r}; "
              f"source={record.source_ref!r}")


if __name__ == "__main__":
    main()
