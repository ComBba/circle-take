"""Qwen Cloud client (DashScope intl, OpenAI-compatible chat endpoint).

Schema-validated JSON helper with code-fence stripping + one retry, so model
output is always coerced into a Pydantic contract or fails loudly. Vision helper
attaches an image for the Continuity Court. Never commit API keys.

Models (centralized in .env): QWEN_TEXT_MODEL=qwen3.7-plus, QWEN_VISION_MODEL=qwen3.7-plus.
Docs: https://www.alibabacloud.com/help/en/model-studio/ (compatible-mode chat/completions).
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
from typing import Any, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_TEXT_MODEL = os.getenv("QWEN_TEXT_MODEL", "qwen3.7-plus")
QWEN_VISION_MODEL = os.getenv("QWEN_VISION_MODEL", "qwen3.7-plus")

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class QwenError(RuntimeError):
    """Qwen call failed (no key, HTTP error, or unparseable/invalid output)."""


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of a model reply (handles ```json fences + prose)."""
    m = _FENCE.search(text)
    raw = (m.group(1) if m else text).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]
    return json.loads(raw)


def chat_raw(
    messages: List[dict],
    model: Optional[str] = None,
    response_format: Optional[dict] = None,
    timeout: float = 120.0,
) -> str:
    """One chat/completions call; returns the assistant message content string."""
    if not QWEN_API_KEY:
        raise QwenError("QWEN_API_KEY not configured")
    payload: dict[str, Any] = {"model": model or QWEN_TEXT_MODEL, "messages": messages}
    if response_format:
        payload["response_format"] = response_format
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                f"{QWEN_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {QWEN_API_KEY}"},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
        return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise QwenError(f"chat HTTP {e.response.status_code}: {e.response.text[:300]}") from e
    except (httpx.HTTPError, KeyError, IndexError) as e:
        raise QwenError(f"chat call failed: {e}") from e


def _json_loop(messages: List[dict], schema: Type[T], model: Optional[str], retries: int) -> T:
    # DashScope json_object mode requires the literal word "json" in the prompt. Scanning the
    # serialized messages is unreliable — base64 image data (vision calls) can contain "json"
    # by chance — so ALWAYS inject an explicit JSON directive.
    messages = messages + [{"role": "system", "content": "Respond with a single valid JSON object."}]
    last: Exception | None = None
    for _ in range(retries + 1):
        content = chat_raw(messages, model=model, response_format={"type": "json_object"})
        try:
            return schema.model_validate(_extract_json(content))
        except (json.JSONDecodeError, ValidationError) as e:
            last = e
            messages = messages + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": f"That was not valid for the schema ({e}). Return ONLY valid JSON."},
            ]
    raise QwenError(f"qwen_json failed after {retries + 1} attempts: {last}")


def qwen_json(system: str, user: str, schema: Type[T], model: Optional[str] = None, retries: int = 1) -> T:
    """Text -> schema-validated Pydantic object."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return _json_loop(messages, schema, model or QWEN_TEXT_MODEL, retries)


def _image_content(path_or_url: str) -> dict:
    if path_or_url.startswith(("http://", "https://", "data:")):
        url = path_or_url
    else:
        mime = mimetypes.guess_type(path_or_url)[0] or "image/png"
        with open(path_or_url, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        url = f"data:{mime};base64,{b64}"
    return {"type": "image_url", "image_url": {"url": url}}


def qwen_vision_json(
    system: str, image: str, user: str, schema: Type[T], model: Optional[str] = None, retries: int = 1
) -> T:
    """Image + text -> schema-validated Pydantic object (Continuity Court)."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": [{"type": "text", "text": user}, _image_content(image)]},
    ]
    return _json_loop(messages, schema, model or QWEN_VISION_MODEL, retries)
