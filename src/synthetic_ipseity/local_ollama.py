"""Opt-in, localhost-only Ollama renderer for admitted first-person frames.

This adapter receives exactly one text value from SubjectOnlyRendererPort.
It has no host, database, observation, audit, tool or source-object access.
It is an engineering integration, not a prompt-injection security sandbox.
"""
from __future__ import annotations

import json
import re
from typing import Callable
from urllib import request

LOCAL_ENDPOINT="http://127.0.0.1:11434/api/generate"
_NAME=re.compile(r"[A-Za-z0-9_.:/-]{1,100}\Z")


def _local_post(body: bytes, timeout: float) -> bytes:
    """Disable proxy use and redirects so the endpoint stays loopback-only."""
    class NoRedirect(request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError("local inference must not follow redirects")
    opener=request.build_opener(request.ProxyHandler({}),NoRedirect())
    req=request.Request(
        LOCAL_ENDPOINT, data=body,
        headers={"Content-Type":"application/json"},
        method="POST",
    )
    with opener.open(req,timeout=timeout) as stream:
        if stream.geturl()!=LOCAL_ENDPOINT:
            raise ValueError("unexpected inference endpoint")
        payload=stream.read(2_000_001)
    if len(payload)>2_000_000:
        raise ValueError("model response exceeds bounded size")
    return payload


class LocalOllamaRenderer:
    """One-text-argument adapter, suitable only behind SubjectOnlyRendererPort.

    The ONLY subject-context value sent in the prompt field is the admitted
    text. No memory state, external system prompt, previous turns, tool JSON,
    world snapshots or developer diagnostics are included.

    A trusted custom transport may be provided for offline tests. Never hand
    host secrets to the transport. No HTTP requests occur on construction.
    """

    def __init__(
        self,
        model: str,
        *,
        timeout: float = 120.0,
        transport: Callable[[bytes, float], bytes] | None = None,
    ) -> None:
        if type(model) is not str or _NAME.fullmatch(model) is None:
            raise ValueError("model must be a bounded Ollama model tag")
        if type(timeout) not in (int,float) or not 0 < timeout <= 900:
            raise ValueError("timeout must be between 0 and 900 seconds")
        if transport is not None and not callable(transport):
            raise TypeError("transport must be a trusted callable")
        self.model=model
        self.timeout=float(timeout)
        self._transport=transport if transport is not None else _local_post

    def __call__(self, admitted_text: str) -> str:
        if type(admitted_text) is not str or not admitted_text.strip():
            raise TypeError("only nonblank admitted subject text can be rendered")
        if len(admitted_text)>32_000:
            raise ValueError("subject frame exceeds local renderer's size limit")
        # A deliberately minimal stateless, single-frame request. The HTTP
        # payload contains standard inference settings, not hidden world data.
        body=json.dumps({
            "model":self.model,
            "prompt":admitted_text,
            "stream":False,
            "options":{"temperature":0},
        },sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        reply=self._transport(body,self.timeout)
        if type(reply) is not bytes:
            raise TypeError("local transport must return bytes")
        try:
            response=json.loads(reply)
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:
            raise ValueError("invalid local model JSON response") from exc
        if type(response) is not dict or type(response.get("response")) is not str:
            raise ValueError("local model did not provide response text")
        text=response["response"]
        if not text.strip():
            raise ValueError("local model returned a blank response")
        return text
