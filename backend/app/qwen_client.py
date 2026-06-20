"""Qwen Cloud client placeholder.

Use OpenAI-compatible client patterns against Qwen Cloud compatible endpoint.
Never commit API keys.
"""

import os
import httpx

QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

async def qwen_chat(messages, model="qwen3.7-plus", response_format=None):
    """TODO: replace with official/compatible SDK call.

    This function should be used for:
    - contracts
    - storyboard slate
    - shot risk ledger
    - continuity verdict JSON
    - reshoot spell
    - auto greenlight
    """
    if not QWEN_API_KEY:
        return {"mock": True, "message": "QWEN_API_KEY not configured"}
    headers = {"Authorization": f"Bearer {QWEN_API_KEY}"}
    payload = {"model": model, "messages": messages}
    if response_format:
        payload["response_format"] = response_format
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{QWEN_BASE_URL}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()
