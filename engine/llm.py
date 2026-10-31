"""Groq client (OpenAI-compatible) for OpenAI's open-weight gpt-oss models.

Records token usage and cost for every call so the notebook can report token
and cost figures for a representative run. Retries on rate limits (HTTP 429)
using the retry-after header, and on malformed JSON once.
"""
import json
import os
import re
import time

import httpx

from .config import MODEL, PRICES

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(RuntimeError):
    pass


class DailyLimit(LLMError):
    """Free-tier daily token/request cap: retrying will not help until it resets."""


class Usage:
    """Accumulates usage across calls (one per registration session or eval run)."""

    def __init__(self):
        self.calls = []

    def add(self, step, model, usage, latency):
        p = PRICES.get(model, {"input": 0.15, "output": 0.60})
        pin = usage.get("prompt_tokens", 0)
        pout = usage.get("completion_tokens", 0)
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        cost = pin / 1e6 * p["input"] + pout / 1e6 * p["output"]
        self.calls.append({"step": step, "model": model, "prompt_tokens": pin, "completion_tokens": pout,
                           "reasoning_tokens": reasoning, "cost_usd": cost, "latency_s": round(latency, 2)})

    def summary(self):
        t = {"calls": len(self.calls), "prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "cost_usd": 0.0, "latency_s": 0.0}
        for c in self.calls:
            for k in ("prompt_tokens", "completion_tokens", "reasoning_tokens", "cost_usd", "latency_s"):
                t[k] += c[k]
        t["total_tokens"] = t["prompt_tokens"] + t["completion_tokens"]
        t["cost_usd"] = round(t["cost_usd"], 6)
        t["latency_s"] = round(t["latency_s"], 2)
        return t


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def chat_json(system: str, user: str, *, step: str, usage: Usage | None = None, model: str | None = None,
              reasoning_effort: str = "low", max_tokens: int = 2500, temperature: float = 0.2,
              api_key: str | None = None, client: httpx.Client | None = None) -> dict:
    """Call the model and return parsed JSON. Raises LLMError on failure."""
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set")
    model = model or MODEL
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "reasoning_effort": reasoning_effort,
        "include_reasoning": False,
    }
    own = client is None
    client = client or httpx.Client(timeout=60)
    try:
        last_err = None
        max_wait = float(os.environ.get("GROQ_MAX_WAIT", 12))  # the eval runner raises this; web requests must finish < 60 s
        attempts = int(os.environ.get("GROQ_ATTEMPTS", 4))
        for attempt in range(attempts):
            t0 = time.time()
            try:
                r = client.post(GROQ_URL, json=body, headers={"Authorization": f"Bearer {key}"})
            except httpx.HTTPError as e:
                last_err = str(e)
                time.sleep(min(2 ** attempt, 4))
                continue
            if r.status_code == 429 and ("per day" in r.text or "TPD" in r.text or "RPD" in r.text):
                raise DailyLimit(f"Groq daily limit reached for {model}: {r.text[:200]}")
            if r.status_code == 429:
                wait = float(r.headers.get("retry-after", 2 ** attempt))
                time.sleep(min(wait, max_wait) + 0.5)
                last_err = "rate limited"
                continue
            if r.status_code == 400 and ("include_reasoning" in r.text or "reasoning_effort" in r.text):
                body.pop("include_reasoning", None)
                body.pop("reasoning_effort", None)
                continue
            if r.status_code == 400 and "json_validate_failed" in r.text and attempt < 2:
                last_err = "json_validate_failed"
                continue
            if r.status_code >= 400:
                raise LLMError(f"Groq HTTP {r.status_code}: {r.text[:300]}")
            data = r.json()
            if usage is not None:
                usage.add(step, model, data.get("usage", {}), time.time() - t0)
            content = data["choices"][0]["message"].get("content") or ""
            try:
                return _extract_json(content)
            except (json.JSONDecodeError, ValueError):
                last_err = "invalid JSON from model"
                body["messages"].append({"role": "assistant", "content": content[:2000]})
                body["messages"].append({"role": "user", "content": "That was not valid JSON. Reply with the JSON object only."})
        raise LLMError(f"model call failed after retries: {last_err}")
    finally:
        if own:
            client.close()
