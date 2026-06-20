"""Generation Route Selector placeholder.

Routes each shot to T2V / I2V / R2V / VideoEdit according to risk.
"""

def select_route(shot):
    risk = shot.get("risk_level", "medium")
    needs_character = shot.get("character_critical", False)
    needs_repair = shot.get("repair", False)
    if needs_repair:
        return "videoedit_then_r2v_fallback"
    if needs_character or risk == "high":
        return "r2v"
    return "t2v"
