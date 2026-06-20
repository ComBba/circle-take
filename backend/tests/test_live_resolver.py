from app import config, main


def test_resolve_uses_fixture_in_fixture_mode(monkeypatch):
    monkeypatch.setattr(config, "is_live", lambda: False)
    assert main._resolve_json("brief.json")["style_contract_id"] == "clay_stop_motion_mvp"


def test_resolve_prefers_live_when_live(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "is_live", lambda: True)
    monkeypatch.setattr(main, "LIVE", tmp_path)
    (tmp_path / "thing.json").write_text('{"who": "live"}')
    assert main._resolve_json("brief.json", "thing.json") == {"who": "live"}


def test_resolve_falls_back_when_live_artifact_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "is_live", lambda: True)
    monkeypatch.setattr(main, "LIVE", tmp_path)  # empty -> fall back to fixture
    assert main._resolve_json("brief.json", "missing.json")["style_contract_id"] == "clay_stop_motion_mvp"


def test_take_marker_live(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "is_live", lambda: True)
    monkeypatch.setattr(main, "LIVE", tmp_path)
    (tmp_path / "take1_S02.mp4").write_bytes(b"x")
    m = main._take_marker(1)
    assert m["source"] == "live" and "take1" in m["video"]


def test_take_marker_fixture(monkeypatch):
    monkeypatch.setattr(config, "is_live", lambda: False)
    assert main._take_marker(1)["source"] == "fixture"
