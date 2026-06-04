# Smash Meter & Audio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add main-theme menu music, ball-hit SFX, and a per-player Final Smash charge meter that replaces the old field-spawn power-up system.

**Architecture:** Five focused tasks — copy assets, wire audio, strip old power-up system + add constants, TDD the smash meter logic, then update the renderer HUD. Each task leaves the test suite green.

**Tech Stack:** Python 3.12+, pygame-ce>=2.5.0, pytest

---

## File Map

| File | Change |
|------|--------|
| `assets/sounds/main theme.mp3` | New — copied from `~/Downloads/` |
| `assets/sounds/ball hit.mp3` | New — copied from `~/Downloads/` |
| `src/constants.py` | Add `SMASH_BASE_CHARGE_RATE`, `SMASH_PER_POINT_CHARGE` |
| `src/game.py` | Remove old power-up system; add smash meter state + logic + audio wiring |
| `src/renderer.py` | Remove `draw_powerup`; add `_draw_smash_meter`; update `draw_hud` signature |
| `tests/test_game_logic.py` | Append smash meter tests |

---

### Task 1: Copy audio assets

**Files:**
- Create: `assets/sounds/main theme.mp3`
- Create: `assets/sounds/ball hit.mp3`

- [ ] **Step 1: Copy files from Downloads**

```bash
cp ~/Downloads/main\ theme.mp3 /home/aryan/Documents/GitHub/py-pong/assets/sounds/
cp ~/Downloads/ball\ hit.mp3 /home/aryan/Documents/GitHub/py-pong/assets/sounds/
```

- [ ] **Step 2: Verify both files are present**

```bash
ls -lh assets/sounds/
```

Expected output includes both `ball hit.mp3` and `main theme.mp3` with non-zero size.

- [ ] **Step 3: Commit**

```bash
git add "assets/sounds/ball hit.mp3" "assets/sounds/main theme.mp3"
git commit -m "feat: add ball hit and main theme audio assets"
```

---

### Task 2: Wire ball hit sound and menu music

**Files:**
- Modify: `src/game.py` — `_init_audio`, `_start_match`, `_reset_to_menu`, `__init__`

- [ ] **Step 1: Replace `_init_audio` in src/game.py**

Replace the entire `_init_audio` method (lines 61–84) with:

```python
def _init_audio(self):
    self.sfx: dict = {}
    for name, path in [
        ("hit", "assets/sounds/ball hit.mp3"),
        ("score", "assets/sounds/score.wav"),
        ("powerup", "assets/sounds/powerup.wav"),
        ("win", "assets/sounds/win.wav"),
    ]:
        try:
            self.sfx[name] = pygame.mixer.Sound(path)
        except Exception:
            self.sfx[name] = None

    self.music_channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
    self.music_normal = None
    self.music_intense = None
    try:
        self.music_normal = pygame.mixer.Sound("assets/sounds/music_normal.ogg")
        self.music_intense = pygame.mixer.Sound("assets/sounds/music_intense.ogg")
    except Exception:
        pass
    self.current_music = "normal"
    if self.music_normal:
        self.music_channels[0].play(self.music_normal, loops=-1)

    self._menu_music_loaded = False
    try:
        pygame.mixer.music.load("assets/sounds/main theme.mp3")
        self._menu_music_loaded = True
    except Exception:
        pass
```

`pygame.mixer.music` (menu theme) and `pygame.mixer.Sound` channels (normal/intense) are separate systems — they don't conflict.

- [ ] **Step 2: Add `_start_menu_music` and `_stop_menu_music` helpers to src/game.py**

Add these two methods directly after `_init_audio`:

```python
def _start_menu_music(self):
    if self._menu_music_loaded:
        pygame.mixer.music.play(-1)

def _stop_menu_music(self):
    if self._menu_music_loaded:
        pygame.mixer.music.fadeout(500)
```

- [ ] **Step 3: Call `_start_menu_music()` at the end of `__init__`**

In `__init__`, the last line is `self._init_audio()`. Add one line after it:

```python
        self._init_audio()
        self._start_menu_music()
```

- [ ] **Step 4: Stop music when gameplay starts; restart when returning to menu**

In `_start_match`, add `self._stop_menu_music()` as the first line of the method:

```python
    def _start_match(self):
        self._stop_menu_music()
        self.p1.score = 0
        # ... rest unchanged
```

