# CPU Smash Meter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the CPU opponent to charge and fire the Final Smash meter on HARD (instantly) and INSANE (when ball is incoming and player is off-center) difficulty levels, with the meter visible to the player in the HUD.

**Architecture:** `CPUController` gains `smash_enabled`/`_insane_strategic` flags and a `should_smash()` method. `game.py` gates p2 meter charging and calls `should_smash()` each frame, firing `_activate_smash(2)` when it returns True. `renderer.py` receives the real meter values and shows a clean `"READY!"` label (no key hint) for CPU mode.

**Tech Stack:** Python 3.12, pygame-ce, pytest

---

### Task 1: CPUController — smash fields and `should_smash()`

**Files:**
- Modify: `src/cpu.py`
- Test: `tests/test_cpu.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cpu.py`:

```python
def _make_player_paddle():
    return Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)


def _make_ball_incoming():
    """Ball moving right — toward CPU (P2 on the right)."""
    b = Ball()
    b.vel.x = 400
    return b


def _make_ball_retreating():
    """Ball moving left — away from CPU."""
    b = Ball()
    b.vel.x = -400
    return b


def test_smash_disabled_for_easy():
    cpu = CPUController("EASY")
    assert cpu.smash_enabled is False


def test_smash_disabled_for_medium():
    cpu = CPUController("MEDIUM")
    assert cpu.smash_enabled is False


def test_smash_enabled_for_hard():
    cpu = CPUController("HARD")
    assert cpu.smash_enabled is True


def test_smash_enabled_for_insane():
    cpu = CPUController("INSANE")
    assert cpu.smash_enabled is True


def test_should_smash_returns_false_when_meter_not_ready():
    cpu = CPUController("HARD")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    assert cpu.should_smash(ball, player, meter_ready=False) is False


def test_should_smash_returns_false_for_disabled_difficulty():
    cpu = CPUController("EASY")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    assert cpu.should_smash(ball, player, meter_ready=True) is False


def test_hard_fires_immediately_when_ready():
    cpu = CPUController("HARD")
    ball = _make_ball_retreating()   # direction does not matter for HARD
    player = _make_player_paddle()
    player.pos.y = CENTER_Y          # player perfectly centered — still fires
    assert cpu.should_smash(ball, player, meter_ready=True) is True


def test_insane_fires_when_ball_incoming_and_player_off_center():
    cpu = CPUController("INSANE")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    player.pos.y = CENTER_Y + 120    # well off-center (>80 px)
    assert cpu.should_smash(ball, player, meter_ready=True) is True


def test_insane_withholds_when_ball_moving_away():
    cpu = CPUController("INSANE")
    ball = _make_ball_retreating()
    player = _make_player_paddle()
    player.pos.y = CENTER_Y + 120    # off-center but ball retreating
    assert cpu.should_smash(ball, player, meter_ready=True) is False


def test_insane_withholds_when_player_is_centered():
    cpu = CPUController("INSANE")
    ball = _make_ball_incoming()
    player = _make_player_paddle()
    player.pos.y = CENTER_Y + 20     # within 80 px — considered centered
    assert cpu.should_smash(ball, player, meter_ready=True) is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python -m pytest tests/test_cpu.py::test_smash_enabled_for_hard -v
```

Expected: `FAILED` — `AttributeError: 'CPUController' object has no attribute 'smash_enabled'`

- [ ] **Step 3: Implement the changes in `src/cpu.py`**

Replace the full file with:

```python
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
        self.smash_enabled: bool = difficulty in ("HARD", "INSANE")
        self._insane_strategic: bool = difficulty == "INSANE"

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

    def should_smash(self, ball: Ball, player_paddle: Paddle, meter_ready: bool) -> bool:
        if not self.smash_enabled or not meter_ready:
            return False
        if not self._insane_strategic:
            return True  # HARD: fire the moment meter is full
        # INSANE: ball heading toward CPU and player visibly off-center
        field_center_y = (SCREEN_H + HUD_HEIGHT) / 2.0
        player_off_center = abs(player_paddle.pos.y - field_center_y) > 80
        return ball.vel.x > 0 and player_off_center
```

- [ ] **Step 4: Run all new cpu tests**

```bash
python -m pytest tests/test_cpu.py -v
```

Expected: all tests pass (including the original 6 and all new ones).

- [ ] **Step 5: Commit**

```bash
git add src/cpu.py tests/test_cpu.py
git commit -m "feat: add CPU smash fields and should_smash() to CPUController"
```

---

### Task 2: game.py — charge gating, activation, HUD passthrough

**Files:**
- Modify: `src/game.py`
- Test: `tests/test_game_logic.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_game_logic.py`:

```python
from src.cpu import CPUController
from src.constants import OPPONENT_CPU, SMASH_BASE_CHARGE_RATE


def _make_cpu_game(difficulty):
    g = make_game()
    g.opponent_type = OPPONENT_CPU
    g.cpu_difficulty = difficulty
    g.cpu = CPUController(difficulty)
    return g


def test_cpu_p2_meter_does_not_charge_on_easy():
    g = _make_cpu_game("EASY")
    g._update_smash_meters(5.0)
    assert g.p2_smash_meter == 0.0


def test_cpu_p2_meter_does_not_charge_on_medium():
    g = _make_cpu_game("MEDIUM")
    g._update_smash_meters(5.0)
    assert g.p2_smash_meter == 0.0


def test_cpu_p2_meter_charges_on_hard():
    g = _make_cpu_game("HARD")
    g._update_smash_meters(1.0)
    assert g.p2_smash_meter > 0.0


def test_cpu_p2_meter_charges_on_insane():
    g = _make_cpu_game("INSANE")
    g._update_smash_meters(1.0)
    assert g.p2_smash_meter > 0.0


def test_hard_cpu_fires_smash_in_update_playing():
    """_update_playing calls _activate_smash(2) when HARD CPU meter is ready."""
    g = _make_cpu_game("HARD")
    g.p2_smash_meter = 1.0
    g.p2_smash_ready = True
    g._update_playing(0.016)
    assert g.p2_smash_meter == 0.0
    assert g.p2_smash_ready is False


def test_insane_cpu_withholds_smash_when_ball_moving_away():
    """INSANE CPU does not fire when ball.vel.x < 0, even with meter ready."""
    g = _make_cpu_game("INSANE")
    g.p2_smash_meter = 1.0
    g.p2_smash_ready = True
    g.balls[0].vel.x = -400  # ball moving away from CPU
    g._update_playing(0.016)
    assert g.p2_smash_ready is True  # meter was NOT consumed
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_game_logic.py::test_cpu_p2_meter_charges_on_hard -v
```

