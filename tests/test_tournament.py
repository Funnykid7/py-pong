import pytest
from src.tournament import Slot, Match, TournamentManager


def _human(label: str) -> Slot:
    return Slot(label=label, is_cpu=False, difficulty="EASY")


def _cpu(difficulty: str) -> Slot:
    return Slot(label=f"CPU-{difficulty}", is_cpu=True, difficulty=difficulty)


def _4player() -> TournamentManager:
    return TournamentManager([_human("P1"), _human("P2"), _human("P3"), _human("P4")])


def _8player() -> TournamentManager:
    return TournamentManager([_human(f"P{i+1}") for i in range(8)])


# ── 4-player ──────────────────────────────────────────────────────────────────

def test_4player_first_match_is_slot0_vs_slot1():
    tm = _4player()
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 1


def test_4player_second_match_is_slot2_vs_slot3():
    tm = _4player()
    tm.record_result(0)
    m = tm.next_match()
    assert m.slot_a == 2 and m.slot_b == 3


def test_4player_winner_propagates_to_final_slot_a():
    tm = _4player()
    tm.record_result(1)  # P2 wins semi 1
    assert tm.rounds[1][0].slot_a == 1


def test_4player_winner_propagates_to_final_slot_b():
    tm = _4player()
    tm.record_result(0)  # P1 wins semi 1
    tm.record_result(3)  # P4 wins semi 2
    assert tm.rounds[1][0].slot_b == 3


def test_4player_final_match_uses_propagated_slots():
    tm = _4player()
    tm.record_result(0)  # P1 wins semi 1
    tm.record_result(2)  # P3 wins semi 2
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 2


def test_4player_not_complete_before_final():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(2)
    assert tm.is_complete() is False


def test_4player_complete_after_final():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(2)
    tm.record_result(0)  # P1 wins final
    assert tm.is_complete() is True


def test_4player_champion_after_final():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(3)
    tm.record_result(0)  # P1 wins final
    assert tm.champion().label == "P1"


def test_next_match_returns_none_when_complete():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(2)
    tm.record_result(0)
    assert tm.next_match() is None


def test_champion_returns_none_when_not_complete():
    tm = _4player()
    assert tm.champion() is None


# ── 8-player ──────────────────────────────────────────────────────────────────

def test_8player_has_three_rounds():
    tm = _8player()
    assert len(tm.rounds) == 3


def test_8player_round0_has_4_matches():
    tm = _8player()
    assert len(tm.rounds[0]) == 4


def test_8player_first_match_is_slot0_vs_slot1():
    tm = _8player()
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 1


def test_8player_advances_to_semifinal_after_4_qf_results():
    tm = _8player()
    for winner in [0, 2, 4, 6]:
        tm.record_result(winner)
    assert tm.round_idx == 1


def test_8player_sf_match0_uses_qf_winners():
    tm = _8player()
    for winner in [0, 2, 4, 6]:
        tm.record_result(winner)
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 2


def test_8player_complete_tournament_champion():
    tm = _8player()
    for winner in [0, 2, 4, 6]:   # QF: P1,P3,P5,P7 win
        tm.record_result(winner)
    tm.record_result(0)            # SF: P1 wins
    tm.record_result(4)            # SF: P5 wins
    tm.record_result(0)            # Final: P1 wins
    assert tm.is_complete() is True
    assert tm.champion().label == "P1"


# ── CPU slot ──────────────────────────────────────────────────────────────────

def test_cpu_slot_in_bracket():
    tm = TournamentManager([_human("P1"), _cpu("HARD"), _human("P2"), _cpu("INSANE")])
    tm.record_result(0)  # P1 beats CPU-HARD
    tm.record_result(2)  # P2 beats CPU-INSANE
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 2
