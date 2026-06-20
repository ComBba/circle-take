from app import anchor_gate, qwen_client
from app.schemas import AnchorGateResult

ACTORS = {"actors": [{"display_name": "Luna", "fixed_markers": ["red ribbon"]}]}
STYLE = {"rules": ["handmade clay texture"]}


def test_evaluate_returns_result(monkeypatch):
    cap = {}

    def fake(system, image, user, schema, **k):
        cap.update(image=image, schema=schema, user=user)
        return schema(
            shot_id="S02_take_two",
            identity_score=93, style_score=91, prop_score=95, anchor_status="approved",
        )

    monkeypatch.setattr(qwen_client, "qwen_vision_json", fake)
    res = anchor_gate.evaluate("S02_take_two", "/tmp/f.png", ACTORS, STYLE)
    assert isinstance(res, AnchorGateResult)
    assert res.anchor_status == "approved"
    assert cap["image"] == "/tmp/f.png" and cap["schema"] is AnchorGateResult
    assert "Luna" in cap["user"]


def test_is_approved_threshold():
    ok = AnchorGateResult(shot_id="s", identity_score=93, style_score=91, prop_score=95, anchor_status="approved")
    bad = AnchorGateResult(shot_id="s", identity_score=80, style_score=91, prop_score=95, anchor_status="quarantine")
    assert anchor_gate.is_approved(ok) is True
    assert anchor_gate.is_approved(bad) is False
    assert anchor_gate.is_approved(bad, threshold=75) is True
