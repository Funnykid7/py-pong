import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, HUD_HEIGHT, PADDLE_W, PADDLE_H,
    PADDLE_SPEED, PADDLE_MARGIN, POWERUP_DURATION
)
from src.entities import Paddle


def test_paddle_clamps_to_top_bound():
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.pos.y = HUD_HEIGHT  # too high
    p.vel.y = -PADDLE_SPEED
    p.update(1.0)
    assert p.pos.y >= HUD_HEIGHT + PADDLE_H // 2


def test_paddle_clamps_to_bottom_bound():
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.pos.y = SCREEN_H  # too low
    p.vel.y = PADDLE_SPEED
    p.update(1.0)
    assert p.pos.y <= SCREEN_H - PADDLE_H // 2


def test_paddle_rect_follows_pos():
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.vel.y = PADDLE_SPEED
    p.update(0.1)
    assert p.rect.centery == int(p.pos.y)
    assert p.rect.centerx == int(p.pos.x)


def test_paddle_powerup_deactivates_after_duration():
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.activate_powerup("BIG_PADDLE")
    assert p.active_powerup == "BIG_PADDLE"
    p.update(POWERUP_DURATION + 0.1)
    assert p.active_powerup is None
    assert p.height == PADDLE_H


def test_big_paddle_increases_height():
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.activate_powerup("BIG_PADDLE")
    assert p.height > PADDLE_H


def test_small_opponent_decreases_height():
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 2)
    p.activate_powerup("SMALL_OPPONENT")
    assert p.height < PADDLE_H
    p.update(POWERUP_DURATION + 0.1)
    assert p.height == PADDLE_H


def test_paddle_player_colors():
    p1 = Paddle(50, 1)
    p2 = Paddle(SCREEN_W - 50, 2)
    from src.constants import P1_COLOR, P2_COLOR
    assert p1.color == P1_COLOR
    assert p2.color == P2_COLOR
