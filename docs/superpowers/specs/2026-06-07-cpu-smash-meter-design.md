# CPU Smash Meter Design — 2026-06-07

## Goal

Enable the CPU opponent to charge and fire the Final Smash meter on HARD and INSANE difficulty levels. HARD fires immediately on full charge; INSANE fires opportunistically when the ball is incoming and the player is off-center. The meter is visible to the human player on both difficulties.

## Approach

Option A — CPUController owns the smash decision. All CPU smash logic lives in `src/cpu.py` alongside existing movement logic. `game.py` gates charging and calls `cpu.should_smash()` each frame. No new files.

---

## Section 1: CPUController (`src/cpu.py`)

Two new fields added in `__init__`:

```python
self.smash_enabled: bool = difficulty in ("HARD", "INSANE")
self._insane_strategic: bool = difficulty == "INSANE"
```

New method:

```python
def should_smash(self, ball: Ball, player_paddle: Paddle, meter_ready: bool) -> bool:
    if not self.smash_enabled or not meter_ready:
        return False
    if not self._insane_strategic:
        return True  # HARD: fire immediately when full
    # INSANE: ball heading toward CPU and player visibly off-center
    field_center_y = (SCREEN_H + HUD_HEIGHT) / 2.0
    player_off_center = abs(player_paddle.pos.y - field_center_y) > 80
    return ball.vel.x > 0 and player_off_center
```

- `ball.vel.x > 0` — ball moving right, toward the CPU's side (P2)
- 80 px off-center threshold — roughly one paddle-height, ensures the player is visibly displaced before INSANE capitalises

EASY and MEDIUM CPUs: `smash_enabled = False`, meter never charges, HUD shows nothing (existing behaviour unchanged).

---

## Section 2: game.py (`src/game.py`)

**`_update_smash_meters`** — replace the hard `if self.opponent_type != OPPONENT_CPU` guard:

```python
if self.opponent_type != OPPONENT_CPU or (self.cpu and self.cpu.smash_enabled):
    # existing p2 charge block (unchanged)
```

**`_update_playing`** — after `_update_smash_meters(dt)`, add one call:

```python
if self.cpu is not None and self.cpu.should_smash(self.balls[0], self.p1, self.p2_smash_ready):
    self._activate_smash(2)
```

`_activate_smash(2)` is already implemented and handles BIG_PADDLE + SMALL_OPPONENT + SFX + meter reset.

**`_draw` HUD passthrough** — replace hardcoded suppressions with:

```python
cpu_smash_on = is_cpu and self.cpu is not None and self.cpu.smash_enabled
p2_smash_val = self.p2_smash_meter if (not is_cpu or cpu_smash_on) else 0.0
p2_ready_val = self.p2_smash_ready if (not is_cpu or cpu_smash_on) else False
```

Pass `p2_smash_val` and `p2_ready_val` to `draw_hud` instead of the inline `0.0 if is_cpu` expressions.

---

## Section 3: renderer.py (`src/renderer.py`)

In `draw_hud`, derive the P2 shift label before calling `_draw_smash_meter`:

```python
p2_shift = "" if cpu_mode else "[RSHIFT]"
_draw_smash_meter(surface, 7 * SCREEN_W // 8, p2_smash, p2_ready, smash_pulse_t,
                  P2_COLOR, p2_shift, font_small)
```

In `_draw_smash_meter`, tighten the ready-state label so an empty `shift_label` produces clean output:

```python
label_txt = font_small.render(f"READY! {shift_label}".strip(), True, ACCENT_COLOR)
```

CPU P2 shows `"READY!"` as a warning to the player when the meter is full, instead of `"READY! [RSHIFT]"`.

---

## Files Changed

| File | Change |
|------|--------|
| `src/cpu.py` | Add `smash_enabled`, `_insane_strategic` fields; add `should_smash()` method |
| `src/game.py` | Gate p2 charging on `cpu.smash_enabled`; call `cpu.should_smash()` in `_update_playing`; fix HUD passthrough in `_draw` |
| `src/renderer.py` | Derive `p2_shift` label in `draw_hud`; strip trailing space in `_draw_smash_meter` ready label |

---

## Out of Scope

- EASY and MEDIUM CPU smash (disabled by design)
- CPU smash strategy based on score gap or timing window
- Any changes to smash meter charge rate or duration
- Changes to 1v1 human smash behaviour
