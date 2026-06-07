import pygame
from src.constants import (
    SCREEN_W, SCREEN_H,
    MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED,
    CLASSIC_WIN_SCORE, SET_WIN_SCORE,
    SUDDEN_DEATH_DURATION,
    STATE_PLAYING, STATE_GAME_OVER,
    OPPONENT_HUMAN,
)
from src.game import Game


def make_game(mode=MODE_FIRST_TO_11):
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    g = Game(screen)
    g.game_mode = mode
    g.state = STATE_PLAYING
    g.countdown = 0
    return g


def test_first_to_11_p1_wins_at_11():
    g = make_game(MODE_FIRST_TO_11)
    g.p1.score = CLASSIC_WIN_SCORE - 1
    ball = g.balls[0]
    g._score(1, ball)
    assert g.state == STATE_GAME_OVER
    assert g.winner == 1


def test_first_to_11_p2_wins_at_11():
    g = make_game(MODE_FIRST_TO_11)
    g.p2.score = CLASSIC_WIN_SCORE - 1
    ball = g.balls[0]
    g._score(2, ball)
    assert g.state == STATE_GAME_OVER
    assert g.winner == 2


def test_first_to_11_no_win_before_11():
    g = make_game(MODE_FIRST_TO_11)
    g.p1.score = CLASSIC_WIN_SCORE - 2
    ball = g.balls[0]
    g._score(1, ball)
    assert g.state == STATE_PLAYING
    assert g.p1.score == CLASSIC_WIN_SCORE - 1


def test_best_of_3_set_win_increments_sets():
    g = make_game(MODE_BEST_OF_3)
    g.p1.score = SET_WIN_SCORE - 1
    ball = g.balls[0]
    g._score(1, ball)
    assert g.p1.sets_won == 1
    assert g.p1.score == 0
    assert g.p2.score == 0


def test_best_of_3_match_win_at_2_sets():
    g = make_game(MODE_BEST_OF_3)
    g.p1.sets_won = 1
    g.p1.score = SET_WIN_SCORE - 1
    ball = g.balls[0]
    g._score(1, ball)
    assert g.state == STATE_GAME_OVER
    assert g.winner == 1


def test_timed_winner_by_score_when_not_tied():
    g = make_game(MODE_TIMED)
    g.p1.score = 7
    g.p2.score = 5
    g.time_left = 0.001
    g._update_playing(0.01)
    assert g.state == STATE_GAME_OVER
    assert g.winner == 1


def test_timed_sudden_death_when_tied():
    g = make_game(MODE_TIMED)
    g.p1.score = 5
    g.p2.score = 5
    g.time_left = 0.001
    g._update_playing(0.01)
    assert g.sudden_death is True
    assert abs(g.time_left - SUDDEN_DEATH_DURATION) < 1.0


def test_multi_ball_removes_extra_ball_on_score():
    from src.entities import Ball
    g = make_game()
    extra = Ball()
    g.balls.append(extra)
    assert len(g.balls) == 2
    g._score(1, extra)
    assert len(g.balls) == 1


def test_score_resets_rally_count():
    g = make_game()
    g.rally_count = 7
    ball = g.balls[0]
    g._score(1, ball)
    assert g.rally_count == 0


from src.constants import SMASH_BASE_CHARGE_RATE, SMASH_PER_POINT_CHARGE
from src.constants import PADDLE_H


def test_smash_meter_charges_at_base_rate_when_tied():
    g = make_game()
    g.p1.score = 3
    g.p2.score = 3
    g._update_smash_meters(1.0)
    assert abs(g.p1_smash_meter - SMASH_BASE_CHARGE_RATE) < 0.001


def test_smash_meter_charges_faster_when_behind():
    g = make_game()
    g.p1.score = 2
    g.p2.score = 5  # p1 is 3 points behind
    g._update_smash_meters(1.0)
    expected = SMASH_BASE_CHARGE_RATE + 3 * SMASH_PER_POINT_CHARGE
    assert abs(g.p1_smash_meter - expected) < 0.001


