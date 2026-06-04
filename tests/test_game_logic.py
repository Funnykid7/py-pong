import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, PADDLE_H,
    MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED,
    CLASSIC_WIN_SCORE, SET_WIN_SCORE,
    SUDDEN_DEATH_DURATION,
    STATE_PLAYING, STATE_GAME_OVER,
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


from src.entities import PowerUp, PowerUpType


def make_powerup(ptype: str) -> PowerUp:
    pu = PowerUp()
    pu.type = ptype
    return pu


def test_speed_boost_increases_ball_speed():
    g = make_game()
    ball = g.balls[0]
    ball.last_touch = 1
    initial_speed = ball.vel.length()
    g._activate_powerup(make_powerup(PowerUpType.SPEED_BOOST), ball)
    assert ball.vel.length() > initial_speed * 1.4


def test_slow_ball_decreases_ball_speed():
    g = make_game()
    ball = g.balls[0]
    ball.last_touch = 1
    initial_speed = ball.vel.length()
    g._activate_powerup(make_powerup(PowerUpType.SLOW_BALL), ball)
    assert ball.vel.length() < initial_speed * 0.7


def test_big_paddle_increases_beneficiary_height():
    g = make_game()
    ball = g.balls[0]
    ball.last_touch = 1
    g._activate_powerup(make_powerup(PowerUpType.BIG_PADDLE), ball)
    assert g.p1.height > PADDLE_H
    assert g.p1.active_powerup == PowerUpType.BIG_PADDLE


def test_small_opponent_shrinks_opponent():
    g = make_game()
    ball = g.balls[0]
    ball.last_touch = 1  # P1 benefits, P2 shrinks
    g._activate_powerup(make_powerup(PowerUpType.SMALL_OPPONENT), ball)
    assert g.p2.height < PADDLE_H
    assert g.p2.active_powerup == PowerUpType.SMALL_OPPONENT


def test_multi_ball_adds_second_ball():
    g = make_game()
    ball = g.balls[0]
    ball.last_touch = 2
    assert len(g.balls) == 1
    g._activate_powerup(make_powerup(PowerUpType.MULTI_BALL), ball)
    assert len(g.balls) == 2


def test_powerup_beneficiary_is_last_touch_player():
    g = make_game()
    ball = g.balls[0]
    ball.last_touch = 2
    g._activate_powerup(make_powerup(PowerUpType.BIG_PADDLE), ball)
    assert g.p2.height > PADDLE_H
    assert g.p1.height == PADDLE_H
