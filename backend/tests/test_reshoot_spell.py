from app import reshoot_spell


def test_reshoot_spell_targets_failed_shot_only():
    verdict = {
        "shot_id": "S02",
        "verdict": "fail",
        "violations": [
            {"type": "fixed_marker_missing", "detail": "red ribbon missing"},
            {"type": "prop_identity_drift", "detail": "paper dial changed to digital"},
        ],
        "repair_action": "reshoot_shot_only",
    }
    actors = {"actors": [{"display_name": "Luna", "fixed_markers": ["red ribbon", "yellow clay eyes"]}]}
    spell = reshoot_spell.build_reshoot_spell(verdict, actors)
    assert "RESHOOT S02 ONLY" in spell
    assert "red ribbon" in spell
    assert "paper dial" in spell
    assert "Do not alter" in spell and "S02" in spell


def test_reshoot_spell_accepts_pydantic_verdict():
    from app.schemas import ContinuityVerdict

    v = ContinuityVerdict(
        shot_id="S03", verdict="fail",
        violations=[{"type": "x", "detail": "thing broke"}], repair_action="reshoot_shot_only",
    )
    spell = reshoot_spell.build_reshoot_spell(v)
    assert "RESHOOT S03 ONLY" in spell and "thing broke" in spell
