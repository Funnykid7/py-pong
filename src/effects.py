import math
import random
import pygame
from src.constants import (
    SHAKE_MAX_OFFSET, SHAKE_DECAY,
    PARTICLE_COUNT_SCORE, PARTICLE_LIFETIME_MIN, PARTICLE_LIFETIME_MAX,
    HUD_HEIGHT, SCREEN_H,
)


class ScreenShake:
    def __init__(self):
        self.trauma = 0.0

    def add_trauma(self, amount: float):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt: float):
        self.trauma = max(0.0, self.trauma * (SHAKE_DECAY ** (dt * 60)))

    def get_offset(self) -> pygame.Vector2:
        if self.trauma <= 0:
            return pygame.Vector2(0, 0)
        shake = self.trauma ** 2 * SHAKE_MAX_OFFSET
        return pygame.Vector2(
            random.uniform(-shake, shake),
            random.uniform(-shake, shake),
        )


class Particle:
    def __init__(self, pos: pygame.Vector2, color: tuple):
        self.pos = pygame.Vector2(pos)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(100, 400)
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.color = color
        self.lifetime = random.uniform(PARTICLE_LIFETIME_MIN, PARTICLE_LIFETIME_MAX)
        self.max_lifetime = self.lifetime
        self.radius = random.randint(2, 5)

    def update(self, dt: float) -> bool:
        self.pos += self.vel * dt
        self.vel *= 0.95
        self.lifetime -= dt
        return self.lifetime > 0

    @property
    def alpha(self) -> int:
        return max(0, int(255 * (self.lifetime / self.max_lifetime)))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def emit_score(self, x: float, color: tuple):
        for _ in range(PARTICLE_COUNT_SCORE):
            pos = pygame.Vector2(x, random.uniform(HUD_HEIGHT, SCREEN_H))
            self.particles.append(Particle(pos, color))

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]

    def clear(self):
        self.particles.clear()


class TransitionManager:
    def __init__(self):
        self._state = "idle"   # "idle" | "fade_out" | "fade_in"
        self._progress = 0.0
        self._duration = 0.25
        self._callback = None
        self._overlay = None   # allocated lazily on first draw()

    def start(self, callback, duration: float = 0.25):
        if self._state != "idle":
            return
        if duration <= 0:
            duration = 0.25
        self._callback = callback
        self._duration = duration
        self._progress = 0.0
        self._state = "fade_out"

    def update(self, dt: float):
        if self._state == "idle":
            return
        self._progress += dt / self._duration
        if self._progress >= 1.0:
            if self._state == "fade_out":
                cb, self._callback = self._callback, None
                self._state = "fade_in"
                self._progress = 0.0
                if cb:
                    cb()
            elif self._state == "fade_in":
                self._state = "idle"
                self._progress = 0.0

    def draw(self, surf: pygame.Surface):
        if self._state == "idle":
            return
        if self._overlay is None or self._overlay.get_size() != surf.get_size():
            self._overlay = pygame.Surface(surf.get_size())
            self._overlay.fill((0, 0, 0))
        if self._state == "fade_out":
            alpha = int(255 * min(1.0, self._progress))
        else:
            alpha = int(255 * max(0.0, 1.0 - self._progress))
        self._overlay.set_alpha(max(0, min(255, alpha)))
        surf.blit(self._overlay, (0, 0))

    @property
    def blocking(self) -> bool:
        return self._state != "idle"
