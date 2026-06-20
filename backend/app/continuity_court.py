"""Continuity Court — Qwen-vision verdict (the differentiator).

Sends a generated frame + the Actor/Style contracts to Qwen's multimodal model
and returns a schema-validated ContinuityVerdict. This is the "Qwen judges the
take" moment; the verdict JSON it produces is the non-staged evidence.
"""
from __future__ import annotations

from typing import Any, Dict

from . import qwen_client
from .schemas import ContinuityVerdict

CONTINUITY_COURT_SYSTEM = """
You are Scripty, a continuity supervisor for generated episodes.
Compare the generated take against Actor Contract, Style Contract, Story Contract, and Red-Thread Memory.
Return strict JSON with verdict, violations, repair_action, and memory_policy.
Do not invent extra issues. Do not approve failed keyframes.
""".strip()


def build_user_prompt(actor_contracts: Dict[str, Any], style_contract: Dict[str, Any]) -> str:
    lines = []
    for a in actor_contracts.get("actors", []):
        lines.append(
            f"- {a.get('display_name')}: keep fixed markers {a.get('fixed_markers')}; "
            f"forbid drift {a.get('forbidden_drift')}"
        )
    rules = "; ".join(style_contract.get("rules", []))
    return (
        "Judge the attached generated frame against these contracts.\n"
        "Actors:\n" + "\n".join(lines) + "\n"
        f"Style rules: {rules}\n"
        "Return strict JSON with keys: shot_id, verdict ('pass'|'fail'), "
        "violations (list of {type, actor?, prop?, detail}), repair_action, memory_policy."
    )


def judge(
    shot_id: str,
    frame: str,
    actor_contracts: Dict[str, Any],
    style_contract: Dict[str, Any],
    retries: int = 1,
) -> ContinuityVerdict:
    """Run the Continuity Court on one frame. Requires QWEN_API_KEY (vision model)."""
    user = f"shot_id={shot_id}\n" + build_user_prompt(actor_contracts, style_contract)
    return qwen_client.qwen_vision_json(
        CONTINUITY_COURT_SYSTEM, frame, user, ContinuityVerdict, retries=retries
    )
