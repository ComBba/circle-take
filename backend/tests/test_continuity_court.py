from app import continuity_court as cc
from app import qwen_client
from app.schemas import ContinuityVerdict

ACTORS = {
    "actors": [
        {"display_name": "Luna", "fixed_markers": ["red ribbon"], "forbidden_drift": ["missing ribbon"]}
    ]
}
STYLE = {"rules": ["handmade clay texture", "no photorealistic live action"]}


def test_build_user_prompt_mentions_markers_and_style():
    p = cc.build_user_prompt(ACTORS, STYLE)
    assert "Luna" in p
    assert "red ribbon" in p
    assert "clay" in p


def test_judge_returns_validated_verdict(monkeypatch):
    captured = {}

    def fake(system, image, user, schema, **k):
        captured.update(system=system, image=image, user=user, schema=schema)
        return schema(
            shot_id="S02",
            verdict="fail",
            violations=[{"type": "fixed_marker_missing", "detail": "red ribbon missing"}],
            repair_action="reshoot_shot_only",
        )

    monkeypatch.setattr(qwen_client, "qwen_vision_json", fake)
    v = cc.judge("S02", "/tmp/frame.png", ACTORS, STYLE)
    assert isinstance(v, ContinuityVerdict)
    assert v.verdict == "fail"
    assert captured["image"] == "/tmp/frame.png"
    assert captured["schema"] is ContinuityVerdict
    assert "S02" in captured["user"]
