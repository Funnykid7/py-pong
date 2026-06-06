# Menu Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add animated menu backgrounds, smooth fade transitions between game states, and hover animations (scale, glow bar, color breathe) for menu items.

**Architecture:** Extend `src/effects.py` with a `TransitionManager` class; add `menu_particles` list and `menu_hover_t` float to `Game`; update `draw_menu`, `draw_difficulty_select`, and `draw_mode_select` in `src/renderer.py` to accept and render both. Wire `TransitionManager` throughout `Game`'s event handlers and draw loop.

**Tech Stack:** Python 3.12, pygame-ce ≥ 2.5.0, pytest

---

## File Map

| File | Change |
|------|--------|
| `src/effects.py` | Add `TransitionManager` class |
| `tests/test_effects.py` | Add tests for `TransitionManager` |
| `src/game.py` | Add `import math`, `import random`; add `self.menu_particles`, `self.menu_hover_t`, `self.transition`; add `_make_menu_particles()`, `_update_menu_particles()`; update `_update()`, `_update_menu()`, all menu event handlers, `_draw()` |
| `src/renderer.py` | Update `draw_menu`, `draw_mode_select`, `draw_difficulty_select` signatures and item-rendering loops |

---

## Task 1: TransitionManager

**Files:**
- Modify: `src/effects.py`
- Modify: `tests/test_effects.py`

- [ ] **Step 1: Append failing tests to tests/test_effects.py**

```python
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
```

- [ ] **Step 2: Run tests — confirm the new tests fail**

```bash
cd /home/aryan/Documents/GitHub/py-pong && python -m pytest tests/test_effects.py -k "transition" -v
```

Expected: `ImportError` — `TransitionManager` not defined yet.

- [ ] **Step 3: Implement TransitionManager — append to src/effects.py**

```python
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
                if self._callback:
                    self._callback()
                    self._callback = None
                self._state = "fade_in"
                self._progress = 0.0
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
        self._overlay.set_alpha(alpha)
        surf.blit(self._overlay, (0, 0))

    @property
    def blocking(self) -> bool:
        return self._state != "idle"
```

- [ ] **Step 4: Run tests — confirm all TransitionManager tests pass**

```bash
cd /home/aryan/Documents/GitHub/py-pong && python -m pytest tests/test_effects.py -v
```

Expected: all tests PASS (existing shake/particle tests unaffected).

- [ ] **Step 5: Commit**

```bash
cd /home/aryan/Documents/GitHub/py-pong && git add src/effects.py tests/test_effects.py && git commit -m "feat: add TransitionManager to effects module"
```

---

## Task 2: Menu Particle Field

**Files:**
- Modify: `src/game.py`
- Modify: `src/renderer.py`

- [ ] **Step 1: Add imports, particle init, and update methods to game.py**

At the top of `src/game.py`, add `import math` and `import random` after `import pygame`:

```python
import pygame
import math
import random
```

In `Game.__init__`, after `self.menu_ball_vel = pygame.Vector2(300, 220)`, add:

```python
        self.menu_particles: list[dict] = self._make_menu_particles()
        self.menu_hover_t: float = 0.0
```

Add these two methods to the `Game` class (place after `_update_menu`):

```python
    def _make_menu_particles(self) -> list[dict]:
        particles = []
        for _ in range(60):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(15, 40)
            particles.append({
                "pos": pygame.Vector2(
                    random.uniform(0, SCREEN_W),
                    random.uniform(0, SCREEN_H),
                ),
                "vel": pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),
                "phase": random.uniform(0, 2 * math.pi),
                "color": random.choice([P1_COLOR, P2_COLOR]),
                "radius": random.randint(2, 4),
            })
        return particles

    def _update_menu_particles(self, dt: float):
        for p in self.menu_particles:
            p["pos"] += p["vel"] * dt
            if p["pos"].x < 0:
                p["pos"].x = SCREEN_W
            elif p["pos"].x > SCREEN_W:
                p["pos"].x = 0
            if p["pos"].y < 0:
                p["pos"].y = SCREEN_H
            elif p["pos"].y > SCREEN_H:
                p["pos"].y = 0
```

- [ ] **Step 2: Call _update_menu_particles from relevant states**

Replace `_update_menu` entirely:

```python
    def _update_menu(self, dt: float):
        self.menu_ball_pos += self.menu_ball_vel * dt
        if self.menu_ball_pos.x < 0 or self.menu_ball_pos.x > SCREEN_W:
            self.menu_ball_vel.x *= -1
        if self.menu_ball_pos.y < 0 or self.menu_ball_pos.y > SCREEN_H:
            self.menu_ball_vel.y *= -1
        self._update_menu_particles(dt)
```

