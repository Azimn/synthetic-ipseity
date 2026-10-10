"""A reference renderer ingress with one admitted, subject-only text channel.

The caller grants a trusted renderer callback access ONLY to the subject text
from the durable outbox. The adapter does not provide a universal sandbox or
prevent caller code from separately invoking other model clients.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .durable_host import DurableIpseityHost


@dataclass(frozen=True)
class RenderDelivery:
    """Engineer-visible delivery receipt. Not input to the subject."""

    outbox_id: int
    response: str


class SubjectOnlyRendererPort:
    """Drains durable first-person experiences to one text renderer.

    The renderer sees a single positional string, the admitted subject text.
    It receives no host object, audit, source channel metadata, hidden state,
    input event, checkpoint or outbox ID through this callback API.

    A renderer exception or invalid response does not acknowledge a lease.
    The leased frame can be delivered again after expiry, so downstream side
    effects need their own idempotency controls.
    """

    def __init__(
        self,
        host: DurableIpseityHost,
        renderer: Callable[[str], str],
    ) -> None:
        if not isinstance(host, DurableIpseityHost):
            raise TypeError("renderer port requires DurableIpseityHost")
        if not callable(renderer):
            raise TypeError("renderer must be callable")
        self._host = host
        self._renderer = renderer

    def deliver_next(
        self,
        *,
        now_ms: int,
        lease_ms: int = 30_000,
    ) -> RenderDelivery | None:
        lease = self._host.claim_next(now_ms=now_ms, lease_ms=lease_ms)
        if lease is None:
            return None
        # The ONLY value crossing into model inference is the canonical
        # subject text read from the committed, checksum-validated outbox.
        subject_text = self._host.read_subject_text(lease)
        response = self._renderer(subject_text)
        if not isinstance(response, str) or not response.strip():
            raise TypeError("renderer must return nonblank text")
        self._host.ack_delivery(lease)
        return RenderDelivery(outbox_id=lease.outbox_id, response=response)
