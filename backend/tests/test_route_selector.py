from app import video_router as vr


def test_repair_uses_edit_then_r2v_fallback():
    r = vr.select_route({"repair": True})
    assert r == "videoedit_then_r2v_fallback"
    assert vr.models_for(r) == [vr.WAN_EDIT, vr.WAN_R2V]


def test_high_risk_or_character_uses_r2v():
    assert vr.select_route({"risk_level": "high"}) == "r2v"
    assert vr.select_route({"character_critical": True}) == "r2v"
    assert vr.models_for("r2v") == [vr.WAN_R2V]


def test_first_or_last_frame_uses_i2v():
    assert vr.select_route({"first_or_last_frame": True}) == "i2v"
    assert vr.models_for("i2v") == [vr.WAN_I2V]


def test_default_is_t2v():
    assert vr.select_route({"risk_level": "low"}) == "t2v"
    assert vr.select_route({}) == "t2v"
    assert vr.models_for("t2v") == [vr.WAN_T2V]
