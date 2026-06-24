"""Reference Pack (identity data) + the reshoot ladder (route selection in video_router)."""
from app import reference_pack, video_router


def test_build_reference_pack_locks_primary_actor():
    ac = {"actors": [{"actor_id": "luna_cat", "display_name": "Luna", "fixed_markers": ["red ribbon", "yellow eyes"]}]}
    pack = reference_pack.build_reference_pack(ac, "https://ref/luna.png")
    assert pack["actor_id"] == "luna_cat"
    assert pack["fixed_markers"] == ["red ribbon", "yellow eyes"]
    assert pack["reference_image_url"] == "https://ref/luna.png"


def test_build_reference_pack_no_url_is_none():
    pack = reference_pack.build_reference_pack({"actors": [{"display_name": "Luna"}]}, "")
    assert pack["reference_image_url"] is None
    assert pack["actor_id"] == "Luna"  # falls back to display_name


def test_build_reference_pack_empty_actors():
    pack = reference_pack.build_reference_pack({"actors": []})
    assert pack["actor_id"] == "actor" and pack["fixed_markers"] == []


def test_reshoot_ladder_with_reference_is_conditioned():
    ladder = video_router.reshoot_ladder("https://ref/luna.png")
    assert [r["mode"] for r in ladder] == ["i2v", "r2v", "kf2v"]  # escalating, reference-conditioned
    assert ladder[0]["ref"] == {"img_url": "https://ref/luna.png"}
    assert ladder[1]["ref"] == {"reference_urls": ["https://ref/luna.png"]}
    assert ladder[2]["ref"]["first_frame_url"] == "https://ref/luna.png"


def test_reshoot_ladder_without_reference_falls_back_to_t2v():
    ladder = video_router.reshoot_ladder(None)
    assert len(ladder) == 1 and ladder[0]["mode"] == "t2v" and ladder[0]["ref"] == {}