Replace `_update` entirely (STATE_DIFFICULTY and STATE_MODE_SELECT now advance particles; `menu_hover_t` is ticked unconditionally — `transition.update` is wired in Task 4):

```python
    def _update(self, dt: float):
        self.menu_hover_t += dt
        if self.state == STATE_MENU:
            self._update_menu(dt)
        elif self.state in (STATE_DIFFICULTY, STATE_MODE_SELECT):
            self._update_menu_particles(dt)
        elif self.state == STATE_PLAYING:
            self._update_playing(dt)
        elif self.state == STATE_GAME_OVER:
            self.gameover_pulse += dt
            self.particles.update(dt)
```

- [ ] **Step 3: Update renderer draw functions to accept and draw particles**

Replace `draw_menu` in `src/renderer.py`:

```python
def draw_menu(surface, font_title, font_large, font_small, selected: int,
              anim_ball_pos: tuple, menu_particles: list | None = None, hover_t: float = 0.0):
    draw_background(surface)
    if menu_particles:
        for p in menu_particles:
            alpha = max(0, min(255, int(160 + 80 * math.sin(hover_t + p["phase"]))))
            dot_surf = pygame.Surface((p["radius"] * 2, p["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*p["color"], alpha),
                               (p["radius"], p["radius"]), p["radius"])
            surface.blit(dot_surf, (int(p["pos"].x) - p["radius"], int(p["pos"].y) - p["radius"]))
    draw_glow(surface, ACCENT_COLOR, (int(anim_ball_pos[0]), int(anim_ball_pos[1])), BALL_SIZE // 2)
    title = font_title.render("PY-PONG", True, P1_COLOR)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))
    for i, opt in enumerate(["1 v 1", "1 v CPU", "QUIT"]):
        color = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(opt, True, color)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 320 + i * 70))
```

Replace `draw_mode_select` in `src/renderer.py`:

```python
def draw_mode_select(surface, font_large, font_small, selected: int,
                     context_label: str | None = None, menu_particles: list | None = None,
                     hover_t: float = 0.0):
    draw_background(surface)
    if menu_particles:
        for p in menu_particles:
            alpha = max(0, min(255, int(160 + 80 * math.sin(hover_t + p["phase"]))))
            dot_surf = pygame.Surface((p["radius"] * 2, p["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*p["color"], alpha),
                               (p["radius"], p["radius"]), p["radius"])
            surface.blit(dot_surf, (int(p["pos"].x) - p["radius"], int(p["pos"].y) - p["radius"]))
    title = font_large.render("SELECT MODE", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 160))
    modes = [
        ("FIRST TO 11", "Classic — first to 11 points wins"),
        ("BEST OF 3 SETS", "Win 2 sets of 7 points each"),
        ("TIMED  3 MIN", "Most points in 3 minutes — tie = sudden death"),
    ]
    for i, (label, desc) in enumerate(modes):
        y = 280 + i * 110
        color = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(label, True, color)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
        desc_text = font_small.render(desc, True, (120, 120, 140))
        surface.blit(desc_text, (SCREEN_W // 2 - desc_text.get_width() // 2, y + 44))
    if context_label:
        ctx = font_small.render(context_label, True, (80, 80, 100))
        surface.blit(ctx, (SCREEN_W // 2 - ctx.get_width() // 2, SCREEN_H - 50))
```

Replace `draw_difficulty_select` in `src/renderer.py`:

```python
def draw_difficulty_select(surface, font_large, font_small, selected: int,
                           menu_particles: list | None = None, hover_t: float = 0.0):
    draw_background(surface)
    if menu_particles:
        for p in menu_particles:
            alpha = max(0, min(255, int(160 + 80 * math.sin(hover_t + p["phase"]))))
            dot_surf = pygame.Surface((p["radius"] * 2, p["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*p["color"], alpha),
                               (p["radius"], p["radius"]), p["radius"])
            surface.blit(dot_surf, (int(p["pos"].x) - p["radius"], int(p["pos"].y) - p["radius"]))
    title = font_large.render("SELECT DIFFICULTY", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 160))
    for i, name in enumerate(DIFFICULTY_OPTIONS):
        y = 290 + i * 90
        color = DIFFICULTY_COLORS[name] if i == selected else (100, 100, 120)
        text = font_large.render(name, True, color)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
    hint = font_small.render("ESC  Back", True, (60, 60, 80))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 50))
```

