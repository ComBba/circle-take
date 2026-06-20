from app import contracts, qwen_client
from app.schemas import ActorContracts, StoryContract, StyleContract

BRIEF = {
    "title": "The Last Alarm",
    "logline": "A broken alarm clock learns it will be replaced.",
    "cast": ["Luna, a jealous black cat"],
    "style_contract_id": "clay_stop_motion_mvp",
}


def _patch(monkeypatch, result):
    cap = {}

    def fake(system, user, schema, **k):
        cap.update(system=system, user=user, schema=schema)
        return result

    monkeypatch.setattr(qwen_client, "qwen_json", fake)
    return cap


def test_build_actor_contracts(monkeypatch):
    res = ActorContracts(actors=[{
        "actor_id": "luna_cat", "display_name": "Luna", "role": "cat",
        "fixed_markers": ["red ribbon"], "forbidden_drift": ["missing ribbon"],
    }])
    cap = _patch(monkeypatch, res)
    out = contracts.build_actor_contracts(BRIEF)
    assert out is res
    assert cap["schema"] is ActorContracts
    assert "Luna" in cap["user"]


def test_build_style_contract(monkeypatch):
    res = StyleContract(style_id="clay_stop_motion_mvp", rules=["handmade clay texture"])
    cap = _patch(monkeypatch, res)
    out = contracts.build_style_contract(BRIEF)
    assert out is res and cap["schema"] is StyleContract


def test_build_story_contract(monkeypatch):
    res = StoryContract(title="The Last Alarm", beats={"hook": "h", "conflict": "c", "reversal": "r", "button": "b"})
    cap = _patch(monkeypatch, res)
    out = contracts.build_story_contract(BRIEF)
    assert out is res and cap["schema"] is StoryContract
