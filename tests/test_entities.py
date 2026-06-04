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


from src.entities import Ball
from src.constants import BALL_TRAIL_LENGTH, BALL_SPEED_INITIAL, BALL_SPEED_MAX_MULTIPLIER


def test_ball_starts_at_center():
    b = Ball()
    assert abs(b.pos.x - SCREEN_W / 2) < 1
    assert abs(b.pos.y - SCREEN_H / 2) < 1


def test_ball_trail_does_not_exceed_max_length():
    b = Ball()
    for _ in range(20):
        b.update(1 / 60)
    assert len(b.trail_positions) <= BALL_TRAIL_LENGTH


def test_ball_bounces_wall():
    b = Ball()
    b.vel = pygame.Vector2(400, -400)
    b.bounce_wall()
    assert b.vel.y > 0


def test_ball_reset_clears_trail_and_returns_to_center():
    b = Ball()
    for _ in range(10):
        b.update(1 / 60)
    b.reset()
    assert len(b.trail_positions) == 0
    assert abs(b.pos.x - SCREEN_W / 2) < 1
    assert abs(b.pos.y - SCREEN_H / 2) < 1
    assert b.rally_hits == 0


def test_ball_bounce_paddle_upward_on_top_hit():
    b = Ball()
    b.pos = pygame.Vector2(200, 200)
    b.vel = pygame.Vector2(-400, 0)
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.pos.y = 300
    p.rect.centery = 300
    # Hit near top of paddle — relative_y should be negative
    b.pos.y = p.pos.y - p.height * 0.4
    b.bounce_paddle(p)
    assert b.vel.y < 0  # going upward
    assert b.vel.x > 0  # reversed direction


def test_ball_bounce_paddle_downward_on_bottom_hit():
    b = Ball()
    b.vel = pygame.Vector2(-400, 0)
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.pos.y = 300
    p.rect.centery = 300
    b.pos.y = p.pos.y + p.height * 0.4
    b.bounce_paddle(p)
    assert b.vel.y > 0  # going downward
    assert b.vel.x > 0


def test_ball_speed_increases_per_hit():
    b = Ball()
    b.vel = pygame.Vector2(-400, 0)
    initial_speed = b.vel.length()
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.pos.y = SCREEN_H / 2
    p.rect.centery = int(SCREEN_H / 2)
    b.pos.y = SCREEN_H / 2
    b.bounce_paddle(p)
    assert b.vel.length() > initial_speed


def test_ball_speed_capped_at_max():
    b = Ball()
    p = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p.pos.y = SCREEN_H / 2
    p.rect.centery = int(SCREEN_H / 2)
    b.pos.y = SCREEN_H / 2
    # Simulate many hits
    for _ in range(100):
        b.vel.x = -abs(b.vel.x)
        b.bounce_paddle(p)
    max_speed = BALL_SPEED_INITIAL * BALL_SPEED_MAX_MULTIPLIER
    assert b.vel.length() <= max_speed * 1.01  # small float tolerance


def test_ball_records_last_touch_player():
    b = Ball()
    b.vel = pygame.Vector2(-400, 0)
    p1 = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
    p1.pos.y = SCREEN_H / 2
    p1.rect.centery = int(SCREEN_H / 2)
    b.pos.y = SCREEN_H / 2
    b.bounce_paddle(p1)
    assert b.last_touch == 1


from src.entities import PowerUp, PowerUpType
from src.constants import POWERUP_SIZE, HUD_HEIGHT


def test_powerup_collected_when_ball_overlaps():
    pu = PowerUp()
    pu.pos = pygame.Vector2(640, 360)
    pu.rect.center = (640, 360)
    b = Ball()
    b.pos = pygame.Vector2(640, 360)
    b.rect.center = (640, 360)
    assert pu.check_collection(b) is True
    assert pu.collected is True


def test_powerup_not_collected_when_ball_far():
    pu = PowerUp()
    pu.pos = pygame.Vector2(640, 360)
    pu.rect.center = (640, 360)
    b = Ball()
    b.pos = pygame.Vector2(100, 100)
    b.rect.center = (100, 100)
    assert pu.check_collection(b) is False
    assert pu.collected is False


def test_powerup_type_is_valid():
    for _ in range(20):
        pu = PowerUp()
        assert pu.type in PowerUpType.ALL


def test_powerup_spawns_in_midfield():
    for _ in range(20):
        pu = PowerUp()
        assert SCREEN_W // 4 <= pu.pos.x <= 3 * SCREEN_W // 4
        assert pu.pos.y > HUD_HEIGHT


def test_powerup_pulse_increases_over_time():
    pu = PowerUp()
    t0 = pu.pulse_t
    pu.update(0.1)
    assert pu.pulse_t > t0