def test_smash_meter_charges_at_base_when_ahead():
    g = make_game()
    g.p1.score = 5
    g.p2.score = 2  # p1 is ahead — gap = 0
    g._update_smash_meters(1.0)
    assert abs(g.p1_smash_meter - SMASH_BASE_CHARGE_RATE) < 0.001


def test_smash_meter_caps_at_one():
    g = make_game()
    g.p1_smash_meter = 0.95
    g.p1.score = 0
    g.p2.score = 10
    g._update_smash_meters(5.0)
    assert g.p1_smash_meter <= 1.0


def test_smash_ready_flag_set_when_meter_reaches_one():
    g = make_game()
    g.p1_smash_meter = 0.99
    g.p1.score = 0
    g.p2.score = 5
    g._update_smash_meters(1.0)
    assert g.p1_smash_ready is True


def test_activate_smash_p1_big_paddle_p2_shrinks():
    g = make_game()
    g.p1_smash_ready = True
    g.p1_smash_meter = 1.0
    g._activate_smash(1)
    assert g.p1.height > PADDLE_H
    assert g.p1.active_powerup == "BIG_PADDLE"
    assert g.p2.height < PADDLE_H
    assert g.p2.active_powerup == "SMALL_OPPONENT"


def test_activate_smash_p2_big_paddle_p1_shrinks():
    g = make_game()
    g.p2_smash_ready = True
    g.p2_smash_meter = 1.0
    g._activate_smash(2)
    assert g.p2.height > PADDLE_H
    assert g.p2.active_powerup == "BIG_PADDLE"
    assert g.p1.height < PADDLE_H
    assert g.p1.active_powerup == "SMALL_OPPONENT"


def test_activate_smash_resets_meter_and_flag():
    g = make_game()
    g.p1_smash_ready = True
    g.p1_smash_meter = 1.0
    g._activate_smash(1)
    assert g.p1_smash_meter == 0.0
    assert g.p1_smash_ready is False


def test_activate_smash_does_nothing_when_not_ready():
    g = make_game()
    g.p1_smash_ready = False
    g.p1_smash_meter = 0.5
    g._activate_smash(1)
    assert g.p1.height == PADDLE_H
    assert g.p1.active_powerup is None


def test_smash_meters_reset_on_new_match():
    g = make_game()
    g.p1_smash_meter = 0.8
    g.p2_smash_meter = 0.6
    g.p1_smash_ready = True
    g._start_match()
    assert g.p1_smash_meter == 0.0
    assert g.p2_smash_meter == 0.0
    assert g.p1_smash_ready is False


def test_smash_meters_reset_on_set_win():
    g = make_game(MODE_BEST_OF_3)
    g.p1_smash_meter = 0.9
    g.p2_smash_meter = 0.7
    g.p1.score = SET_WIN_SCORE - 1
    ball = g.balls[0]
    g._score(1, ball)  # triggers _check_set_win
    assert g.p1_smash_meter == 0.0
    assert g.p2_smash_meter == 0.0
    assert g.p1_smash_ready is False
    assert g.p2_smash_ready is False


from src.cpu import CPUController
from src.constants import OPPONENT_CPU, SMASH_BASE_CHARGE_RATE


def _make_cpu_game(difficulty):
    g = make_game()
    g.opponent_type = OPPONENT_CPU
    g.cpu_difficulty = difficulty
    g.cpu = CPUController(difficulty)
    return g


def test_cpu_p2_meter_does_not_charge_on_easy():
    g = _make_cpu_game("EASY")
    g._update_smash_meters(5.0)
    assert g.p2_smash_meter == 0.0


def test_cpu_p2_meter_does_not_charge_on_medium():
    g = _make_cpu_game("MEDIUM")
    g._update_smash_meters(5.0)
    assert g.p2_smash_meter == 0.0


