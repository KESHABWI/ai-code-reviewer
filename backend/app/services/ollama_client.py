"""Thin async client for the Ollama /api/chat endpoint.

Works transparently with local models and Ollama's cloud-routed models
(e.g. gpt-oss:20b-cloud) since both are served through the same OLLAMA_HOST API.
"""

import json
import re

import httpx

from app.config import get_settings


class OllamaError(RuntimeError):
    pass


def _trace(arrow: str, label: str, payload) -> None:
    if not get_settings().trace_io:
        return
    print(f"\n{arrow} {label}")
    try:
        print(json.dumps(payload, indent=2, default=str)[:2000])
    except TypeError:
        print(str(payload)[:2000])


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise OllamaError(f"Model did not return valid JSON. Got: {text[:300]}")
    return json.loads(match.group(0))


class OllamaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._host = settings.ollama_host.rstrip("/")
        self._model = settings.ollama_model
        self._timeout = settings.request_timeout_seconds

    async def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            _trace("==>", f"POST {self._host}/api/chat", payload)
            try:
                response = await client.post(f"{self._host}/api/chat", json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise OllamaError(f"Failed to reach Ollama at {self._host}: {exc}") from exc
            data = response.json()
            _trace("<==", f"POST {self._host}/api/chat response", data)

        content = data.get("message", {}).get("content", "")
        return _extract_json(content)
