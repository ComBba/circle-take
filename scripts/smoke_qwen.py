"""Task 0.2 — live smoke test for Qwen Cloud (DashScope intl).

Confirms credentials + the latest model IDs by making ONE real call each for
text, vision-capable, and video models, then polls one video task to completion.
Promote only HTTP-200 models into docs/verified_models.md.

Usage:
    # put QWEN_API_KEY in circle-take/.env (gitignored), then:
    python scripts/smoke_qwen.py
"""
import os
import sys
import time
import json
import httpx

try:
    from pathlib import Path
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parents[1]
    load_dotenv(_root / ".env.local")  # secrets (gitignored; preferred)
    load_dotenv(_root / ".env")        # fallback if present
except Exception:
    pass

# Mode: "text" = text+vision only (cheap); "all" (default) also creates a video task.
MODE = sys.argv[1] if len(sys.argv) > 1 else "all"

KEY = os.getenv("QWEN_API_KEY", "")
if not KEY or KEY == "replace_me":
    sys.exit("QWEN_API_KEY not set. Put it in circle-take/.env.local then re-run.")

HOST = "https://dashscope-intl.aliyuncs.com"
AUTH = {"Authorization": f"Bearer {KEY}"}

TEXT_CANDIDATES = ["qwen3.7-plus", "qwen3.7-max"]
VISION_CANDIDATES = ["qwen3.7-plus"]
VIDEO_CANDIDATES = ["wan2.7-t2v", "wan2.7-i2v", "wan2.7-r2v", "wan2.7-videoedit"]


def try_chat(model: str) -> tuple[int, str]:
    try:
        r = httpx.post(
            f"{HOST}/compatible-mode/v1/chat/completions",
            headers=AUTH,
            json={"model": model, "messages": [{"role": "user", "content": "reply with the single word OK"}]},
            timeout=60,
        )
        return r.status_code, r.text[:160]
    except Exception as e:  # network/dns errors surface here, not a crash
        return -1, repr(e)[:160]


def create_video_task(model: str) -> tuple[int, str]:
    try:
        r = httpx.post(
            f"{HOST}/api/v1/services/aigc/video-generation/video-synthesis",
            headers={**AUTH, "X-DashScope-Async": "enable", "Content-Type": "application/json"},
            json={"model": model, "input": {"prompt": "a clay stop-motion cat waves, tabletop miniature"},
                  "parameters": {"size": "1280*720"}},
            timeout=60,
        )
        return r.status_code, r.text[:300]
    except Exception as e:
        return -1, repr(e)[:300]


def poll_task(task_id: str, timeout_s: int = 420) -> tuple[str, str]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        r = httpx.get(f"{HOST}/api/v1/tasks/{task_id}", headers=AUTH, timeout=60)
        body = r.json()
        status = body.get("output", {}).get("task_status", "UNKNOWN")
        if status == "SUCCEEDED":
            return status, body.get("output", {}).get("video_url", "(no url field)")
        if status in ("FAILED", "CANCELED"):
            return status, json.dumps(body)[:300]
        time.sleep(10)
    return "TIMEOUT", ""


def main() -> None:
    print("== TEXT ==")
    for m in TEXT_CANDIDATES:
        print(f"  {m}: {try_chat(m)}")
    print("== VISION-capable ==")
    for m in VISION_CANDIDATES:
        print(f"  {m}: {try_chat(m)}")
    if MODE != "all":
        print("== VIDEO skipped (text mode) ==")
        return
    print("== VIDEO (create task) ==")
    first_ok = None
    for m in VIDEO_CANDIDATES:
        code, text = create_video_task(m)
        print(f"  {m}: {code} {text}")
        if code == 200 and first_ok is None:
            try:
                tid = httpx.post(  # re-create to grab task_id cleanly
                    f"{HOST}/api/v1/services/aigc/video-generation/video-synthesis",
                    headers={**AUTH, "X-DashScope-Async": "enable", "Content-Type": "application/json"},
                    json={"model": m, "input": {"prompt": "a clay cat waves"}, "parameters": {"size": "1280*720"}},
                    timeout=60,
                ).json().get("output", {}).get("task_id")
                first_ok = (m, tid)
            except Exception as e:
                print(f"    (could not parse task_id: {e!r})")
    if first_ok and first_ok[1]:
        m, tid = first_ok
        print(f"== POLL {m} task {tid} ==")
        print("  ", poll_task(tid))
    else:
        print("No video model returned 200 — check model IDs against docs/official_sources.md")


if __name__ == "__main__":
    main()
