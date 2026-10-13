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
        max_output_tokens: int = 64,
        transport: Callable[[bytes, float], bytes] | None = None,
    ) -> None:
        if (type(model) is not str or _NAME.fullmatch(model) is None
                or model.startswith((".", "/", "-")) or ".." in model
                or "://" in model):
            raise ValueError("model must be a bounded Ollama model tag")
        if type(timeout) not in (int,float) or not 0 < timeout <= 900:
            raise ValueError("timeout must be between 0 and 900 seconds")
        if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 512:
            raise ValueError("max_output_tokens must be an integer from 1 to 512")
        if transport is not None and not callable(transport):
            raise TypeError("transport must be a trusted callable")
        self.model=model
        self.timeout=float(timeout)
        self.max_output_tokens=max_output_tokens
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
            "options":{"temperature":0,"num_predict":self.max_output_tokens},
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



class LocalOllamaConfiguredRenderer:
    """Two-lane localhost adapter for trusted renderer-only instructions.

    Input lane 1: EXACT admitted first-person text in the prompt field.
    Input lane 2: trusted host configuration in the system field, never cognition.
    No history, oracle, host state, audit, user metadata or tool data is sent.
    This general transport is usable by any host of the speech governor.
    """

    def __init__(
        self, model: str, *, timeout: float = 120.0,
        max_output_tokens: int = 120,
        transport: Callable[[bytes, float], bytes] | None = None,
    ):
        validated = LocalOllamaRenderer(
            model, timeout=timeout, max_output_tokens=max_output_tokens,
            transport=transport,
        )
        self.model = validated.model
        self.timeout = validated.timeout
        self.max_output_tokens = validated.max_output_tokens
        self._transport = validated._transport

    def __call__(self, subject_text: str, trusted_instruction: str) -> str:
        if type(subject_text) is not str or not subject_text.strip():
            raise TypeError("First-person subject frame required")
        if len(subject_text) > 32000:
            raise ValueError("Admitted frame exceeds local limit")
        if type(trusted_instruction) is not str or not trusted_instruction.strip():
            raise TypeError("Trusted renderer instructions required")
        if len(trusted_instruction) > 4000:
            raise ValueError("Renderer-only instruction exceeds bound")
        payload = json.dumps({
            "model": self.model,
            "prompt": subject_text,
            "system": trusted_instruction,
            "stream": False,
            "options": {"temperature": 0, "num_predict": self.max_output_tokens},
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")
        response = self._transport(payload, self.timeout)
        if type(response) is not bytes:
            raise TypeError("Local model transport returned no bytes")
        try:
            decoded = json.loads(response)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid model response JSON") from exc
        if type(decoded) is not dict:
            raise ValueError("Invalid model payload shape")
        value = decoded.get("response")
        if type(value) is not str or not value.strip():
            raise ValueError("Missing nonempty model speech")
        return value.strip()
