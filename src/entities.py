import math
import random
import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, HUD_HEIGHT, PADDLE_W, PADDLE_H,
    PADDLE_SPEED, PADDLE_MARGIN, POWERUP_DURATION,
    BALL_SIZE, BALL_SPEED_INITIAL, BALL_SPEED_MAX_MULTIPLIER,
    BALL_SPEED_INCREMENT, BALL_TRAIL_LENGTH, POWERUP_SIZE,
    P1_COLOR, P2_COLOR,
)


class Paddle:
    def __init__(self, x: float, player: int):
        self.player = player
        self.color = P1_COLOR if player == 1 else P2_COLOR
        self.pos = pygame.Vector2(x, SCREEN_H / 2)
        self.vel = pygame.Vector2(0, 0)
        self.height = PADDLE_H
        self.rect = pygame.Rect(0, 0, PADDLE_W, self.height)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.score = 0
        self.sets_won = 0
        self.active_powerup: str | None = None
        self.powerup_timer = 0.0

    def update(self, dt: float):
        self.pos.y += self.vel.y * dt
        half_h = self.height / 2
        self.pos.y = max(HUD_HEIGHT + half_h, min(SCREEN_H - half_h, self.pos.y))
        self.rect.h = self.height
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.active_powerup:
            self.powerup_timer -= dt
            if self.powerup_timer <= 0:
                self.deactivate_powerup()

    def activate_powerup(self, powerup_type: str):
        self.active_powerup = powerup_type
        self.powerup_timer = POWERUP_DURATION
        if powerup_type == "BIG_PADDLE":
            self.height = int(PADDLE_H * 1.5)
        elif powerup_type == "SMALL_OPPONENT":
            self.height = int(PADDLE_H * 0.6)

    def deactivate_powerup(self):
        if self.active_powerup in ("BIG_PADDLE", "SMALL_OPPONENT"):
            self.height = PADDLE_H
        self.active_powerup = None
        self.powerup_timer = 0.0


class Ball:
    def __init__(self):
        self.pos = pygame.Vector2(SCREEN_W / 2, SCREEN_H / 2)
        self.base_speed = float(BALL_SPEED_INITIAL)
        angle = random.choice([-30, -15, 0, 15, 30])
        direction = random.choice([-1, 1])
        rad = math.radians(angle)
        self.vel = pygame.Vector2(
            direction * self.base_speed * math.cos(rad),
            self.base_speed * math.sin(rad),
        )
        self.rally_hits = 0
        self.spin = 0.0
        self.trail_positions: list[pygame.Vector2] = []
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.last_touch: int = 0

    def update(self, dt: float):
        self.trail_positions.append(pygame.Vector2(self.pos))
        if len(self.trail_positions) > BALL_TRAIL_LENGTH:
            self.trail_positions.pop(0)
        self.vel.y += self.spin * dt
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def bounce_wall(self):
        self.vel.y *= -1

    def bounce_paddle(self, paddle: "Paddle"):
        relative_y = (self.pos.y - paddle.pos.y) / (paddle.height / 2)
        relative_y = max(-1.0, min(1.0, relative_y))
        bounce_angle = relative_y * 75
        self.rally_hits += 1
        speed_mult = min(
            1.0 + self.rally_hits * BALL_SPEED_INCREMENT,
            BALL_SPEED_MAX_MULTIPLIER,
        )
        new_speed = self.base_speed * speed_mult
        rad = math.radians(bounce_angle)
        direction = 1 if self.vel.x < 0 else -1
        self.vel.x = direction * new_speed * math.cos(rad)
        self.vel.y = new_speed * math.sin(rad)
        self.spin = relative_y * 50
        self.last_touch = paddle.player

    def reset(self):
        self.pos = pygame.Vector2(SCREEN_W / 2, SCREEN_H / 2)
        self.trail_positions.clear()
        self.rally_hits = 0
        self.spin = 0.0
        angle = random.choice([-30, -15, 0, 15, 30])
        direction = random.choice([-1, 1])
        rad = math.radians(angle)
        self.vel = pygame.Vector2(
            direction * self.base_speed * math.cos(rad),
            self.base_speed * math.sin(rad),
        )
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    @property
    def current_speed(self) -> float:
        return self.vel.length()


class PowerUpType:
    SPEED_BOOST = "SPEED_BOOST"
    SLOW_BALL = "SLOW_BALL"
    BIG_PADDLE = "BIG_PADDLE"
    SMALL_OPPONENT = "SMALL_OPPONENT"
    MULTI_BALL = "MULTI_BALL"
    ALL = ["SPEED_BOOST", "SLOW_BALL", "BIG_PADDLE", "SMALL_OPPONENT", "MULTI_BALL"]


class PowerUp:
    def __init__(self):
        margin = 100
        self.pos = pygame.Vector2(
            random.randint(SCREEN_W // 4, 3 * SCREEN_W // 4),
            random.randint(HUD_HEIGHT + margin, SCREEN_H - margin),
        )
        self.type: str = random.choice(PowerUpType.ALL)
        self.rect = pygame.Rect(0, 0, POWERUP_SIZE, POWERUP_SIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.pulse_t = 0.0
        self.collected = False

    def update(self, dt: float):
        self.pulse_t += dt

    def check_collection(self, ball: "Ball") -> bool:
        if self.rect.colliderect(ball.rect):
            self.collected = True
            return True
        return False
