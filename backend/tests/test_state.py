from app.state import EpisodeStatus, next_status, can_transition


def test_linear_progression():
    assert next_status(EpisodeStatus.DRAFT) == EpisodeStatus.CONTRACTED
    assert next_status(EpisodeStatus.CUT_REQUIRED) == EpisodeStatus.RESHOOTING


def test_terminal_has_no_next():
    assert next_status(EpisodeStatus.AUTO_GREENLIT) is None


def test_illegal_transition_rejected():
    assert can_transition(EpisodeStatus.DRAFT, EpisodeStatus.REMEMBERED) is False


def test_full_chain_is_connected():
    s = EpisodeStatus.DRAFT
    steps = 0
    while (nxt := next_status(s)) is not None:
        assert can_transition(s, nxt)
        s = nxt
        steps += 1
    assert s == EpisodeStatus.AUTO_GREENLIT
    assert steps == 11  # 12 states => 11 hops
