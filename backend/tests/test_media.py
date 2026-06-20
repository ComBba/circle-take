from app import main
from app.main import app
from fastapi.testclient import TestClient


def test_media_rejects_non_whitelisted():
    c = TestClient(app)
    assert c.get("/api/media/evil.txt").status_code == 404
    assert c.get("/api/media/secrets.env").status_code == 404


def test_media_404_when_not_generated(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "LIVE", tmp_path)  # empty dir -> fixture/offline
    c = TestClient(app)
    assert c.get("/api/media/take1_S02.mp4").status_code == 404


def test_media_serves_when_present(monkeypatch, tmp_path):
    (tmp_path / "take1_S02.mp4").write_bytes(b"\x00\x01video-bytes")
    monkeypatch.setattr(main, "LIVE", tmp_path)
    c = TestClient(app)
    r = c.get("/api/media/take1_S02.mp4")
    assert r.status_code == 200
    assert r.content == b"\x00\x01video-bytes"
