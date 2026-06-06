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


from src.effects import TransitionManager


def test_transition_not_blocking_at_start():
    tm = TransitionManager()
    assert not tm.blocking


def test_transition_blocking_after_start():
    tm = TransitionManager()
    tm.start(lambda: None)
    assert tm.blocking


def test_transition_callback_fires_at_end_of_fade_out():
    fired = []
    tm = TransitionManager()
    tm.start(lambda: fired.append(1), duration=0.25)
    tm.update(0.30)
    assert fired == [1]


def test_transition_still_blocking_during_fade_in():
    tm = TransitionManager()
    tm.start(lambda: None, duration=0.1)
    tm.update(0.15)  # fade_out completes, fade_in begins
    assert tm.blocking


def test_transition_idle_after_full_cycle():
    tm = TransitionManager()
    tm.start(lambda: None, duration=0.1)
    tm.update(0.15)  # fade_out → fade_in
    tm.update(0.15)  # fade_in → idle
    assert not tm.blocking


def test_transition_second_start_ignored_while_active():
    fired = []
    tm = TransitionManager()
    tm.start(lambda: fired.append(1), duration=0.5)
    tm.start(lambda: fired.append(2), duration=0.1)  # must be ignored
    tm.update(0.6)
    assert fired == [1]


def test_transition_draw_noop_when_idle():
    surf = pygame.Surface((100, 100))
    surf.fill((255, 0, 0))
    tm = TransitionManager()
    tm.draw(surf)
    assert surf.get_at((50, 50))[:3] == (255, 0, 0)


def test_transition_draw_darkens_surface_during_fade_out():
    surf = pygame.Surface((100, 100))
    surf.fill((255, 255, 255))
    tm = TransitionManager()
    tm.start(lambda: None, duration=1.0)
    tm.update(0.5)  # progress 0.5 → overlay alpha 127
    tm.draw(surf)
    r = surf.get_at((50, 50))[0]
    assert r < 200  # white significantly darkened by black overlay
