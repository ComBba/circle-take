#!/usr/bin/env python3
"""qc.py — objective quality gate for the finished demo video.

Adapted from Two-Weeks-Team/demo-forge's guardrails. Checks resolution/fps,
duration <= cap, integrated loudness / true-peak near target (-14 LUFS / -1 dBTP),
and a mid-roll black-frame scan. Exit 0 = PASS. The subjective
"does this look generic?" critique stays a human judgement, not here.

Usage: python scripts/demo/qc.py [video.mp4] [--cap 180] [--lufs -14] [--json out.json]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "artifacts/demo/circle-take-demo.mp4"


def sh(args: list) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], capture_output=True, text=True)


def probe(video: str) -> dict:
    r = sh(["ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate",
            "-show_entries", "format=duration", "-of", "json", video])
    d = json.loads(r.stdout or "{}")
    st = (d.get("streams") or [{}])[0]
    n, dn = (st.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = round(float(n) / float(dn), 2) if float(dn) else 0
    return {"width": st.get("width"), "height": st.get("height"), "fps": fps,
            "duration": round(float(d.get("format", {}).get("duration", 0)), 3)}


def loudness(video: str) -> dict:
    r = sh(["ffmpeg", "-hide_banner", "-nostdin", "-i", video,
            "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    blk = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr)
    if not blk:
        return {}
    d = json.loads(blk.group())
    return {"lufs": float(d["input_i"]), "true_peak": float(d["input_tp"]),
            "lra": float(d["input_lra"])}


def black_frames(video: str) -> list:
    # pix_th=0.02 counts only TRUE black (darker than our #0b0b0d brand bg, luma ~0.043),
    # so legitimate dark-themed cards aren't false-flagged — only real gaps/glitches.
    r = sh(["ffmpeg", "-hide_banner", "-nostdin", "-i", video,
            "-vf", "blackdetect=d=0.3:pic_th=0.98:pix_th=0.02", "-an", "-f", "null", "-"])
    return re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)


def run_qc(video: str, cap: float = 180.0, lufs_target: float = -14.0) -> dict:
    p = probe(video)
    loud = loudness(video)
    blk = black_frames(video)
    dur = p["duration"]
    checks = {
        "resolution_ok": (p["width"] or 0) >= 1920,
        "fps_ok": p["fps"] >= 24,
        "duration_ok": dur <= cap,
        "loudness_ok": bool(loud) and abs(loud.get("lufs", -99) - lufs_target) <= 1.5,
        "true_peak_ok": bool(loud) and loud.get("true_peak", 99) <= -0.5,
        # only mid-roll black is a problem; intentional fades at the very ends are fine
        "no_midroll_black": all(float(s) < 1.0 or float(e) > dur - 1.0 for s, e in blk),
    }
    return {"video": video, "probe": p, "loudness": loud,
            "black_frames": blk, "checks": checks, "PASS": all(checks.values())}


def main() -> None:
    a = sys.argv[1:]

    def arg(k, d=None):
        return a[a.index(k) + 1] if k in a else d

    video = next((x for x in a if not x.startswith("--") and a[a.index(x) - 1] not in
                  ("--cap", "--lufs", "--json")), str(DEFAULT))
    rep = run_qc(video, float(arg("--cap", 180)), float(arg("--lufs", -14)))
    out = json.dumps(rep, indent=2)
    if arg("--json"):
        Path(arg("--json")).write_text(out, encoding="utf-8")
    print(out)
    print("\nQC:", "PASS ✅" if rep["PASS"] else "FAIL ❌")
    raise SystemExit(0 if rep["PASS"] else 1)


if __name__ == "__main__":
    main()