- [ ] **Step 4: Update the three draw calls in Game._draw() to pass particles and hover_t**

In `src/game.py` `_draw()`, replace the three menu renderer calls:

```python
        if self.state == STATE_MENU:
            renderer.draw_menu(game_surf, self.font_title, self.font_large, self.font_small,
                               self.menu_selected, (self.menu_ball_pos.x, self.menu_ball_pos.y),
                               self.menu_particles, self.menu_hover_t)
        elif self.state == STATE_DIFFICULTY:
            renderer.draw_difficulty_select(game_surf, self.font_large, self.font_small,
                                            self.difficulty_selected,
                                            self.menu_particles, self.menu_hover_t)
        elif self.state == STATE_MODE_SELECT:
            context = f"1vCPU · {self.cpu_difficulty}" if self.opponent_type == OPPONENT_CPU else None
            renderer.draw_mode_select(game_surf, self.font_large, self.font_small,
                                      self.mode_selected, context,
                                      self.menu_particles, self.menu_hover_t)
```

- [ ] **Step 5: Run all tests**

```bash
cd /home/aryan/Documents/GitHub/py-pong && python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/aryan/Documents/GitHub/py-pong && git add src/game.py src/renderer.py && git commit -m "feat: add animated particle field to all menu screens"
```

---

## Task 3: Menu Item Hover Animations

**Files:**
- Modify: `src/game.py` (reset `menu_hover_t` on selection changes)
- Modify: `src/renderer.py` (scale, glow bar, color breathe, dim unselected)

- [ ] **Step 1: Reset menu_hover_t on selection changes in all three event handlers**

Replace `_handle_menu_event` in `src/game.py`:

```python
    def _handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.menu_selected = (self.menu_selected - 1) % 3
                self.menu_hover_t = 0.0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                if self.menu_selected == 0:
                    self.opponent_type = OPPONENT_HUMAN
                    self.state = STATE_MODE_SELECT
                elif self.menu_selected == 1:
                    self.opponent_type = OPPONENT_CPU
                    self.state = STATE_DIFFICULTY
                else:
                    return "quit"
```

Replace `_handle_difficulty_event` in `src/game.py`:

```python
    def _handle_difficulty_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.difficulty_selected = (self.difficulty_selected - 1) % 4
                self.menu_hover_t = 0.0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.difficulty_selected = (self.difficulty_selected + 1) % 4
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                self.cpu_difficulty = DIFFICULTY_OPTIONS[self.difficulty_selected]
                self.state = STATE_MODE_SELECT
            elif event.key == pygame.K_ESCAPE:
                self.state = STATE_MENU
```

Replace `_handle_mode_select_event` in `src/game.py`:

```python
    def _handle_mode_select_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.mode_selected = (self.mode_selected - 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_DOWN:
                self.mode_selected = (self.mode_selected + 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                modes = [MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED]
                self.game_mode = modes[self.mode_selected]
                self._start_match()
            elif event.key == pygame.K_ESCAPE:
                if self.opponent_type == OPPONENT_CPU:
                    self.state = STATE_DIFFICULTY
                else:
                    self.state = STATE_MENU
```

- [ ] **Step 2: Update draw_menu item loop — scale, glow bar, color breathe, dim unselected**

In `src/renderer.py`, replace only the item loop at the bottom of `draw_menu` (after the title blit):

```python
    for i, opt in enumerate(["1 v 1", "1 v CPU", "QUIT"]):
        y = 320 + i * 70
        if i == selected:
            t = 0.15 * (0.5 + 0.5 * math.sin(hover_t * 2))
            color = (
                int(ACCENT_COLOR[0] + (WHITE[0] - ACCENT_COLOR[0]) * t),
                int(ACCENT_COLOR[1] + (WHITE[1] - ACCENT_COLOR[1]) * t),
                int(ACCENT_COLOR[2] + (WHITE[2] - ACCENT_COLOR[2]) * t),
            )
            base_surf = font_large.render(opt, True, color)
            w, h = base_surf.get_size()
            scaled = pygame.transform.smoothscale(base_surf, (int(w * 1.08), int(h * 1.08)))
            surface.blit(scaled, (SCREEN_W // 2 - scaled.get_width() // 2,
                                  y - (scaled.get_height() - h) // 2))
            bar_w = int(w + 8 * math.sin(hover_t * 3))
            pygame.draw.rect(surface, color, (SCREEN_W // 2 - bar_w // 2, y + h + 6, bar_w, 2))
        else:
            dim = (int(WHITE[0] * 0.6), int(WHITE[1] * 0.6), int(WHITE[2] * 0.6))
            text = font_large.render(opt, True, dim)
            surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
```

