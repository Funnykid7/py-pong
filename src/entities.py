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
