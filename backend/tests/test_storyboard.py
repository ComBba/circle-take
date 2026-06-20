from app import qwen_client, storyboard
from app.schemas import ShotRiskLedger, StoryboardSlate


def test_build_storyboard(monkeypatch):
    res = StoryboardSlate(shots=[{"shot_id": "S01", "action": "open"}])
    cap = {}

    def fake(system, user, schema, **k):
        cap.update(schema=schema, user=user)
        return res

    monkeypatch.setattr(qwen_client, "qwen_json", fake)
    out = storyboard.build_storyboard({"beats": {"hook": "h"}})
    assert out is res and cap["schema"] is StoryboardSlate


def test_build_shot_risk_ledger(monkeypatch):
    res = ShotRiskLedger(risks=[{"shot_id": "S02", "risk_level": "high"}])
    cap = {}

    def fake(system, user, schema, **k):
        cap.update(schema=schema, user=user)
        return res

    monkeypatch.setattr(qwen_client, "qwen_json", fake)
    out = storyboard.build_shot_risk_ledger(
        {"shots": [{"shot_id": "S02"}]},
        {"actors": [{"display_name": "Luna", "fixed_markers": ["red ribbon"]}]},
    )
    assert out is res and cap["schema"] is ShotRiskLedger
    assert "Luna" in cap["user"]