- [ ] **Step 3: Update draw_mode_select item loop**

In `src/renderer.py`, replace only the `for i, (label, desc) in enumerate(modes):` loop in `draw_mode_select`:

```python
    for i, (label, desc) in enumerate(modes):
        y = 280 + i * 110
        if i == selected:
            t = 0.15 * (0.5 + 0.5 * math.sin(hover_t * 2))
            color = (
                int(ACCENT_COLOR[0] + (WHITE[0] - ACCENT_COLOR[0]) * t),
                int(ACCENT_COLOR[1] + (WHITE[1] - ACCENT_COLOR[1]) * t),
                int(ACCENT_COLOR[2] + (WHITE[2] - ACCENT_COLOR[2]) * t),
            )
            base_surf = font_large.render(label, True, color)
            w, h = base_surf.get_size()
            scaled = pygame.transform.smoothscale(base_surf, (int(w * 1.08), int(h * 1.08)))
            surface.blit(scaled, (SCREEN_W // 2 - scaled.get_width() // 2,
                                  y - (scaled.get_height() - h) // 2))
            bar_w = int(w + 8 * math.sin(hover_t * 3))
            pygame.draw.rect(surface, color, (SCREEN_W // 2 - bar_w // 2, y + h + 6, bar_w, 2))
        else:
            dim = (int(WHITE[0] * 0.6), int(WHITE[1] * 0.6), int(WHITE[2] * 0.6))
            text = font_large.render(label, True, dim)
            surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
        desc_text = font_small.render(desc, True, (120, 120, 140))
        surface.blit(desc_text, (SCREEN_W // 2 - desc_text.get_width() // 2, y + 44))
```

- [ ] **Step 4: Update draw_difficulty_select item loop**

In `src/renderer.py`, replace only the `for i, name in enumerate(DIFFICULTY_OPTIONS):` loop in `draw_difficulty_select`:

```python
    for i, name in enumerate(DIFFICULTY_OPTIONS):
        y = 290 + i * 90
        if i == selected:
            base_color = DIFFICULTY_COLORS[name]
            t = 0.15 * (0.5 + 0.5 * math.sin(hover_t * 2))
            color = (
                int(base_color[0] + (WHITE[0] - base_color[0]) * t),
                int(base_color[1] + (WHITE[1] - base_color[1]) * t),
                int(base_color[2] + (WHITE[2] - base_color[2]) * t),
            )
            base_surf = font_large.render(name, True, color)
            w, h = base_surf.get_size()
            scaled = pygame.transform.smoothscale(base_surf, (int(w * 1.08), int(h * 1.08)))
            surface.blit(scaled, (SCREEN_W // 2 - scaled.get_width() // 2,
                                  y - (scaled.get_height() - h) // 2))
            bar_w = int(w + 8 * math.sin(hover_t * 3))
            pygame.draw.rect(surface, color, (SCREEN_W // 2 - bar_w // 2, y + h + 6, bar_w, 2))
        else:
            bc = DIFFICULTY_COLORS[name]
            dim = (int(bc[0] * 0.6), int(bc[1] * 0.6), int(bc[2] * 0.6))
            text = font_large.render(name, True, dim)
            surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
```

- [ ] **Step 5: Run all tests**

```bash
cd /home/aryan/Documents/GitHub/py-pong && python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/aryan/Documents/GitHub/py-pong && git add src/game.py src/renderer.py && git commit -m "feat: menu item hover animations — scale, glow bar, color breathe"
```

---

## Task 4: Wire TransitionManager in Game

**Files:**
- Modify: `src/game.py`

- [ ] **Step 1: Import TransitionManager and add to __init__**

Update the import from `src.effects` in `src/game.py`:

```python
from src.effects import ScreenShake, ParticleSystem, TransitionManager
```

In `Game.__init__`, add `self.transition` after `self.particles`:

```python
        self.shake = ScreenShake()
        self.particles = ParticleSystem()
        self.transition = TransitionManager()
```

- [ ] **Step 2: Advance and draw the transition in _update and _draw**

Replace `_update` in `src/game.py` to call `self.transition.update(dt)`:

