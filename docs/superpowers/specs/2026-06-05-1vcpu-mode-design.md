# 1vCPU Mode — Design Spec
**Date:** 2026-06-05
**Status:** Approved

---

## Overview

Add a single-player mode where P1 (human, left side) competes against a CPU-controlled P2 (right side). The main menu is restructured to offer `1v1` and `1vCPU` as the first choice. Selecting `1vCPU` routes through a new difficulty screen before reaching the existing mode select. The CPU AI uses a reaction-delay + speed model across four difficulty tiers.

---

## Menu Flow

```
MAIN MENU
├── 1v1   → MODE SELECT → GAME
└── 1v CPU → DIFFICULTY → MODE SELECT → GAME
    QUIT
```

**Back-navigation:**
- ESC on Difficulty → Main Menu
- ESC on Mode Select → Difficulty (if CPU mode) or Main Menu (if 1v1)

---

## State Machine Changes

New state added: `STATE_DIFFICULTY = "difficulty"`

Full sequence:
```
STATE_MENU → STATE_DIFFICULTY* → STATE_MODE_SELECT → STATE_PLAYING → STATE_PAUSED → STATE_GAME_OVER → STATE_MENU
```
*`STATE_DIFFICULTY` only inserted when `opponent_type == OPPONENT_CPU`

New constants in `src/constants.py`:
```python
STATE_DIFFICULTY = "difficulty"
OPPONENT_HUMAN = "human"
OPPONENT_CPU   = "cpu"
```

---

## Screen Designs

### Main Menu
Options: `1v1`, `1v CPU`, `QUIT` (replaces old `PLAY` / `QUIT`).
Navigation: Up/Down arrows, Enter to confirm. Same neon aesthetic as existing menu.

### Difficulty Select Screen
Appears only after choosing `1v CPU`. Four options with colour-coded labels:

| Option  | Label colour |
|---------|-------------|
| EASY    | `#69ff47` (green) |
| MEDIUM  | `#ffd740` (yellow) |
| HARD    | `#ff6d00` (orange) |
| INSANE  | `#ff1744` (red) |

ESC backs out to Main Menu. Enter confirms and proceeds to Mode Select.

### Mode Select (unchanged)
No changes to existing options (First to 11, Timed, Best of 3).
When in CPU mode, a small dim label at the bottom of the screen shows: `1vCPU · HARD` (or whichever difficulty was selected), so the player has context.

---

## CPU AI — `CPUController`

Lives in new file `src/cpu.py`.

### Behaviour Rules
1. **Tracks ball only when it's approaching** — when `ball.vel.x > 0` (ball moving right toward CPU), the CPU actively updates its target Y. When ball moves away, the CPU drifts toward screen center Y. This creates natural gaps for the player to exploit.
2. **Reaction delay** — the CPU stores a `reaction_timer`. It only refreshes its `target_y` when the timer hits zero; then the timer resets. Between refreshes it keeps moving toward the last known `target_y`.
3. **Dead zone** — CPU stops adjusting if its paddle center is already within `dead_zone` pixels of `target_y`, preventing jitter.
4. **Speed cap** — paddle velocity is clamped to `max_speed` px/s per difficulty.

### Difficulty Parameters

| Difficulty | `max_speed` (px/s) | `reaction_delay` (s) | `dead_zone` (px) |
|------------|-------------------|----------------------|-----------------|
| EASY       | 180               | 0.35                 | 20              |
| MEDIUM     | 320               | 0.18                 | 15              |
| HARD       | 480               | 0.06                 | 10              |
| INSANE     | 650               | 0.00                 | 5               |

### Interface

```python
class CPUController:
    def __init__(self, difficulty: str): ...
    def update(self, dt: float, ball: Ball, paddle: Paddle): ...
```

`update()` mutates `paddle.vel.y` directly — the same attribute keyboard input writes. No changes to `Paddle` or `Ball` classes.

---

## File Changes

| File | Description |
|------|-------------|
| `src/constants.py` | Add `STATE_DIFFICULTY`, `OPPONENT_HUMAN`, `OPPONENT_CPU`; add `CPU_PARAMS` dict keyed by difficulty name |
| `src/cpu.py` | **New.** `CPUController` class |
| `src/game.py` | Add `self.opponent_type`, `self.cpu_difficulty`, `self.cpu` (CPUController instance); update `_update_menu` input for 3 options; add `_update_difficulty` and `_draw_difficulty` handlers; wire `self.cpu.update()` into `_update_playing` instead of P2 keyboard input when in CPU mode; update `_reset_to_menu` to clear CPU state; update ESC back-nav on mode select |
| `src/renderer.py` | Add `draw_difficulty_select()`; update `draw_menu()` for 3 options; add difficulty context label on `draw_mode_select()` |
| `tests/test_cpu.py` | **New.** Test: CPU drifts to center when ball moves away; reaction delay blocks immediate target update; speed is capped per difficulty |

---

## Verification

1. `python3 main.py` — main menu shows `1v1 / 1v CPU / QUIT`
2. Select `1v CPU` → difficulty screen appears with 4 colour-coded options
3. Select a difficulty → mode select appears with difficulty label at bottom
4. Start game → CPU paddle moves, reacts with visible delay on Easy, near-instant on Insane
5. On Easy: ball should pass CPU paddle occasionally; on Insane: CPU should rarely miss
6. ESC from difficulty → returns to main menu
7. ESC from mode select (CPU mode) → returns to difficulty screen
8. `python3 -m pytest tests/test_cpu.py` — all tests pass