In `_reset_to_menu`, add `self._start_menu_music()` after setting the state:

```python
    def _reset_to_menu(self):
        self.state = STATE_MENU
        self.menu_selected = 0
        self._start_menu_music()
```

- [ ] **Step 5: Run the full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all 44 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/game.py
git commit -m "feat: ball hit SFX and menu music with state-based start/stop"
```

---

### Task 3: Add smash constants + strip old power-up system

**Files:**
- Modify: `src/constants.py`
- Modify: `src/game.py`
- Modify: `src/renderer.py`

- [ ] **Step 1: Add smash constants to src/constants.py**

Append to the end of `src/constants.py`:

```python
# Final Smash meter
SMASH_BASE_CHARGE_RATE = 0.025   # fills in ~40s at zero gap
SMASH_PER_POINT_CHARGE = 0.020   # additional rate per point behind
```

- [ ] **Step 2: Update game.py imports — remove power-up constants and classes**

Replace the current import block at the top of `src/game.py` with:

```python
import random
import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, FPS, HUD_HEIGHT, BG_COLOR,
    PADDLE_W, PADDLE_H, PADDLE_MARGIN, PADDLE_SPEED,
    BALL_SIZE, BALL_SPEED_INITIAL,
    MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED,
    TIMED_DURATION, SUDDEN_DEATH_DURATION, SET_WIN_SCORE,
    MATCH_WIN_SETS, CLASSIC_WIN_SCORE,
    STATE_MENU, STATE_MODE_SELECT, STATE_PLAYING,
    STATE_PAUSED, STATE_GAME_OVER,
    SHAKE_HIT_TRAUMA, SHAKE_SCORE_TRAUMA,
    P1_COLOR, P2_COLOR,
    SMASH_BASE_CHARGE_RATE, SMASH_PER_POINT_CHARGE,
)
from src.entities import Paddle, Ball
from src.effects import ScreenShake, ParticleSystem
import src.renderer as renderer
```

- [ ] **Step 3: Remove power-up state from `__init__`**

In `__init__`, remove these two lines:

```python
        self.powerup: PowerUp | None = None
```
```python
        self.powerup_spawn_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)
```

- [ ] **Step 4: Remove power-up reset lines from `_start_match`**

In `_start_match`, remove these two lines:

```python
        self.powerup = None
        self.powerup_spawn_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)
```

- [ ] **Step 5: Remove `_update_powerup` call from `_update_playing`**

In `_update_playing`, remove this line:

```python
        self._update_powerup(dt)
```

- [ ] **Step 6: Remove power-up drawing from `_draw`**

In `_draw`, inside the `STATE_PLAYING` branch, remove:

```python
            if self.powerup:
                renderer.draw_powerup(game_surf, self.powerup)
```

- [ ] **Step 7: Delete `_update_powerup` and `_activate_powerup` methods entirely**

Delete from `src/game.py` (lines 354–391 in the original file):

```python
    def _update_powerup(self, dt: float):
        ...

    def _activate_powerup(self, powerup: PowerUp, ball: Ball):
        ...
