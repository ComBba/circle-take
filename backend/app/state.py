"""Episode state machine for Circle Take.

Linear golden-path progression DRAFT -> AUTO_GREENLIT. Only adjacent
transitions are legal. See docs/PLAN.md Phase 1.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


class EpisodeStatus(str, Enum):
    DRAFT = "DRAFT"
    CONTRACTED = "CONTRACTED"
    STORYBOARDED = "STORYBOARDED"
    GENERATING = "GENERATING"
    TAKE_1_READY = "TAKE_1_READY"
    REVIEWING = "REVIEWING"
    CUT_REQUIRED = "CUT_REQUIRED"
    RESHOOTING = "RESHOOTING"
    TAKE_2_READY = "TAKE_2_READY"
    ANCHOR_APPROVED = "ANCHOR_APPROVED"
    REMEMBERED = "REMEMBERED"
    AUTO_GREENLIT = "AUTO_GREENLIT"


# Canonical golden-path order. Index adjacency defines legal transitions.
ORDER: list[EpisodeStatus] = [
    EpisodeStatus.DRAFT,
    EpisodeStatus.CONTRACTED,
    EpisodeStatus.STORYBOARDED,
    EpisodeStatus.GENERATING,
    EpisodeStatus.TAKE_1_READY,
    EpisodeStatus.REVIEWING,
    EpisodeStatus.CUT_REQUIRED,
    EpisodeStatus.RESHOOTING,
    EpisodeStatus.TAKE_2_READY,
    EpisodeStatus.ANCHOR_APPROVED,
    EpisodeStatus.REMEMBERED,
    EpisodeStatus.AUTO_GREENLIT,
]


def next_status(current: EpisodeStatus) -> Optional[EpisodeStatus]:
    """Return the next state in the golden path, or None if terminal."""
    i = ORDER.index(current)
    return ORDER[i + 1] if i + 1 < len(ORDER) else None


def can_transition(a: EpisodeStatus, b: EpisodeStatus) -> bool:
    """True only when b is the immediate successor of a."""
    return next_status(a) == b
