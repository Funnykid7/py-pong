import pygame
from src.constants import (
    SHAKE_MAX_OFFSET, SHAKE_DECAY, PARTICLE_COUNT_SCORE,
    PARTICLE_LIFETIME_MIN, PARTICLE_LIFETIME_MAX,
)
from src.effects import ScreenShake, ParticleSystem


def test_shake_trauma_decays_each_frame():
    s = ScreenShake()
    s.add_trauma(1.0)
    before = s.trauma
    s.update(1 / 60)
    assert s.trauma < before


def test_shake_offset_zero_at_zero_trauma():
    s = ScreenShake()
    s.trauma = 0.0
    offset = s.get_offset()
    assert offset.x == 0.0
    assert offset.y == 0.0


def test_shake_offset_nonzero_at_full_trauma():
    s = ScreenShake()
    s.add_trauma(1.0)
    # Run a few samples — at least one should be non-zero
    nonzero = any(
        s.get_offset().length() > 0
        for _ in range(10)
    )
    assert nonzero


def test_shake_trauma_capped_at_one():
    s = ScreenShake()
    s.add_trauma(0.8)
    s.add_trauma(0.8)
    assert s.trauma <= 1.0


def test_particles_emitted_on_score():
    ps = ParticleSystem()
    ps.emit_score(0, (255, 0, 200))
    assert len(ps.particles) == PARTICLE_COUNT_SCORE


def test_particles_culled_after_lifetime():
    ps = ParticleSystem()
    ps.emit_score(0, (255, 0, 200))
    # Advance time past max lifetime
    for _ in range(200):
        ps.update(PARTICLE_LIFETIME_MAX / 10)
    assert len(ps.particles) == 0


def test_particle_alpha_decreases_over_lifetime():
    ps = ParticleSystem()
    ps.emit_score(640, (0, 245, 255))
    p = ps.particles[0]
    alpha_start = p.alpha
    p.update(p.max_lifetime * 0.5)
    assert p.alpha < alpha_start


def test_particle_system_clear():
    ps = ParticleSystem()
    ps.emit_score(640, (255, 230, 0))
    ps.clear()
    assert len(ps.particles) == 0