```python
    def _update(self, dt: float):
        self.menu_hover_t += dt
        self.transition.update(dt)
        if self.state == STATE_MENU:
            self._update_menu(dt)
        elif self.state in (STATE_DIFFICULTY, STATE_MODE_SELECT):
            self._update_menu_particles(dt)
        elif self.state == STATE_PLAYING:
            self._update_playing(dt)
        elif self.state == STATE_GAME_OVER:
            self.gameover_pulse += dt
            self.particles.update(dt)
```

In `_draw`, add `self.transition.draw(game_surf)` as the final operation on `game_surf`, immediately before `self.screen.fill(BG_COLOR)`:

```python
        self.transition.draw(game_surf)
        self.screen.fill(BG_COLOR)
        self.screen.blit(game_surf, (int(offset.x), int(offset.y)))
```

- [ ] **Step 3: Guard all event handling while a transition is in progress**

Replace the top of `_handle_event` in `src/game.py`:

```python
    def _handle_event(self, event):
        if self.transition.blocking:
            return
        if self.state == STATE_MENU:
            return self._handle_menu_event(event)
        elif self.state == STATE_DIFFICULTY:
            return self._handle_difficulty_event(event)
        elif self.state == STATE_MODE_SELECT:
            return self._handle_mode_select_event(event)
        elif self.state == STATE_PLAYING:
            return self._handle_playing_event(event)
        elif self.state == STATE_PAUSED:
            return self._handle_paused_event(event)
        elif self.state == STATE_GAME_OVER:
            return self._handle_gameover_event(event)
```

- [ ] **Step 4: Replace direct state assignments with transition.start() in all menu event handlers**

Replace `_handle_menu_event` in `src/game.py`:

```python
    def _handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.menu_selected = (self.menu_selected - 1) % 3
                self.menu_hover_t = 0.0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                if self.menu_selected == 0:
                    def _go_1v1():
                        self.opponent_type = OPPONENT_HUMAN
                        self.state = STATE_MODE_SELECT
                    self.transition.start(_go_1v1)
                elif self.menu_selected == 1:
                    def _go_cpu():
                        self.opponent_type = OPPONENT_CPU
                        self.state = STATE_DIFFICULTY
                    self.transition.start(_go_cpu)
                else:
                    return "quit"
```

Replace `_handle_difficulty_event` in `src/game.py`:

```python
    def _handle_difficulty_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.difficulty_selected = (self.difficulty_selected - 1) % 4
                self.menu_hover_t = 0.0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.difficulty_selected = (self.difficulty_selected + 1) % 4
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                diff = DIFFICULTY_OPTIONS[self.difficulty_selected]
                def _go_mode():
                    self.cpu_difficulty = diff
                    self.state = STATE_MODE_SELECT
                self.transition.start(_go_mode)
            elif event.key == pygame.K_ESCAPE:
                self.transition.start(lambda: setattr(self, "state", STATE_MENU))
```

Replace `_handle_mode_select_event` in `src/game.py`:

```python
    def _handle_mode_select_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.mode_selected = (self.mode_selected - 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_DOWN:
                self.mode_selected = (self.mode_selected + 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                modes = [MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED]
                mode = modes[self.mode_selected]
                def _start():
                    self.game_mode = mode
                    self._start_match()
                self.transition.start(_start)
            elif event.key == pygame.K_ESCAPE:
                if self.opponent_type == OPPONENT_CPU:
                    self.transition.start(lambda: setattr(self, "state", STATE_DIFFICULTY))
                else:
                    self.transition.start(lambda: setattr(self, "state", STATE_MENU))
```

Replace `_handle_gameover_event` in `src/game.py`:

```python
    def _handle_gameover_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.gameover_selected = (self.gameover_selected - 1) % 2
            elif event.key == pygame.K_DOWN:
                self.gameover_selected = (self.gameover_selected + 1) % 2
            elif event.key == pygame.K_RETURN:
                if self.gameover_selected == 0:
                    self.transition.start(self._start_match)
                else:
                    self.transition.start(self._reset_to_menu)
```

- [ ] **Step 5: Run all tests**

```bash
cd /home/aryan/Documents/GitHub/py-pong && python -m pytest tests/ -v
```

Expected: all tests PASS. (`_end_match` still sets `self.state = STATE_GAME_OVER` directly, so game-logic tests are unaffected.)

- [ ] **Step 6: Commit**

```bash
cd /home/aryan/Documents/GitHub/py-pong && git add src/game.py && git commit -m "feat: wire TransitionManager — smooth fade on all menu navigation"
```
