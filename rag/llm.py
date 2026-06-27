"""Thin, model-agnostic LLM client.

One interface (`LLMClient.complete`) over two free backends — Groq (hosted) and
Ollama (offline). Keeping it thin is deliberate: the pipeline never imports a
provider SDK directly, so swapping models is a one-line config change.
"""
from __future__ import annotations

import json
import time
from functools import lru_cache

import requests

from .config import CONFIG, Config


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or CONFIG
        self.provider = self.cfg.llm_provider.lower()
        self._groq = None
        if self.provider == "groq":
            if not self.cfg.groq_api_key:
                raise LLMError(
                    "LLM_PROVIDER=groq but GROQ_API_KEY is empty. Set it in .env "
                    "or switch LLM_PROVIDER=ollama for offline mode."
                )
            from groq import Groq  # lazy import so ollama-only users don't need it

            self._groq = Groq(api_key=self.cfg.groq_api_key)

    @property
    def model(self) -> str:
        return self.cfg.groq_model if self.provider == "groq" else self.cfg.ollama_model

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = False,
        retries: int = 4,
    ) -> str:
        """Return the model's text completion. Retries on transient/rate errors
        with exponential backoff (Groq free tier is rate-limited, not metered)."""
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                if self.provider == "groq":
                    return self._complete_groq(
                        prompt, system, temperature, max_tokens, json_mode
                    )
                return self._complete_ollama(
                    prompt, system, temperature, max_tokens, json_mode
                )
            except Exception as e:  # noqa: BLE001 - we re-raise after backoff
                last_err = e
                wait = min(2 ** attempt, 20)
                time.sleep(wait)
        raise LLMError(f"LLM call failed after {retries} attempts: {last_err}")

    def complete_json(self, prompt: str, system: str | None = None, **kw) -> dict:
        """Completion that must parse as a JSON object. Tolerates the model
        wrapping JSON in prose or ```json fences."""
        raw = self.complete(prompt, system=system, json_mode=True, **kw)
        return _extract_json(raw)

    # --- backends ----------------------------------------------------------
    def _complete_groq(self, prompt, system, temperature, max_tokens, json_mode) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs = dict(
            model=self.cfg.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._groq.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def _complete_ollama(self, prompt, system, temperature, max_tokens, json_mode) -> str:
        payload = {
            "model": self.cfg.ollama_model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        r = requests.post(
            f"{self.cfg.ollama_host}/api/generate", json=payload, timeout=120
        )
        r.raise_for_status()
        return r.json().get("response", "")


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise


@lru_cache(maxsize=1)
def get_llm() -> LLMClient:
    """Process-wide singleton so we don't re-init the client per call."""
    return LLMClient()
