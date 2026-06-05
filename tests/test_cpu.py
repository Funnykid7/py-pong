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