def test_cpu_p2_meter_charges_on_hard():
    g = _make_cpu_game("HARD")
    g._update_smash_meters(1.0)
    assert g.p2_smash_meter > 0.0


def test_cpu_p2_meter_charges_on_insane():
    g = _make_cpu_game("INSANE")
    g._update_smash_meters(1.0)
    assert g.p2_smash_meter > 0.0


def test_hard_cpu_fires_smash_in_update_playing():
    """_update_playing calls _activate_smash(2) when HARD CPU meter is ready."""
    g = _make_cpu_game("HARD")
    g.p2_smash_meter = 1.0
    g.p2_smash_ready = True
    g._update_playing(0.016)
    assert g.p2_smash_meter == 0.0
    assert g.p2_smash_ready is False


def test_insane_cpu_withholds_smash_when_ball_moving_away():
    """INSANE CPU does not fire when ball.vel.x < 0, even with meter ready."""
    g = _make_cpu_game("INSANE")
    g.p2_smash_meter = 1.0
    g.p2_smash_ready = True
    g.balls[0].vel.x = -400  # ball moving away from CPU
    g._update_playing(0.016)
    assert g.p2_smash_ready is True  # meter was NOT consumed


# ── Tournament integration ────────────────────────────────────────────────────

from src.tournament import TournamentManager, Slot as TSlot
from src.constants import STATE_BRACKET


def _make_4p_tournament():
    slots = [
        TSlot("P1", False, "EASY"), TSlot("P2", False, "EASY"),
        TSlot("P3", False, "EASY"), TSlot("P4", False, "EASY"),
    ]
    return TournamentManager(slots)


def test_end_match_transitions_to_bracket_when_tournament_active():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._tournament_match_slots = (0, 1)
    g._end_match(winner=1)
    assert g.state == STATE_BRACKET
    assert g.tournament.rounds[0][0].winner == 0


def test_end_match_records_correct_winner_slot_player1():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._tournament_match_slots = (0, 1)
    g._end_match(winner=1)         # game player 1 → slot index 0
    assert g.tournament.rounds[0][0].winner == 0


def test_end_match_records_correct_winner_slot_player2():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._tournament_match_slots = (0, 1)
    g._end_match(winner=2)         # game player 2 → slot index 1
    assert g.tournament.rounds[0][0].winner == 1


def test_end_match_without_tournament_goes_to_game_over():
    g = make_game()
    g.tournament = None
    g._end_match(winner=1)
    assert g.state == STATE_GAME_OVER


def test_setup_tournament_match_human_vs_human():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._setup_tournament_match()
    assert g.opponent_type == OPPONENT_HUMAN
    assert g._tournament_match_slots == (0, 1)


def test_setup_tournament_match_cpu_slot_b():
    from src.constants import OPPONENT_CPU
    slots = [
        TSlot("P1", False, "EASY"), TSlot("CPU-HARD", True, "HARD"),
        TSlot("P2", False, "EASY"), TSlot("P3", False, "EASY"),
    ]
    g = make_game()
    g.tournament = TournamentManager(slots)
    g._setup_tournament_match()    # match is slot 0 (human) vs slot 1 (CPU)
    assert g.opponent_type == OPPONENT_CPU
    assert g.cpu_difficulty == "HARD"
    assert g._tournament_match_slots == (0, 1)


def test_setup_tournament_match_cpu_slot_a_swaps_to_right():
    from src.constants import OPPONENT_CPU
    slots = [
        TSlot("CPU-EASY", True, "EASY"), TSlot("P1", False, "EASY"),
        TSlot("P2", False, "EASY"), TSlot("P3", False, "EASY"),
    ]
    g = make_game()
    g.tournament = TournamentManager(slots)
    g._setup_tournament_match()    # match is slot 0 (CPU) vs slot 1 (human) → must swap
    assert g.opponent_type == OPPONENT_CPU
    assert g._tournament_match_slots == (1, 0)  # human is now slot_a (left)
