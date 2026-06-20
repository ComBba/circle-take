import json
from pathlib import Path

from app import schemas

GOLDEN = Path(__file__).resolve().parents[2] / "examples" / "golden_path"


def _load(name):
    return json.loads((GOLDEN / name).read_text())


def test_brief_fixture():
    b = schemas.EpisodeBrief(**_load("brief.json"))
    assert b.style_contract_id == "clay_stop_motion_mvp"


def test_continuity_verdict_before_fixture():
    v = schemas.ContinuityVerdict(**_load("continuity_verdict_before.json"))
    assert v.verdict == "fail"
    assert v.shot_id == "S02"
    assert v.memory_policy == "quarantine_failed_keyframe"


def test_shot_risk_ledger_fixture():
    ledger = schemas.ShotRiskLedger(**_load("shot_risk_ledger.json"))
    s02 = next(r for r in ledger.risks if r.shot_id == "S02")
    assert s02.risk_level == "high"
    assert s02.route == "r2v"


def test_red_thread_memory_fixture():
    m = schemas.RedThreadMemory(**_load("red_thread_memory.json"))
    assert m.story_memory.new_fact.startswith("Luna hid")
    assert m.auto_greenlight is not None
    assert m.auto_greenlight.episode_2_title == "The Delivery Box"