Expected: `FAILED` — `AssertionError: assert 0.0 > 0.0` (meter not charging yet).

- [ ] **Step 3: Edit `_update_smash_meters` in `src/game.py`**

Find the block starting at line 128:

```python
        if self.opponent_type != OPPONENT_CPU:
            p2_gap = max(0, self.p1.score - self.p2.score)
            self.p2_smash_meter = min(1.0, self.p2_smash_meter + (SMASH_BASE_CHARGE_RATE + p2_gap * SMASH_PER_POINT_CHARGE) * dt)
            if self.p2_smash_meter >= 1.0:
                self.p2_smash_ready = True
```

Replace with:

```python
        if self.opponent_type != OPPONENT_CPU or (self.cpu and self.cpu.smash_enabled):
            p2_gap = max(0, self.p1.score - self.p2.score)
            self.p2_smash_meter = min(1.0, self.p2_smash_meter + (SMASH_BASE_CHARGE_RATE + p2_gap * SMASH_PER_POINT_CHARGE) * dt)
            if self.p2_smash_meter >= 1.0:
                self.p2_smash_ready = True
```

- [ ] **Step 4: Add the CPU smash activation call in `_update_playing`**

Find this line in `_update_playing` (around line 395):

```python
        self._update_smash_meters(dt)
```

Add the CPU smash check directly after it:

```python
        self._update_smash_meters(dt)
        if self.cpu is not None and self.cpu.should_smash(self.balls[0], self.p1, self.p2_smash_ready):
            self._activate_smash(2)
```

- [ ] **Step 5: Fix HUD passthrough in `_draw`**

Find these two lines in `_draw` (around line 543):

```python
            renderer.draw_hud(
                game_surf, self.p1, self.p2, self.font_large, self.font_small,
                self.game_mode,
                self.time_left if self.game_mode == MODE_TIMED else None,
                (self.p1.sets_won, self.p2.sets_won) if self.game_mode == MODE_BEST_OF_3 else None,
                self.p1_smash_meter, 0.0 if is_cpu else self.p2_smash_meter,
                self.p1_smash_ready, False if is_cpu else self.p2_smash_ready,
                self.smash_pulse_t,
                cpu_mode=is_cpu,
            )
```

Replace with:

```python
            cpu_smash_on = is_cpu and self.cpu is not None and self.cpu.smash_enabled
            p2_smash_val = self.p2_smash_meter if (not is_cpu or cpu_smash_on) else 0.0
            p2_ready_val = self.p2_smash_ready if (not is_cpu or cpu_smash_on) else False
            renderer.draw_hud(
                game_surf, self.p1, self.p2, self.font_large, self.font_small,
                self.game_mode,
                self.time_left if self.game_mode == MODE_TIMED else None,
                (self.p1.sets_won, self.p2.sets_won) if self.game_mode == MODE_BEST_OF_3 else None,
                self.p1_smash_meter, p2_smash_val,
                self.p1_smash_ready, p2_ready_val,
                self.smash_pulse_t,
                cpu_mode=is_cpu,
            )
```

- [ ] **Step 6: Run all game logic tests**

```bash
python -m pytest tests/test_game_logic.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Run full test suite**

```bash
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/game.py tests/test_game_logic.py
git commit -m "feat: gate and fire CPU smash meter for HARD/INSANE difficulty"
```

---

### Task 3: renderer.py — CPU-safe READY! label

**Files:**
- Modify: `src/renderer.py`

- [ ] **Step 1: Fix `draw_hud` to derive p2 shift label**

In `draw_hud` (around line 95), find:

```python
    if p2.active_powerup:
        _draw_powerup_hud(surface, p2, font_small, 7 * SCREEN_W // 8, P2_COLOR)
    else:
        _draw_smash_meter(surface, 7 * SCREEN_W // 8, p2_smash, p2_ready, smash_pulse_t,
                          P2_COLOR, "[RSHIFT]", font_small)
```

Replace with:

```python
    if p2.active_powerup:
        _draw_powerup_hud(surface, p2, font_small, 7 * SCREEN_W // 8, P2_COLOR)
    else:
        p2_shift = "" if cpu_mode else "[RSHIFT]"
        _draw_smash_meter(surface, 7 * SCREEN_W // 8, p2_smash, p2_ready, smash_pulse_t,
                          P2_COLOR, p2_shift, font_small)
```

- [ ] **Step 2: Fix `_draw_smash_meter` ready label to strip trailing space**

Find in `_draw_smash_meter` (around line 116):

```python
        label_txt = font_small.render(f"READY! {shift_label}", True, ACCENT_COLOR)
```

Replace with:

```python
        label_txt = font_small.render(f"READY! {shift_label}".strip(), True, ACCENT_COLOR)
```

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/renderer.py
git commit -m "fix: show clean READY! label for CPU smash meter in HUD"
```
