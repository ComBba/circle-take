"""Lever 2c de-risk spike: does a reference-conditioned reshoot clear the Anchor Gate?

Generates a reshoot via i2v conditioned on the locked Luna reference keyframe, then
runs the real Qwen-vision Anchor Gate on a frame and prints the scores. This is the
empirical proof that the Identity-Lock reshoot works (vs the old blind-t2v quarantine).

Usage:  python scripts/spike_reshoot.py <reference_image_url> [i2v_model]
Reads QWEN_API_KEY from .env.local. Spends a few seconds of free-tier i2v quota.
"""
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env.local")
sys.path.insert(0, str(_ROOT / "backend"))

from app import anchor_gate, config, pipeline, video_tasks  # noqa: E402

REF_URL = sys.argv[1]
# wan2.7-i2v (unified input.media[] first-frame conditioning) is the current default;
# submit_video maps img_url -> media[{type:first_frame}]. Render-verified 2026-06-29.
I2V_MODEL = sys.argv[2] if len(sys.argv) > 2 else "wan2.7-i2v"

FIX_PROMPT = (
    "clay stop-motion, a black clay cat with a bright RED RIBBON around her neck, round "
    "yellow clay eyes and a crooked left ear, sneaky low posture, tabletop miniature set, "
    "handmade clay texture with visible fingerprints, not glossy, not photorealistic"
)
LUNA = {"actors": [{
    "display_name": "Luna",
    "fixed_markers": ["red ribbon", "yellow clay eyes", "crooked left ear"],
    "forbidden_drift": ["missing ribbon", "realistic fur", "different eye color"],
}]}
STYLE = {"rules": [
    "handmade clay texture", "visible fingerprints", "tabletop miniature set",
    "pose-to-pose stop-motion feel", "no glossy 3D look", "no photorealistic live action",
]}


def main() -> None:
    print(f"[spike] reference = {REF_URL[:80]}...")
    print(f"[spike] i2v reshoot, model={I2V_MODEL}, 5s @720P, conditioned on the locked reference")
    task_id = video_tasks.submit_video(
        "i2v", FIX_PROMPT, model=I2V_MODEL, img_url=REF_URL, resolution="720P", duration=5,
    )
    print(f"[spike] task_id={task_id}; polling (async, ~1-5 min)...")
    video_url = video_tasks.poll(task_id, interval=12, max_wait=480)
    print(f"[spike] video_url={video_url[:80]}...")

    data = httpx.get(video_url, timeout=180).content
    frame = pipeline._extract_frame_data_url(data)
    if not frame:
        print("[spike] FAILED: could not extract a frame (is ffmpeg on PATH?)")
        sys.exit(1)
    print("[spike] frame extracted; running the Anchor Gate (Qwen vision)...")

    gate = anchor_gate.evaluate("S02_take_two", frame, LUNA, STYLE).model_dump()
    worst = min(gate.get("identity_score", 0), gate.get("style_score", 0), gate.get("prop_score", 0))
    thr = config.gate_threshold()
    print(f"[spike] GATE scores = {gate}")
    print(f"[spike] worst={worst}  threshold={thr}  PASS={worst >= thr}")
    print(f"[spike] RESULT: {'PASS — reference-conditioned reshoot clears the gate' if worst >= thr else 'BELOW THRESHOLD — would escalate/tune'}")


if __name__ == "__main__":
    main()
