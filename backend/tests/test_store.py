import os
import tempfile

from app.store import Store


def _store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def test_create_and_get_episode():
    s = _store()
    eid = s.create_episode("The Last Alarm", "DRAFT")
    ep = s.get_episode(eid)
    assert ep["title"] == "The Last Alarm"
    assert ep["state"] == "DRAFT"
    assert ep["episode_id"] == eid


def test_update_status():
    s = _store()
    eid = s.create_episode("X", "DRAFT")
    s.update_status(eid, "CONTRACTED")
    assert s.get_episode(eid)["state"] == "CONTRACTED"


def test_artifact_roundtrip_and_upsert():
    s = _store()
    eid = s.create_episode("X", "DRAFT")
    s.put_artifact(eid, "brief", {"title": "X"})
    assert s.get_artifact(eid, "brief") == {"title": "X"}
    s.put_artifact(eid, "brief", {"title": "Y"})  # upsert, not duplicate
    assert s.get_artifact(eid, "brief") == {"title": "Y"}
    assert s.get_episode(eid)["artifacts"]["brief"] == {"title": "Y"}


def test_missing_returns_none():
    s = _store()
    assert s.get_episode("nope") is None
    eid = s.create_episode("X", "DRAFT")
    assert s.get_artifact(eid, "missing") is None
