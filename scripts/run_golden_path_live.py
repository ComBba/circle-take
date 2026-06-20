"""Run the live golden path with real Qwen3.7 + Wan2.7 + OSS.

Cost-controlled, stage-gated, idempotent (skips already-generated videos).
Outputs real artifacts to artifacts/live/ and uploads them to OSS.

Usage:
    python scripts/run_golden_path_live.py [text|video|court|all]   (default: all)
      text  - contracts + storyboard + shot risk (cheap Qwen text)
      video - + Take 1/Take 2 Wan generation + frame extraction (costs)
      court - text + video + real Continuity Court + Anchor Gate + memory + report

Demo-failure strategy = Option B (transparent constructed): Take 1 is generated with a
"no ribbon" prompt and Take 2 with a "red ribbon" prompt; both are real generations and
the Continuity Court verdict comes from a real Qwen-vision call on the actual frame.
"""
import json
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.local")  # load creds BEFORE importing app modules
sys.path.insert(0, str(ROOT / "backend"))

import httpx  # noqa: E402

from app import (  # noqa: E402
    anchor_gate,
    contracts,
    continuity_court,
    memory as memory_mod,
    oss_storage,
    reshoot_spell,
    storyboard,
    video_tasks,
)

STAGE = sys.argv[1] if len(sys.argv) > 1 else "all"
LIVE = ROOT / "artifacts" / "live"
LIVE.mkdir(parents=True, exist_ok=True)
brief = json.loads((ROOT / "examples" / "golden_path" / "brief.json").read_text())

FAIL_PROMPT = ("clay stop-motion, a black clay cat WITHOUT any ribbon hides a small paper ad "
               "under her tail, tabletop miniature set, handmade clay texture, visible fingerprints")
FIX_PROMPT = ("clay stop-motion, a black clay cat with a bright RED RIBBON and a crooked left ear "
              "hides a small paper ad under her tail, tabletop miniature set, handmade clay texture")


def save_json(name, obj):
    p = LIVE / name
    p.write_text(json.dumps(obj, indent=2))
    return p


def save_text(name, text):
    p = LIVE / name
    p.write_text(text)
    return p


def upload(key, path):
    try:
        url = oss_storage.put_file(f"live/{key}", str(path))
        print("   OSS:", url)
        return url
    except Exception as e:  # never fail the run on an upload hiccup
        print("   OSS upload skipped:", type(e).__name__, str(e)[:80])
        return None


def extract_frame(video_path, out_png, frame_no=30):
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vf", f"select=eq(n\\,{frame_no})",
         "-vframes", "1", str(out_png)],
        check=True, capture_output=True,
    )


def gen_video(prompt, out_mp4):
    if out_mp4.exists():
        print(f"   reuse {out_mp4.name}")
        return
    url = video_tasks.generate(prompt, model=video_tasks.WAN_T2V_MODEL)
    out_mp4.write_bytes(httpx.get(url, timeout=180).content)
    print(f"   wrote {out_mp4.name} ({out_mp4.stat().st_size} bytes)")


# ---------------- TEXT ----------------
print("== Contracts (qwen3.7-plus) ==")
actors = contracts.build_actor_contracts(brief).model_dump()
style = contracts.build_style_contract(brief).model_dump()
story = contracts.build_story_contract(brief).model_dump()
print("== Storyboard + Shot Risk ==")
slate = storyboard.build_storyboard(story).model_dump()
risk = storyboard.build_shot_risk_ledger(slate, actors).model_dump()
for name, obj in [("actor_contracts.json", actors), ("style_contract.json", style),
                  ("story_contract.json", story), ("storyboard_slate.json", slate),
                  ("shot_risk_ledger.json", risk)]:
    p = save_json(name, obj)
    upload(name, p)
print("TEXT stage done")
if STAGE == "text":
    sys.exit(0)

# ---------------- VIDEO ----------------
take1, take2 = LIVE / "take1_S02.mp4", LIVE / "take2_S02.mp4"
print("== Wan 2.7 Take 1 (S02, no-ribbon prompt) ==")
gen_video(FAIL_PROMPT, take1)
extract_frame(take1, LIVE / "take1_frame.png")
print("== Wan 2.7 Take 2 (S02, red-ribbon prompt) ==")
gen_video(FIX_PROMPT, take2)
extract_frame(take2, LIVE / "take2_frame.png")
for name in ["take1_S02.mp4", "take2_S02.mp4", "take1_frame.png", "take2_frame.png"]:
    upload(name, LIVE / name)
print("VIDEO stage done")
if STAGE == "video":
    sys.exit(0)

# ---------------- COURT / GATE / MEMORY ----------------
ac = {"actors": actors["actors"]}
print("== Continuity Court (real Qwen-vision on Take 1 frame) ==")
verdict = continuity_court.judge("S02", str(LIVE / "take1_frame.png"), ac, style).model_dump()
save_json("continuity_verdict.json", verdict)
upload("continuity_verdict.json", LIVE / "continuity_verdict.json")
print("   verdict:", verdict["verdict"], "| violations:", len(verdict.get("violations", [])))

spell = reshoot_spell.build_reshoot_spell(verdict, ac)
save_text("reshoot_spell.txt", spell)

print("== Anchor Gate (real Qwen-vision on Take 2 frame) ==")
gate = anchor_gate.evaluate("S02_take_two", str(LIVE / "take2_frame.png"), ac, style).model_dump()
save_json("anchor_gate.json", gate)
upload("anchor_gate.json", LIVE / "anchor_gate.json")
print("   anchor:", gate["anchor_status"],
      "| scores:", gate["identity_score"], gate["style_score"], gate["prop_score"])

mem = memory_mod.build_red_thread_memory(gate)
save_json("red_thread_memory.json", mem)

report = {
    "brief": brief,
    "contracts": {"actors": actors, "style": style, "story": story},
    "storyboard": slate, "shot_risk": risk,
    "continuity_verdict": verdict, "reshoot_spell": spell,
    "anchor_gate": gate, "red_thread_memory": mem,
}
p = save_json("production_report.json", report)
upload("production_report.json", p)
print("ALL done — live golden path complete; artifacts in artifacts/live/ + OSS live/")
