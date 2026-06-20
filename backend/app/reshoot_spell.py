"""Reshoot Spell — a delta-only repair instruction derived from the verdict.

Deterministic (no model call): turns the Continuity Court violations into a
targeted instruction that reshoots only the failed shot and reinforces each
actor's fixed markers, leaving every other shot untouched.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union

try:  # avoid hard dependency at import for tooling
    from .schemas import ContinuityVerdict
except Exception:  # pragma: no cover
    ContinuityVerdict = None  # type: ignore


def _as_dict(verdict: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    if isinstance(verdict, dict):
        return verdict
    if hasattr(verdict, "model_dump"):
        return verdict.model_dump()
    raise TypeError("verdict must be a dict or a ContinuityVerdict")


def build_reshoot_spell(
    verdict: Union[Dict[str, Any], Any],
    actor_contracts: Optional[Dict[str, Any]] = None,
) -> str:
    v = _as_dict(verdict)
    shot = v.get("shot_id", "S02")
    lines = [f"RESHOOT {shot} ONLY."]
    for viol in v.get("violations", []):
        detail = viol.get("detail") or viol.get("type") or "continuity violation"
        lines.append(f"- Fix: {detail}")
    if actor_contracts:
        for a in actor_contracts.get("actors", []):
            markers = a.get("fixed_markers")
            if markers:
                lines.append(f"Keep {a.get('display_name')}: {', '.join(markers)}.")
    lines.append(f"Preserve camera angle and action. Do not alter any shot other than {shot}.")
    return "\n".join(lines)
