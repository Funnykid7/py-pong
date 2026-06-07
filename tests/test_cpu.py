import pytest
import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, HUD_HEIGHT,
    PADDLE_W, PADDLE_MARGIN,
)
from src.entities import Paddle, Ball
from src.cpu import CPUController


CENTER_Y = (SCREEN_H + HUD_HEIGHT) / 2


def _make_paddle():
    return Paddle(SCREEN_W - PADDLE_MARGIN - PADDLE_W // 2, 2)


def test_cpu_drifts_to_center_when_ball_moves_away():
    """When ball moves away (vel.x < 0), CPU target becomes screen center."""
    ball = Ball()
    ball.vel.x = -400
    paddle = _make_paddle()
    cpu = CPUController("MEDIUM")
    cpu.update(0.1, ball, paddle)
    assert cpu._target_y == CENTER_Y


def test_cpu_reaction_delay_blocks_immediate_target_update():
    """CPU does not update target_y until reaction_delay seconds have elapsed."""
    ball = Ball()
    ball.vel.x = 400
    ball.pos.y = 200.0
    paddle = _make_paddle()
    cpu = CPUController("MEDIUM")  # reaction_delay = 0.18s
    # Advance less than reaction delay — target must not update
    cpu.update(0.05, ball, paddle)
    assert cpu._target_y == CENTER_Y


def test_cpu_updates_target_after_full_reaction_delay():
    """After reaction_delay seconds elapse, target_y snaps to ball position."""
    ball = Ball()
    ball.vel.x = 400
    ball.pos.y = 200.0
    paddle = _make_paddle()
    cpu = CPUController("MEDIUM")  # reaction_delay = 0.18s
    # Advance past the full delay in one step
    cpu.update(0.20, ball, paddle)
    assert cpu._target_y == ball.pos.y


def test_cpu_speed_capped_per_difficulty():
    """Paddle velocity never exceeds max_speed for the chosen difficulty."""
    ball = Ball()
    ball.vel.x = 400
    paddle = _make_paddle()
    paddle.pos.y = SCREEN_H - 10   # paddle near bottom
    cpu = CPUController("EASY")    # max_speed = 180
    cpu._target_y = HUD_HEIGHT     # target near top — maximum chase
    cpu._reaction_timer = -1       # force past delay
    cpu.update(0.1, ball, paddle)
    assert abs(paddle.vel.y) <= cpu.max_speed


def test_cpu_dead_zone_stops_paddle():
    """Paddle stops moving when already within dead_zone pixels of target."""
    ball = Ball()
    ball.vel.x = 400
    paddle = _make_paddle()
    cpu = CPUController("EASY")    # dead_zone = 20
    cpu._target_y = paddle.pos.y + 5   # 5px off — inside 20px dead zone
    cpu._reaction_timer = -1
    cpu.update(0.1, ball, paddle)
    assert paddle.vel.y == 0


def test_insane_reacts_instantly():
    """INSANE difficulty has reaction_delay = 0, so target updates every frame."""
    ball = Ball()
    ball.vel.x = 400
    ball.pos.y = 100.0
    paddle = _make_paddle()
    cpu = CPUController("INSANE")  # reaction_delay = 0.0
    cpu.update(0.016, ball, paddle)
    assert cpu._target_y == ball.pos.y


def _make_player_paddle():
    return Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)


def _make_ball_incoming():
    """Ball moving right — toward CPU (P2 on the right)."""
    b = Ball()
    b.vel.x = 400
    return b


def _make_ball_retreating():
    """Ball moving left — away from CPU."""
    b = Ball()
    b.vel.x = -400
    return b


def test_smash_disabled_for_easy():
    cpu = CPUController("EASY")
    assert cpu.smash_enabled is False


def test_smash_disabled_for_medium():
    cpu = CPUController("MEDIUM")
    assert cpu.smash_enabled is False


def test_smash_enabled_for_hard():
    cpu = CPUController("HARD")
    assert cpu.smash_enabled is True


def test_smash_enabled_for_insane():
    cpu = CPUController("INSANE")
    assert cpu.smash_enabled is True


def test_should_smash_returns_false_when_meter_not_ready():
    cpu = CPUController("HARD")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    assert cpu.should_smash(ball, player, meter_ready=False) is False


def test_should_smash_returns_false_for_disabled_difficulty():
    cpu = CPUController("EASY")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    assert cpu.should_smash(ball, player, meter_ready=True) is False


def test_hard_fires_immediately_when_ready():
    cpu = CPUController("HARD")
    ball = _make_ball_retreating()   # direction does not matter for HARD
    player = _make_player_paddle()
    player.pos.y = CENTER_Y          # player perfectly centered — still fires
    assert cpu.should_smash(ball, player, meter_ready=True) is True


def test_insane_fires_when_ball_incoming_and_player_off_center():
    cpu = CPUController("INSANE")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    player.pos.y = CENTER_Y + 120    # well off-center (>80 px)
    assert cpu.should_smash(ball, player, meter_ready=True) is True


def test_insane_withholds_when_ball_moving_away():
    cpu = CPUController("INSANE")
    ball = _make_ball_retreating()
    player = _make_player_paddle()
    player.pos.y = CENTER_Y + 120    # off-center but ball retreating
    assert cpu.should_smash(ball, player, meter_ready=True) is False


def test_insane_withholds_when_player_is_centered():
    cpu = CPUController("INSANE")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    player.pos.y = CENTER_Y + 20     # within 80 px — considered centered
    assert cpu.should_smash(ball, player, meter_ready=True) is False
