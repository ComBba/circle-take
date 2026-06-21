#!/usr/bin/env python3
"""Assemble the Circle Take demo video — cinematic cut, fully automated.

Not a slideshow: the visual spine is REAL on-screen motion —
  - the Three.js "circle of takes" hero rotating (motion/hero.webm)
  - the autonomous roll scroll montage, Wan clips playing (motion/montage.webm)
  - the CUT clapper and the Anchor Gate QUARANTINE stamp animating in
  - the two real Wan clips (artifacts/live/take{1,2}_S02.mp4)
Detail close-ups use Ken Burns (slow zoom). Every cut is a crossfade.
Narration is macOS `say` (Samantha) — no mic, no copyrighted audio.

Inputs:
  scripts/demo/build/shots/*.png    (capture.mjs        — UI stills)
  scripts/demo/build/motion/*.webm  (capture_motion.mjs — UI motion)
  artifacts/live/take{1,2}_S02.mp4  (real Wan clips)

Output: artifacts/demo/circle-take-demo.mp4  (1080p30, target <= 180 s)

Arc = LIVE / honest: the Anchor Gate quarantines Take 2 (identity 15/100), and
that refusal is the point.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "scripts/demo/build/shots"
MOTION = ROOT / "scripts/demo/build/motion"
CLIPS = ROOT / "artifacts/live"
WORK = ROOT / "scripts/demo/build/work"
OUT = ROOT / "artifacts/demo/circle-take-demo.mp4"
WORK.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30
BG = "0x0b0b0d"
XF = 0.5  # crossfade duration between every beat
SAY_VOICE = os.environ.get("SAY_VOICE", "Samantha")
SAY_RATE = os.environ.get("SAY_RATE", "178")

FONT = next(
    (f for f in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/Library/Fonts/Arial.ttf") if Path(f).exists()),
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)
BOLD = next(
    (f for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                 FONT) if Path(f).exists()),
    FONT,
)

# Each beat: dict(id, kind, asset, dir?, caption, vo, floor)
#   kind "motion" -> clip (webm/mp4), filled/looped to seg length
#   kind "kb"     -> still with Ken Burns (dir: in|out)
#   kind "end"    -> motion hero bg, dimmed, with title card
BEATS = [
    dict(id="b01", kind="motion", asset=CLIPS / "take1_S02.mp4",
         caption="Take 1 — a generated shot.",
         vo="This is a generated episode. A clay micro drama. Meet Luna, a stop "
            "motion cat. Roll Take 1. But watch closely. Her yellow bead eyes, her "
            "crescent chest patch, her red collar. Already gone.",
         floor=15.0),
    dict(id="b02", kind="kb", asset=SHOTS / "05_scene.png", dir="in",
         caption="It calls cut.",
         vo="Circle Take does not hide a bad take. It calls cut.", floor=6.0),
    dict(id="b03", kind="kb", asset=SHOTS / "06_scene.png", dir="in",
         caption="A real Qwen verdict: FAIL.",
         vo="The take is not trusted. It is judged. Qwen's vision model returns a "
            "real verdict. Fail. Actor drift on Luna. The broken alarm clock, "
            "missing. Arthur, missing.",
         floor=16.0),
    dict(id="b04", kind="motion", asset=MOTION / "hero.webm",
         caption="Circle Take — a self-correcting production loop.",
         vo="This is Circle Take. A self correcting production loop for generated "
            "episodes.", floor=8.5),
    dict(id="b05", kind="motion", asset=MOTION / "montage.webm",
         caption="Catch. Reshoot only what failed. Remember only what's approved.",
         vo="Catch broken continuity. Reshoot only the failed shot. Remember only "
            "approved takes. The whole pipeline runs itself.", floor=12.5),
    dict(id="b06", kind="kb", asset=SHOTS / "01_scene.png", dir="out",
         caption="It starts with a brief.",
         vo="It begins with a brief. A broken alarm clock learns it will be "
            "replaced, and a jealous cat hides the evidence.", floor=11.0),
    dict(id="b07", kind="kb", asset=SHOTS / "02_scene.png", dir="in",
         caption="Identity contracts: the markers that must never drift.",
         vo="Scripty turns that brief into identity contracts. Each actor's fixed "
            "markers. Luna's bead eyes, her crescent patch, her frayed red collar. "
            "And the drifts that are forbidden.", floor=16.0),
    dict(id="b08", kind="kb", asset=SHOTS / "03_scene.png", dir="out",
         caption="Every shot scored for identity risk — before a frame exists.",
         vo="Every shot is scored for identity risk before a single frame exists. "
            "Shot two is the danger. The clock strains, and Luna's markers can "
            "vanish.", floor=14.0),
    dict(id="b09", kind="kb", asset=SHOTS / "04_scene.png", dir="in",
         caption="Different shots take different generation routes.",
         vo="Wan generates each shot. And it does not use one route for all of them. "
            "References for character critical frames. Targeted edits for repairable "
            "ones.", floor=13.0),
    dict(id="b10", kind="kb", asset=SHOTS / "07_scene.png", dir="in",
         caption="The repair is a delta-only spell.",
         vo="When a shot fails, the fix is a delta only spell. Reshoot shot two. "
            "Restore every marker. Preserve the camera. Touch nothing else.",
         floor=14.0),
    dict(id="b11", kind="motion", asset=CLIPS / "take2_S02.mp4",
         caption="Wan reshoots — only shot two.",
         vo="Wan reshoots. But only shot two.", floor=6.0),
    dict(id="b12", kind="kb", asset=SHOTS / "09_scene.png", dir="out",
         caption="Identity 15/100 → QUARANTINE.",
         vo="Take two faces the anchor gate. And here is the honest part. Identity "
            "scored fifteen out of a hundred. The reshoot still missed Luna. So the "
            "gate quarantines it. Circle Take refuses to greenlight an anchor that "
            "does not match. Even its own.", floor=16.0),
    dict(id="b13", kind="kb", asset=SHOTS / "10_scene.png", dir="out",
         caption="Only approved anchors become memory.",
         vo="Only approved anchors become memory. The failure becomes a rule. Always "
            "preserve Luna's red ribbon. And the next episode, The Delivery Box, "
            "opens from what the show remembers.", floor=16.0),
    dict(id="end", kind="end", asset=MOTION / "hero.webm",
         caption="",
         vo="Circle Take. Bad takes don't make the cut.", floor=7.0),
]

END_TITLE = "CIRCLE TAKE"
END_SUB = "Bad takes don't make the cut."
END_URL = "github.com/ComBba/circle-take   ·   Built on Qwen Cloud   ·   Track 2: AI Showrunner"


def run(cmd: list) -> None:
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(str(c) for c in cmd) + "\n" + p.stderr[-1800:] + "\n")
        raise SystemExit(f"command failed: {cmd[0]}")


def probe_dur(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def tts(text: str, dst: Path) -> float:
    aiff = dst.with_suffix(".aiff")
    run(["say", "-v", SAY_VOICE, "-r", SAY_RATE, "-o", aiff, text])
    run(["ffmpeg", "-y", "-i", aiff, "-ar", "48000", "-ac", "2", dst])
    aiff.unlink(missing_ok=True)
    return probe_dur(dst)


def caption_vf(caption: str, bid: str, size: int = 48) -> str:
    if not caption:
        return ""
    capf = WORK / f"{bid}.txt"
    capf.write_text("\n".join(textwrap.wrap(caption, width=42)), encoding="utf-8")
    cf = str(capf).replace(":", r"\:")
    ff = FONT.replace(":", r"\:")
    return (
        f",drawtext=textfile='{cf}':fontfile='{ff}':fontsize={size}:fontcolor=white:"
        f"line_spacing=14:box=1:boxcolor=black@0.62:boxborderw=30:"
        f"x=(w-text_w)/2:y=h-text_h-86"
    )


def kenburns_vf(direction: str, dur: float) -> str:
    """Ken Burns via upscale + time-driven crop pan (reliably visible motion)."""
    # Scale the card small (generous margins), upscale the padded frame only 1.08x,
    # then pan: the card stays fully on-screen while the framing drifts -> motion,
    # no clipped text.
    up = int(W * 1.08) - (int(W * 1.08) % 2)
    if direction == "in":      # camera drifts left -> right
        x, y = f"(iw-{W})*min(t/{dur}\\,1)", f"(ih-{H})/2"
    elif direction == "out":   # camera drifts right -> left
        x, y = f"(iw-{W})*(1-min(t/{dur}\\,1))", f"(ih-{H})/2"
    else:                       # vertical drift top -> bottom
        x, y = f"(iw-{W})/2", f"(ih-{H})*min(t/{dur}\\,1)"
    return (
        f"scale=1560:840:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG},setsar=1,"
        f"scale={up}:-2,crop={W}:{H}:x='{x}':y='{y}'"
    )


def build_segment(beat: dict) -> tuple[Path, float]:
    bid = beat["id"]
    wav = WORK / f"{bid}.wav"
    vo = tts(beat["vo"], wav)
    seg_dur = round(max(vo + 0.8, beat["floor"]), 2)
    seg = WORK / f"{bid}.mp4"
    cap = caption_vf(beat["caption"], bid)

    if beat["kind"] == "kb":
        vf = f"{kenburns_vf(beat['dir'], seg_dur)}{cap},fps={FPS}"
        run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", FPS, "-t", seg_dur,
            "-i", beat["asset"], "-i", wav,
            "-vf", vf, "-af", "apad", "-t", seg_dur,
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS,
            "-c:a", "aac", "-ar", "48000", "-ac", "2", seg,
        ])
    elif beat["kind"] == "end":
        ff = FONT.replace(":", r"\:")
        bf = BOLD.replace(":", r"\:")
        for nm, val in (("end_t.txt", END_TITLE), ("end_s.txt", END_SUB), ("end_u.txt", END_URL)):
            (WORK / nm).write_text(val, encoding="utf-8")
        t = str(WORK / "end_t.txt").replace(":", r"\:")
        s = str(WORK / "end_s.txt").replace(":", r"\:")
        u = str(WORK / "end_u.txt").replace(":", r"\:")
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"setsar=1,fps={FPS},eq=brightness=-0.34,"
            f"drawtext=textfile='{t}':fontfile='{bf}':fontsize=150:fontcolor=0xf3ecdf:"
            f"x=(w-text_w)/2:y=h/2-150,"
            f"drawtext=textfile='{s}':fontfile='{ff}':fontsize=58:fontcolor=0xe6324b:"
            f"x=(w-text_w)/2:y=h/2+40,"
            f"drawtext=textfile='{u}':fontfile='{ff}':fontsize=34:fontcolor=0xcfd6df:"
            f"x=(w-text_w)/2:y=h-150"
        )
        run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", beat["asset"], "-i", wav,
            "-t", seg_dur, "-vf", vf, "-af", "apad",
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS,
            "-c:a", "aac", "-ar", "48000", "-ac", "2", seg,
        ])
    else:  # motion clip
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"setsar=1,fps={FPS}{cap}"
        )
        run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", beat["asset"], "-i", wav,
            "-t", seg_dur, "-vf", vf, "-af", "apad",
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS,
            "-c:a", "aac", "-ar", "48000", "-ac", "2", seg,
        ])

    print(f"  {bid:4} {beat['kind']:6} vo={vo:5.1f}s seg={seg_dur:5.1f}s  {beat['caption'][:42]}")
    return seg, seg_dur


def assemble(segs: list, durs: list) -> None:
    """Single ffmpeg pass: xfade video + acrossfade audio across all beats."""
    inputs: list = []
    for s in segs:
        inputs += ["-i", str(s)]

    vchain = []
    prev = "[0:v]"
    acc = durs[0]
    for k in range(1, len(segs)):
        out = f"[vx{k}]"
        off = acc - XF
        vchain.append(
            f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{out}")
        prev = out
        acc = acc + durs[k] - XF
    total = acc
    vchain.append(f"{prev}fade=t=in:st=0:d=0.5,fade=t=out:st={total - 0.6:.2f}:d=0.6[vout]")

    achain = []
    prevA = "[0:a]"
    for k in range(1, len(segs)):
        out = f"[ax{k}]"
        achain.append(f"{prevA}[{k}:a]acrossfade=d={XF}{out}")
        prevA = out
    achain.append(f"{prevA}afade=t=in:st=0:d=0.4,afade=t=out:st={total - 0.6:.2f}:d=0.6[aout]")

    fc = ";".join(vchain + achain)
    run([
        "ffmpeg", "-y", *inputs, "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-r", FPS,
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT),
    ])


def main() -> None:
    for b in BEATS:
        if not Path(b["asset"]).exists():
            raise SystemExit(f"missing asset: {b['asset']}")
    print("Building cinematic segments (TTS + ffmpeg motion/Ken Burns):")
    segs, durs = [], []
    for b in BEATS:
        s, d = build_segment(b)
        segs.append(s)
        durs.append(d)
    print("Assembling with crossfades...")
    assemble(segs, durs)
    final = probe_dur(OUT)
    flag = "OK <=180" if final <= 180 else "OVER 180!"
    print(f"\nDONE  {OUT.relative_to(ROOT)}  duration={final:.1f}s  ({flag})")


if __name__ == "__main__":
    main()