```

Both methods are fully removed.

- [ ] **Step 8: Remove `draw_powerup` and dead constants from src/renderer.py**

In `src/renderer.py`:

1. Remove `POWERUP_SIZE` from the imports line (keep `POWERUP_DURATION` — still used by `_draw_powerup_hud`):

```python
from src.constants import (
    SCREEN_W, SCREEN_H, HUD_HEIGHT, BG_COLOR,
    P1_COLOR, P2_COLOR, ACCENT_COLOR, WHITE,
    BALL_SIZE, BALL_SPEED_INITIAL, BALL_SPEED_MAX_MULTIPLIER,
    PADDLE_H, POWERUP_DURATION,
    MODE_TIMED, MODE_BEST_OF_3,
)
```

2. Remove the `POWERUP_COLORS` dict (it was only used by `draw_powerup`). Keep `POWERUP_LABELS` — still used by `_draw_powerup_hud`.

3. Delete the `draw_powerup` function entirely:

```python
def draw_powerup(surface: pygame.Surface, powerup):
    color = POWERUP_COLORS.get(powerup.type, WHITE)
    scale = 1.0 + 0.15 * math.sin(powerup.pulse_t * 4)
    r = max(1, int(POWERUP_SIZE // 2 * scale))
    draw_glow(surface, color, (int(powerup.pos.x), int(powerup.pos.y)), r)
```

- [ ] **Step 9: Run full test suite to confirm nothing broken**

```bash
python -m pytest tests/ -v
```

Expected: all 44 tests PASS.

- [ ] **Step 10: Commit**

```bash
git add src/constants.py src/game.py src/renderer.py
git commit -m "feat: smash constants; strip old field power-up system"
```

---

### Task 4: Smash meter — tests then implementation

**Files:**
- Modify: `tests/test_game_logic.py` (append smash tests)
- Modify: `src/game.py` (add state, `_update_smash_meters`, `_activate_smash`, wire into loop)

- [ ] **Step 1: Write failing smash meter tests — append to tests/test_game_logic.py**

Append to `tests/test_game_logic.py`:

```python
from src.constants import SMASH_BASE_CHARGE_RATE, SMASH_PER_POINT_CHARGE


def test_smash_meter_charges_at_base_rate_when_tied():
    g = make_game()
    g.p1.score = 3
    g.p2.score = 3
    g._update_smash_meters(1.0)
    assert abs(g.p1_smash_meter - SMASH_BASE_CHARGE_RATE) < 0.001


def test_smash_meter_charges_faster_when_behind():
    g = make_game()
    g.p1.score = 2
    g.p2.score = 5  # p1 is 3 points behind
    g._update_smash_meters(1.0)
    expected = SMASH_BASE_CHARGE_RATE + 3 * SMASH_PER_POINT_CHARGE
    assert abs(g.p1_smash_meter - expected) < 0.001


def test_smash_meter_charges_at_base_when_ahead():
    g = make_game()
    g.p1.score = 5
    g.p2.score = 2  # p1 is ahead — gap = 0
    g._update_smash_meters(1.0)
    assert abs(g.p1_smash_meter - SMASH_BASE_CHARGE_RATE) < 0.001


def test_smash_meter_caps_at_one():
    g = make_game()
    g.p1_smash_meter = 0.95
    g.p1.score = 0
    g.p2.score = 10
    g._update_smash_meters(5.0)
    assert g.p1_smash_meter <= 1.0


def test_smash_ready_flag_set_when_meter_reaches_one():
    g = make_game()
    g.p1_smash_meter = 0.99
    g.p1.score = 0
    g.p2.score = 5
    g._update_smash_meters(1.0)
    assert g.p1_smash_ready is True


def test_activate_smash_p1_big_paddle_p2_shrinks():
    g = make_game()
    g.p1_smash_ready = True
    g.p1_smash_meter = 1.0
    g._activate_smash(1)
    assert g.p1.height > PADDLE_H
    assert g.p1.active_powerup == "BIG_PADDLE"
    assert g.p2.height < PADDLE_H
    assert g.p2.active_powerup == "SMALL_OPPONENT"


def test_activate_smash_p2_big_paddle_p1_shrinks():
    g = make_game()
    g.p2_smash_ready = True
    g.p2_smash_meter = 1.0
    g._activate_smash(2)
    assert g.p2.height > PADDLE_H
    assert g.p2.active_powerup == "BIG_PADDLE"
    assert g.p1.height < PADDLE_H
    assert g.p1.active_powerup == "SMALL_OPPONENT"


def test_activate_smash_resets_meter_and_flag():
    g = make_game()
    g.p1_smash_ready = True
    g.p1_smash_meter = 1.0
    g._activate_smash(1)
    assert g.p1_smash_meter == 0.0
    assert g.p1_smash_ready is False


def test_activate_smash_does_nothing_when_not_ready():
    g = make_game()
    g.p1_smash_ready = False
    g.p1_smash_meter = 0.5
    g._activate_smash(1)
    assert g.p1.height == PADDLE_H
    assert g.p1.active_powerup is None


def test_smash_meters_reset_on_new_match():
    g = make_game()
    g.p1_smash_meter = 0.8
    g.p2_smash_meter = 0.6
    g.p1_smash_ready = True
    g._start_match()
    assert g.p1_smash_meter == 0.0
    assert g.p2_smash_meter == 0.0
    assert g.p1_smash_ready is False


def test_smash_meters_reset_on_set_win():
    g = make_game(MODE_BEST_OF_3)
    g.p1_smash_meter = 0.9
    g.p2_smash_meter = 0.7
    g.p1.score = SET_WIN_SCORE - 1
    ball = g.balls[0]
    g._score(1, ball)  # triggers _check_set_win
    assert g.p1_smash_meter == 0.0
    assert g.p2_smash_meter == 0.0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_game_logic.py -k "smash" -v
```

Expected: `AttributeError` — `p1_smash_meter` not defined yet.

- [ ] **Step 3: Add smash meter state to `__init__` in src/game.py**

After `self.rally_count = 0` in `__init__`, add:

```python
        self.p1_smash_meter = 0.0
        self.p2_smash_meter = 0.0
        self.p1_smash_ready = False
        self.p2_smash_ready = False
        self.smash_pulse_t = 0.0
```

- [ ] **Step 4: Add `_update_smash_meters` method to src/game.py**

Add this method after `_update_music`:

```python
    def _update_smash_meters(self, dt: float):
        p1_gap = max(0, self.p2.score - self.p1.score)
        self.p1_smash_meter = min(1.0, self.p1_smash_meter + (SMASH_BASE_CHARGE_RATE + p1_gap * SMASH_PER_POINT_CHARGE) * dt)
        if self.p1_smash_meter >= 1.0:
            self.p1_smash_ready = True

        p2_gap = max(0, self.p1.score - self.p2.score)
        self.p2_smash_meter = min(1.0, self.p2_smash_meter + (SMASH_BASE_CHARGE_RATE + p2_gap * SMASH_PER_POINT_CHARGE) * dt)
        if self.p2_smash_meter >= 1.0:
            self.p2_smash_ready = True
```

- [ ] **Step 5: Add `_activate_smash` method to src/game.py**

Add this method after `_update_smash_meters`:

```python
    def _activate_smash(self, player: int):
        if player == 1 and not self.p1_smash_ready:
            return
        if player == 2 and not self.p2_smash_ready:
            return
        activator = self.p1 if player == 1 else self.p2
        opponent = self.p2 if player == 1 else self.p1
        activator.activate_powerup("BIG_PADDLE")
        opponent.activate_powerup("SMALL_OPPONENT")
        self._play_sfx("powerup")
        if player == 1:
            self.p1_smash_meter = 0.0
            self.p1_smash_ready = False
        else:
            self.p2_smash_meter = 0.0
            self.p2_smash_ready = False
```

- [ ] **Step 6: Wire smash meter updates into `_update_playing`**

In `_update_playing`, replace the line `self._update_powerup(dt)` (already removed in Task 3) with two new lines. The block after `_handle_collisions()` should now read:

```python
        self._handle_collisions()
        self._update_smash_meters(dt)
        self.smash_pulse_t += dt
        self.shake.update(dt)
        self.particles.update(dt)
```

- [ ] **Step 7: Wire Shift keys into `_handle_playing_event`**

Replace the current `_handle_playing_event` with:

```python
    def _handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = STATE_PAUSED
                self.pause_selected = 0
            elif event.key == pygame.K_LSHIFT:
                self._activate_smash(1)
            elif event.key == pygame.K_RSHIFT:
                self._activate_smash(2)
```

- [ ] **Step 8: Reset smash meters in `_start_match`**

In `_start_match`, after `self.rally_count = 0`, add:

```python
        self.p1_smash_meter = 0.0
        self.p2_smash_meter = 0.0
        self.p1_smash_ready = False
        self.p2_smash_ready = False
```

- [ ] **Step 9: Reset smash meters in `_check_set_win`**

In `_check_set_win`, after `self.p1.score = 0` / `self.p2.score = 0`, add:

```python
                self.p1_smash_meter = 0.0
                self.p2_smash_meter = 0.0
                self.p1_smash_ready = False
                self.p2_smash_ready = False
```

The full updated `_check_set_win` becomes:

```python
    def _check_set_win(self):
        for player, paddle in [(1, self.p1), (2, self.p2)]:
            if paddle.score >= SET_WIN_SCORE:
                paddle.sets_won += 1
                self.p1.score = 0
                self.p2.score = 0
                self.p1_smash_meter = 0.0
                self.p2_smash_meter = 0.0
                self.p1_smash_ready = False
                self.p2_smash_ready = False
                if paddle.sets_won >= MATCH_WIN_SETS:
                    self._end_match(winner=player)
                else:
                    self._start_countdown()
                return
```

- [ ] **Step 10: Run smash meter tests**

```bash
python -m pytest tests/test_game_logic.py -k "smash" -v
```

Expected: all 11 smash tests PASS.

- [ ] **Step 11: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all 55 tests PASS.

- [ ] **Step 12: Commit**

```bash
git add src/game.py tests/test_game_logic.py
git commit -m "feat: Final Smash meter — charge logic, activation, Shift keys, tests"
```

---

### Task 5: Renderer — smash meter HUD bar

**Files:**
- Modify: `src/renderer.py` — add `_draw_smash_meter`, update `draw_hud` signature and body
- Modify: `src/game.py` — update `draw_hud` call in `_draw`

- [ ] **Step 1: Add `_draw_smash_meter` to src/renderer.py**

Add this function after `_draw_powerup_hud`:

```python
def _draw_smash_meter(surface, cx: int, meter: float, ready: bool, pulse_t: float,
                      color: tuple, shift_label: str, font_small):
    bar_w = 100
    bar_x = cx - bar_w // 2
    bar_y = HUD_HEIGHT - 14
    pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, 6), border_radius=3)
    if ready:
        pulse_alpha = int(180 + 75 * math.sin(pulse_t * 6))
        pulse_surf = pygame.Surface((bar_w, 6), pygame.SRCALPHA)
        pygame.draw.rect(pulse_surf, (*ACCENT_COLOR, pulse_alpha), pulse_surf.get_rect(), border_radius=3)
        surface.blit(pulse_surf, (bar_x, bar_y))
        label_txt = font_small.render(f"READY! {shift_label}", True, ACCENT_COLOR)
    else:
        fill_w = int(bar_w * meter)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, 6), border_radius=3)
        label_txt = font_small.render("SMASH", True, color)
    surface.blit(label_txt, (cx - label_txt.get_width() // 2, bar_y - 16))
```

- [ ] **Step 2: Update `draw_hud` signature in src/renderer.py**

Replace:

```python
def draw_hud(surface, p1, p2, font_large, font_small,
             game_mode: str, time_left, sets):
```

With:

```python
def draw_hud(surface, p1, p2, font_large, font_small,
             game_mode: str, time_left, sets,
             p1_smash: float, p2_smash: float,
             p1_ready: bool, p2_ready: bool, smash_pulse_t: float):
```

- [ ] **Step 3: Replace the two `_draw_powerup_hud` calls inside `draw_hud`**

Replace:

```python
    _draw_powerup_hud(surface, p1, font_small, SCREEN_W // 4, P1_COLOR)
    _draw_powerup_hud(surface, p2, font_small, 3 * SCREEN_W // 4, P2_COLOR)
```

With:

```python
    if p1.active_powerup:
        _draw_powerup_hud(surface, p1, font_small, SCREEN_W // 4, P1_COLOR)
    else:
        _draw_smash_meter(surface, SCREEN_W // 4, p1_smash, p1_ready, smash_pulse_t,
                          P1_COLOR, "[LSHIFT]", font_small)

    if p2.active_powerup:
        _draw_powerup_hud(surface, p2, font_small, 3 * SCREEN_W // 4, P2_COLOR)
    else:
        _draw_smash_meter(surface, 3 * SCREEN_W // 4, p2_smash, p2_ready, smash_pulse_t,
                          P2_COLOR, "[RSHIFT]", font_small)
```

- [ ] **Step 4: Update the `draw_hud` call in `src/game.py`**

In `_draw`, replace:

```python
            renderer.draw_hud(
                game_surf, self.p1, self.p2, self.font_large, self.font_small,
                self.game_mode,
                self.time_left if self.game_mode == MODE_TIMED else None,
                (self.p1.sets_won, self.p2.sets_won) if self.game_mode == MODE_BEST_OF_3 else None,
            )
```

With:

```python
            renderer.draw_hud(
                game_surf, self.p1, self.p2, self.font_large, self.font_small,
                self.game_mode,
                self.time_left if self.game_mode == MODE_TIMED else None,
                (self.p1.sets_won, self.p2.sets_won) if self.game_mode == MODE_BEST_OF_3 else None,
                self.p1_smash_meter, self.p2_smash_meter,
                self.p1_smash_ready, self.p2_smash_ready,
                self.smash_pulse_t,
            )
```

- [ ] **Step 5: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all 55 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/renderer.py src/game.py
git commit -m "feat: smash meter HUD bar — neon fill, READY pulse, shift hint"
```
