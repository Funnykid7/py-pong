# py-pong — Smash Meter & Audio Design Spec
**Date:** 2026-06-04
**Status:** Approved

---

## Overview

Two additions to the existing py-pong game:

1. **Main theme music** — loops on the menu screens, fades out when gameplay begins.
2. **Ball hit sound** — plays on every paddle collision.
3. **Final Smash meter** — replaces the old field-spawn power-up system. Each player charges an independent meter that fills faster the further behind they are. When full, pressing their Shift key activates a short powerful effect (Big Paddle for self, Small Paddle for opponent).

---

## Audio

### New files
| Source | Destination | Usage |
|--------|-------------|-------|
| `~/Downloads/main theme.mp3` | `assets/sounds/main theme.mp3` | Menu / Mode Select BGM |
| `~/Downloads/ball hit.mp3` | `assets/sounds/ball hit.mp3` | Paddle collision SFX |

### Behaviour
- **Main theme:** loaded via `pygame.mixer.music`. Starts playing (`pygame.mixer.music.play(-1)`) when the game enters `STATE_MENU` or `STATE_MODE_SELECT` (including when returning from game over). Fades out (`pygame.mixer.music.fadeout(500)`) the moment the game transitions to `STATE_PLAYING`. Does not play during `STATE_PLAYING`, `STATE_PAUSED`, or `STATE_GAME_OVER`.
- **Ball hit:** loaded as a `pygame.mixer.Sound` object under key `"hit"` in `self.sfx`. Called via `_play_sfx("hit")` on every paddle collision — replaces the existing silent placeholder.
- Both files use the existing `try/except` silent-fallback pattern in `_init_audio`. Missing files are skipped without crashing.

---

## Final Smash Meter

### What changes
- **Removed from `game.py`:** `self.powerup`, `self.powerup_spawn_timer`, `_update_powerup()`, `_activate_powerup()`, all `PowerUp` / `PowerUpType` references in the game loop.
- **Kept in `entities.py`:** `PowerUp` and `PowerUpType` classes and their tests remain (they pass cleanly, and removing them is out of scope).
- **Added to `game.py`:** `self.p1_smash_meter: float`, `self.p2_smash_meter: float`, `self.p1_smash_ready: bool`, `self.p2_smash_ready: bool`, plus `_update_smash_meters(dt)` and `_activate_smash(player)`.

### Charge rate formula
```
gap = max(0, opponent_score - my_score)
rate = BASE_CHARGE_RATE + gap × PER_POINT_CHARGE
```

**Constants (added to `src/constants.py`):**
```python
SMASH_BASE_CHARGE_RATE  = 0.025   # fills in ~40s when tied
SMASH_PER_POINT_CHARGE  = 0.020   # +0.02/s per point behind
SMASH_DURATION          = 7.0     # seconds the BIG/SMALL effect lasts after activation
```

Fill-time reference:
| Points behind | Fill time |
|---------------|-----------|
| 0 (tied/ahead) | ~40s |
| 1 | ~22s |
| 3 | ~12s |
| 5 | ~8s |

### Activation
- Meter caps at 1.0. Flag `p1_smash_ready` / `p2_smash_ready` set to `True`.
- **P1:** Left Shift (`pygame.K_LSHIFT`) — handled in `_handle_playing_event`.
- **P2:** Right Shift (`pygame.K_RSHIFT`) — handled in `_handle_playing_event`.
- Key must be a `KEYDOWN` event (not held) to prevent repeated activation spam.

### Effect on activation
| Target | Effect |
|--------|--------|
| Activating player | `BIG_PADDLE` — height becomes `PADDLE_H × 1.5` for `SMASH_DURATION` seconds |
| Opponent | `SMALL_OPPONENT` — height becomes `PADDLE_H × 0.6` for `SMASH_DURATION` seconds |

Both use the existing `Paddle.activate_powerup()` / `Paddle.deactivate_powerup()` methods unchanged.

### Post-activation
- Meter resets to `0.0`.
- `smash_ready` flag set to `False`.
- Meter begins recharging immediately at the current gap rate.

### Reset on new match / new set
- Both meters reset to `0.0` in `_start_match()` and after a set win in `_check_set_win()`.

---

## HUD — Meter Bar

Drawn inside `draw_hud()` in `src/renderer.py` via a new helper `_draw_smash_meter()`.

### Layout
- **Position:** below each player's score, vertically between the score digits and the bottom of the HUD bar.
- **Size:** 100px wide × 6px tall (same height as the existing power-up countdown bar).
- **Centered:** horizontally under the score (`SCREEN_W // 4` for P1, `3 * SCREEN_W // 4` for P2).

### States
| State | Bar color | Label | Label color |
|-------|-----------|-------|-------------|
| Charging | P1_COLOR / P2_COLOR | `"SMASH"` | Player color |
| Ready (`meter >= 1.0`) | Pulsing (alpha oscillates via `sin(pulse_t × 6)`) | `"READY! [LSHIFT]"` / `"READY! [RSHIFT]"` | `ACCENT_COLOR` (yellow) |

`self.smash_pulse_t` is a dedicated float on `Game` that increments by `dt` every frame (same pattern as the existing `gameover_pulse`).

### Active-effect bar
The existing `_draw_powerup_hud()` helper still renders a countdown bar + label when `BIG_PADDLE` or `SMALL_OPPONENT` is active on a paddle — this is unchanged.

---

## Files Changed

| File | Change |
|------|--------|
| `assets/sounds/main theme.mp3` | New — copied from Downloads |
| `assets/sounds/ball hit.mp3` | New — copied from Downloads |
| `src/constants.py` | Add `SMASH_BASE_CHARGE_RATE`, `SMASH_PER_POINT_CHARGE`, `SMASH_DURATION` |
| `src/game.py` | Remove old power-up field system; add smash meter state, charge logic, Shift key handling, `_activate_smash()`, music management |
| `src/renderer.py` | Add `_draw_smash_meter()` helper; call it from `draw_hud()` |
| `tests/test_game_logic.py` | Add smash meter tests: charge rate, gap scaling, activation effect, reset |

---

## Out of Scope

- No AI / single-player mode.
- No visual flash or screen shake on smash activation beyond what already fires from `BIG_PADDLE` / `SMALL_OPPONENT` paddle hit.
- `PowerUp` / `PowerUpType` entities and their tests are untouched.
