import pygame
from src.constants import SCREEN_H, HUD_HEIGHT, CPU_PARAMS
from src.entities import Ball, Paddle


class CPUController:
    def __init__(self, difficulty: str):
        params = CPU_PARAMS[difficulty]
        self.max_speed: float = params["max_speed"]
        self.reaction_delay: float = params["reaction_delay"]
        self.dead_zone: float = params["dead_zone"]
        self._reaction_timer: float = self.reaction_delay
        self._target_y: float = (SCREEN_H + HUD_HEIGHT) / 2.0

    def update(self, dt: float, ball: Ball, paddle: Paddle) -> None:
        center_y = (SCREEN_H + HUD_HEIGHT) / 2.0
        if ball.vel.x > 0:
            self._reaction_timer -= dt
            if self._reaction_timer <= 0:
                self._target_y = ball.pos.y
                self._reaction_timer = self.reaction_delay
        else:
            self._target_y = center_y
            self._reaction_timer = self.reaction_delay

        diff = self._target_y - paddle.pos.y
        if abs(diff) <= self.dead_zone:
            paddle.vel.y = 0.0
        elif diff < 0:
            paddle.vel.y = -self.max_speed
        else:
            paddle.vel.y = self.max_speed
