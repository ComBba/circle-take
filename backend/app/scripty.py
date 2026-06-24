"""Agentic Scripty — the Qwen-driven repair decision (the innovation headline).

At the CUT moment the showrunner does not blindly follow a hardcoded ladder: Scripty
reads the Continuity Court verdict + the available reshoot routes (and any prior Anchor
Gate result) and DECIDES which route to reshoot with, returning structured reasoning
that judges can read. The deterministic ladder stays as the fallback/guardrail when
Scripty is unavailable. Requires a Qwen key (text model).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import qwen_client
from .schemas import RepairDecision

SCRIPTY_SYSTEM = (
    "You are Scripty, the showrunner and continuity supervisor for a generated episode. "
    "A shot failed the Continuity Court. Choose the single best reshoot route from the "
    "AVAILABLE routes to restore the actor's fixed markers, and explain your choice. "
    "Prefer reference-conditioned routes (i2v/r2v/kf2v) that lock identity over plain t2v. "
    "Set give_up only if no available route could plausibly fix the violation."
)


def decide_repair(
    verdict: Dict[str, Any],
    available_routes: List[str],
    prior_gate: Optional[Dict[str, Any]] = None,
    retries: int = 1,
) -> RepairDecision:
    """Qwen picks the next reshoot route. chosen_route is coerced into available_routes."""
    prior = f"Prior Anchor Gate scores: {prior_gate} (that route did not pass).\n" if prior_gate else ""
    user = (
        f"Shot {verdict.get('shot_id', 'S02')} failed the Continuity Court.\n"
        f"Violations: {verdict.get('violations', [])}\n"
        f"{prior}"
        f"AVAILABLE reshoot routes (chosen_route MUST be one of these): {available_routes}\n"
        "Return JSON {chosen_route, reasoning, expected_fix, give_up}."
    )
    decision = qwen_client.qwen_json(SCRIPTY_SYSTEM, user, RepairDecision, retries=retries)
    # Guard against a hallucinated route: fall back to the first available one.
    if decision.chosen_route not in available_routes and available_routes:
        decision = decision.model_copy(update={"chosen_route": available_routes[0]})
    return decision
