# Menu Polish Design — 2026-06-06

## Goal

Improve the feel of all menu and transition screens in py-pong without adding new game modes or restructuring the codebase. Three areas of work: animated backgrounds, screen-transition fades, and reactive menu item animations.

## Approach

Option A — renderer extension. All additions go inside `src/renderer.py` and `src/effects.py`. No new files. Game state that drives animations is held on `Game` and passed to renderer functions. Consistent with how `ScreenShake` and `ParticleSystem` are already managed.

---

## Section 1: Animated Background (MenuParticleField)

A pool of ~60 small neon dots that drift slowly across the menu screen.

**State** — held on `Game` as `self.menu_particles: list[dict]`, each dict:
```
{ "pos": Vector2, "vel": Vector2, "phase": float, "color": tuple, "radius": int }
```
- `vel`: random direction at 15–40 px/s
- `phase`: random offset for opacity pulse
- `color`: randomly chosen from `P1_COLOR` or `P2_COLOR`
- `radius`: 2–4px

**Behavior:**
- Initialized in `Game.__init__` once.
- Advanced in `_update_menu(dt)`: `pos += vel * dt`, wrap at screen edges, no reset needed.
- `renderer.draw_menu()` gains a `menu_particles` parameter and draws each dot with `alpha = int(160 + 80 * sin(hover_t + phase))` on a per-surface draw using `pygame.draw.circle` on the background surface.
- The existing `menu_ball` animation stays (subtle background ornament).

---

## Section 2: Screen Transitions (TransitionManager)

**Location:** `src/effects.py` — new class `TransitionManager`.

**Interface:**
```python
class TransitionManager:
    def start(self, callback: Callable, duration: float = 0.25): ...
    def update(self, dt: float): ...
    def draw(self, surf: pygame.Surface): ...
    @property
    def blocking(self) -> bool: ...  # True while a transition is in progress
```

**States:** `idle → fade_out → fade_in → idle`

- `fade_out`: black overlay alpha increases from 0 → 255 over `duration` seconds. At completion, `callback()` is invoked (this is where `self.state` actually changes in `Game`).
- `fade_in`: alpha decreases from 255 → 0 over `duration` seconds.
- `draw()` blits a black `pygame.Surface` at the current alpha on top of `game_surf`.

**Integration in `Game`:**
- `self.transition = TransitionManager()` in `__init__`.
- All direct `self.state = ...` assignments in event handlers are replaced with `self.transition.start(lambda: setattr(self, 'state', NEW_STATE))`.
- `_update()` calls `self.transition.update(dt)`.
- `_draw()` calls `self.transition.draw(game_surf)` as the final blit before `screen.blit(game_surf, offset)`.
- While `transition.blocking` is True, event handlers skip (no double-trigger during fade).

---

## Section 3: Menu Item Animations

**State** — `self.menu_hover_t: float = 0.0` on `Game`. Advanced in `_update_menu(dt)`, reset to 0.0 on any selection change. Reused for `STATE_DIFFICULTY` and `STATE_MODE_SELECT` screens (same field, same pattern).

**Effects applied to the selected item:**
1. **Glow bar pulse** — the underline/highlight bar width = `base_w + 8 * sin(hover_t * 3)`.
2. **Text scale** — selected item rendered 8% larger. Implementation: render text to a temp surface, `pygame.transform.smoothscale` to 108%.
3. **Color breathe** — selected item color interpolated toward `WHITE` by `0.15 * (0.5 + 0.5 * sin(hover_t * 2))`.

**Non-selected items:** drawn at 60% alpha (via a per-surface alpha set before blitting).

The same rendering helpers are reused for `draw_difficulty_select` and `draw_mode_select`.

---

## Files Changed

| File | Change |
|------|--------|
| `src/effects.py` | Add `TransitionManager` class (~40 lines) |
| `src/game.py` | Add `menu_particles` init, advance in `_update_menu`, wire `TransitionManager`, replace direct `state=` assignments (~15 sites), pass `menu_hover_t` to renderer |
| `src/renderer.py` | Update `draw_menu`, `draw_difficulty_select`, `draw_mode_select` to accept and use `menu_particles`, `hover_t`, and render item animations |
| `src/constants.py` | No changes required |

---

## Out of Scope

- Slide or wipe transitions (fade only per design decision)
- Sound effects on menu hover
- Changes to gameplay, power-ups, or game modes
- New files or scene classes
