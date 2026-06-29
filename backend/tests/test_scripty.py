"""Agentic Scripty repair decision (Qwen mocked — no network)."""
from app import scripty
from app.schemas import RepairDecision


def test_decide_repair_returns_decision(monkeypatch):
    monkeypatch.setattr(
        scripty.qwen_client, "qwen_json",
        lambda system, user, schema, retries=1: RepairDecision(
            chosen_route="r2v",
            reasoning="the red ribbon is missing; reference role-play locks identity best",
            expected_fix="restore Luna's red ribbon",
        ),
    )
    d = scripty.decide_repair(
        {"shot_id": "S02", "violations": [{"detail": "no ribbon"}]}, ["i2v", "r2v", "kf2v"]
    )
    assert d.chosen_route == "r2v" and "ribbon" in d.reasoning.lower() and d.give_up is False


def test_decide_repair_coerces_hallucinated_route(monkeypatch):
    monkeypatch.setattr(
        scripty.qwen_client, "qwen_json",
        lambda system, user, schema, retries=1: RepairDecision(
            chosen_route="teleport", reasoning="x", expected_fix="y"
        ),
    )
    d = scripty.decide_repair({"violations": []}, ["i2v", "r2v"])
    assert d.chosen_route == "i2v"  # invented route coerced to the first available
