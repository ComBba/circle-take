#!/usr/bin/env python3
"""Assemble the Circle Take demo video — fully automated, no human recording.

Inputs (all real, no mockups):
  - scripts/demo/build/shots/*.png  : real screenshots of the live UI (capture.mjs)
  - artifacts/live/take{1,2}_S02.mp4 : the real Wan-generated clips

Pipeline:
  1. macOS `say` (Samantha, en_US) renders per-beat narration  -> wav
  2. ffmpeg builds one 1920x1080/30fps segment per beat:
       still beats: image padded onto dark bg, narration + burnt-in caption
       clip beats : real Wan clip, narration + burnt-in caption
  3. ffmpeg concat -> fade in/out -> faststart MP4

Output: artifacts/demo/circle-take-demo.mp4  (target <= 180s)

Story arc = LIVE / honest: the Anchor Gate quarantines Take 2 (identity 15/100),
and that refusal is the point — Circle Take won't greenlight an anchor that
doesn't match, even its own reshoot.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "scripts/demo/build/shots"
CLIPS = ROOT / "artifacts/live"
WORK = ROOT / "scripts/demo/build/work"
OUT = ROOT / "artifacts/demo/circle-take-demo.mp4"
WORK.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
BG = "0x0b0b0d"
SAY_VOICE = os.environ.get("SAY_VOICE", "Samantha")
SAY_RATE = os.environ.get("SAY_RATE", "178")

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttf",
]
BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
FONT = next((f for f in FONT_CANDIDATES if Path(f).exists()), FONT_CANDIDATES[0])
BOLD = next((f for f in BOLD_CANDIDATES if Path(f).exists()), FONT)

# beat = (id, kind, asset, caption, narration, floor_seconds)
BEATS = [
    ("b1", "clip", CLIPS / "take1_S02.mp4",
     "Take 1 — a generated shot. And it just broke.",
     "This is Circle Take, and this is a generated episode. Luna, a stop motion cat. "
     "But this take just broke. Her yellow bead eyes, her crescent chest patch, her red collar. Gone.",
     12.0),
    ("b2", "still", SHOTS / "05_scene.png",
     "Circle Take does not hide a bad take. It calls cut.",
     "Circle Take does not hide a bad take. It calls cut.", 4.5),
    ("b3", "still", SHOTS / "06_scene.png",
     "Qwen judges the frame against the contracts — the verdict is real.",
     "Qwen judges the frame against the actor and style contracts. The verdict is real. "
     "Actor drift on Luna, and two actors missing. Only shot two goes back.", 12.5),
    ("b4", "still", SHOTS / "00_title.png",
     "A self-correcting production loop.",
     "Circle Take is a self correcting production loop. Catch broken continuity. "
     "Reshoot only the failed shot. Remember only approved takes.", 11.0),
    ("b5", "still", SHOTS / "02_scene.png",
     "Identity contracts: the markers that must never drift.",
     "It starts with identity contracts. Scripty defines who each actor is, "
     "and the markers that must never drift.", 10.0),
    ("b6", "still", SHOTS / "03_scene.png",
     "Every shot is scored for identity risk before a frame exists.",
     "Then a storyboard, scored for identity risk before a single frame exists. "
     "Shot two is the danger.", 9.0),
    ("b7", "still", SHOTS / "07_scene.png",
     "The repair is delta-only — reshoot shot two, and only shot two.",
     "The repair is delta only. Reshoot shot two. Restore every marker. Touch nothing else.", 8.5),
    ("b8", "clip", CLIPS / "take2_S02.mp4",
     "Wan reshoots — only shot two.",
     "Wan reshoots, but only shot two.", 4.5),
    ("b9", "still", SHOTS / "09_scene.png",
     "Identity 15/100 → QUARANTINE. The gate refuses anchors that don't match.",
     "Take two faces the anchor gate. And here is the honest part. "
     "Identity scored fifteen out of a hundred. The reshoot still missed Luna. "
     "So the gate quarantines it. Circle Take refuses to greenlight an anchor "
     "that does not match. Even its own.", 17.5),
    ("b10", "still", SHOTS / "10_scene.png",
     "Only approved anchors become memory. The failure becomes a rule.",
     "Only approved anchors become memory. The failure becomes a rule. "
     "Always preserve Luna's red ribbon. And the next episode opens from what the show remembers.", 13.5),
]

END_TITLE = "CIRCLE TAKE"
END_SUB = "Bad takes don't make the cut."
END_URL = "github.com/ComBba/circle-take   ·   Built on Qwen Cloud   ·   Track 2: AI Showrunner"
END_VO = "Circle Take. Bad takes don't make the cut."


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(map(str, cmd)) + "\n" + p.stderr[-1500:] + "\n")
        raise SystemExit(f"command failed: {cmd[0]}")


def probe_dur(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def tts(text: str, dst: Path) -> float:
    aiff = dst.with_suffix(".aiff")
    run(["say", "-v", SAY_VOICE, "-r", SAY_RATE, "-o", str(aiff), text])
    run(["ffmpeg", "-y", "-i", str(aiff), "-ar", "48000", "-ac", "2", str(dst)])
    aiff.unlink(missing_ok=True)
    return probe_dur(dst)


def wrap_caption(text: str, path: Path, width: int = 44) -> None:
    path.write_text("\n".join(textwrap.wrap(text, width=width)), encoding="utf-8")


def caption_filter(capfile: Path, size: int = 46) -> str:
    cf = str(capfile).replace(":", r"\:").replace("'", r"\'")
    ff = FONT.replace(":", r"\:")
    return (
        f"drawtext=textfile='{cf}':fontfile='{ff}':fontsize={size}:fontcolor=white:"
        f"line_spacing=14:box=1:boxcolor=black@0.62:boxborderw=30:"
        f"x=(w-text_w)/2:y=h-text_h-72"
    )


def build_segment(beat) -> Path:
    bid, kind, asset, caption, narration, floor = beat
    wav = WORK / f"{bid}.wav"
    vo = tts(narration, wav)
    seg_dur = round(max(vo + 0.7, floor), 2)
    capf = WORK / f"{bid}.txt"
    wrap_caption(caption, capf)
    seg = WORK / f"{bid}.mp4"
    cap = caption_filter(capf)

    if kind == "still":
        vf = (
            f"scale=1820:820:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:64:color={BG},setsar=1,{cap},fps={FPS}"
        )
        run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(asset),
            "-i", str(wav), "-t", f"{seg_dur}",
            "-vf", vf, "-af", "apad",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-ar", "48000", "-ac", "2", str(seg),
        ])
    else:  # clip — loop to fill seg_dur, real motion
        vf = f"scale={W}:{H},setsar=1,{cap},fps={FPS}"
        run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(asset),
            "-i", str(wav), "-t", f"{seg_dur}",
            "-vf", vf, "-af", "apad",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-ar", "48000", "-ac", "2", str(seg),
        ])
    print(f"  {bid:4} {kind:5} vo={vo:5.1f}s seg={seg_dur:5.1f}s  {caption[:48]}")
    return seg


def build_endcard() -> Path:
    wav = WORK / "end.wav"
    vo = tts(END_VO, wav)
    seg_dur = round(max(vo + 1.2, 5.0), 2)
    t = WORK / "end_title.txt"; t.write_text(END_TITLE, encoding="utf-8")
    s = WORK / "end_sub.txt"; s.write_text(END_SUB, encoding="utf-8")
    u = WORK / "end_url.txt"; u.write_text(END_URL, encoding="utf-8")
    bold = BOLD.replace(":", r"\:"); ff = FONT.replace(":", r"\:")
    vf = (
        f"drawtext=textfile='{t}':fontfile='{bold}':fontsize=150:fontcolor=0xf3ecdf:"
        f"x=(w-text_w)/2:y=h/2-150,"
        f"drawtext=textfile='{s}':fontfile='{ff}':fontsize=58:fontcolor=0xe6324b:"
        f"x=(w-text_w)/2:y=h/2+40,"
        f"drawtext=textfile='{u}':fontfile='{ff}':fontsize=34:fontcolor=0xcfd6df:"
        f"x=(w-text_w)/2:y=h-150,fps={FPS}"
    )
    seg = WORK / "end.mp4"
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={FPS}",
        "-i", str(wav), "-t", f"{seg_dur}", "-vf", vf, "-af", "apad",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-ar", "48000", "-ac", "2", str(seg),
    ])
    print(f"  end  card  vo={vo:5.1f}s seg={seg_dur:5.1f}s")
    return seg


def main() -> None:
    for b in BEATS:
        if not Path(b[2]).exists():
            raise SystemExit(f"missing asset: {b[2]}")
    print("Building segments (TTS + ffmpeg):")
    segs = [build_segment(b) for b in BEATS]
    segs.append(build_endcard())

    listf = WORK / "concat.txt"
    listf.write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    raw = WORK / "raw.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
         "-c", "copy", str(raw)])

    total = probe_dur(raw)
    fo = max(total - 0.6, 0)
    run([
        "ffmpeg", "-y", "-i", str(raw),
        "-vf", f"fade=t=in:st=0:d=0.6,fade=t=out:st={fo:.2f}:d=0.6",
        "-af", "afade=t=in:st=0:d=0.4,afade=t=out:st={:.2f}:d=0.6".format(max(total - 0.6, 0)),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT),
    ])
    final = probe_dur(OUT)
    print(f"\nDONE  {OUT.relative_to(ROOT)}  duration={final:.1f}s  ({'OK <=180' if final <= 180 else 'OVER 180!'})")


if __name__ == "__main__":
    main()
