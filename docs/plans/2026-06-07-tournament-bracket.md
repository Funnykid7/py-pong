# Tournament Bracket Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a configurable 4/8-player single-elimination tournament mode with CPU slot support, a bracket display screen, and per-match mode selection.

**Architecture:** A new pygame-free `TournamentManager` class (mirroring `CPUController`) owns all bracket state. `Game` holds `self.tournament: TournamentManager | None` and two new states (`STATE_TOURNAMENT_SETUP`, `STATE_BRACKET`). The existing play loop runs unchanged; `_end_match()` intercepts the result when a tournament is active.

**Tech Stack:** Python 3.12, pygame-ce, pytest. No new dependencies.

**Spec:** `docs/specs/2026-06-07-tournament-bracket-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/tournament.py` | `Slot`, `Match`, `TournamentManager` — zero pygame |
| Create | `tests/test_tournament.py` | Unit tests for `TournamentManager` |
| Modify | `src/constants.py` | Add `STATE_TOURNAMENT_SETUP`, `STATE_BRACKET`, `TOURNAMENT_SLOT_TYPES` |
| Modify | `src/renderer.py` | Add `draw_tournament_setup()`, `draw_bracket()` and helpers |
| Modify | `src/game.py` | New state fields, event/update/draw dispatch, `_end_match()` guard |

---

## Task 1 — Constants

**Files:**
- Modify: `src/constants.py`

- [ ] **Step 1: Add the two new state constants and slot-type table**

Open `src/constants.py` and append at the bottom (after the existing `CPU_PARAMS` block):

```python
# Tournament
STATE_TOURNAMENT_SETUP = "tournament_setup"
STATE_BRACKET = "bracket"

# Each entry: (display_label, is_cpu, difficulty)
TOURNAMENT_SLOT_TYPES = [
    ("HUMAN",       False, "EASY"),
    ("CPU-EASY",    True,  "EASY"),
    ("CPU-MEDIUM",  True,  "MEDIUM"),
    ("CPU-HARD",    True,  "HARD"),
    ("CPU-INSANE",  True,  "INSANE"),
]
```

- [ ] **Step 2: Verify the constants import cleanly**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -c "from src.constants import STATE_TOURNAMENT_SETUP, STATE_BRACKET, TOURNAMENT_SLOT_TYPES; print(TOURNAMENT_SLOT_TYPES)"
```

Expected output:
```
[('HUMAN', False, 'EASY'), ('CPU-EASY', True, 'EASY'), ('CPU-MEDIUM', True, 'MEDIUM'), ('CPU-HARD', True, 'HARD'), ('CPU-INSANE', True, 'INSANE')]
```

- [ ] **Step 3: Commit**

```bash
git add src/constants.py
git commit -m "feat: add STATE_TOURNAMENT_SETUP, STATE_BRACKET, TOURNAMENT_SLOT_TYPES"
```

---

## Task 2 — TournamentManager (TDD)

**Files:**
- Create: `src/tournament.py`
- Create: `tests/test_tournament.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_tournament.py`:

```python
import pytest
from src.tournament import Slot, Match, TournamentManager


def _human(label: str) -> Slot:
    return Slot(label=label, is_cpu=False, difficulty="EASY")


def _cpu(difficulty: str) -> Slot:
    return Slot(label=f"CPU-{difficulty}", is_cpu=True, difficulty=difficulty)


def _4player() -> TournamentManager:
    return TournamentManager([_human("P1"), _human("P2"), _human("P3"), _human("P4")])


def _8player() -> TournamentManager:
    return TournamentManager([_human(f"P{i+1}") for i in range(8)])


# ── 4-player ──────────────────────────────────────────────────────────────────

def test_4player_first_match_is_slot0_vs_slot1():
    tm = _4player()
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 1


def test_4player_second_match_is_slot2_vs_slot3():
    tm = _4player()
    tm.record_result(0)
    m = tm.next_match()
    assert m.slot_a == 2 and m.slot_b == 3


def test_4player_winner_propagates_to_final_slot_a():
    tm = _4player()
    tm.record_result(1)  # P2 wins semi 1
    assert tm.rounds[1][0].slot_a == 1


def test_4player_winner_propagates_to_final_slot_b():
    tm = _4player()
    tm.record_result(0)  # P1 wins semi 1
    tm.record_result(3)  # P4 wins semi 2
    assert tm.rounds[1][0].slot_b == 3


def test_4player_final_match_uses_propagated_slots():
    tm = _4player()
    tm.record_result(0)  # P1 wins semi 1
    tm.record_result(2)  # P3 wins semi 2
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 2


def test_4player_not_complete_before_final():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(2)
    assert tm.is_complete() is False


def test_4player_complete_after_final():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(2)
    tm.record_result(0)  # P1 wins final
    assert tm.is_complete() is True


def test_4player_champion_after_final():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(3)
    tm.record_result(0)  # P1 wins final
    assert tm.champion().label == "P1"


def test_next_match_returns_none_when_complete():
    tm = _4player()
    tm.record_result(0)
    tm.record_result(2)
    tm.record_result(0)
    assert tm.next_match() is None


def test_champion_returns_none_when_not_complete():
    tm = _4player()
    assert tm.champion() is None


# ── 8-player ──────────────────────────────────────────────────────────────────

def test_8player_has_three_rounds():
    tm = _8player()
    assert len(tm.rounds) == 3


def test_8player_round0_has_4_matches():
    tm = _8player()
    assert len(tm.rounds[0]) == 4


def test_8player_first_match_is_slot0_vs_slot1():
    tm = _8player()
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 1


def test_8player_advances_to_semifinal_after_4_qf_results():
    tm = _8player()
    for winner in [0, 2, 4, 6]:
        tm.record_result(winner)
    assert tm.round_idx == 1


def test_8player_sf_match0_uses_qf_winners():
    tm = _8player()
    for winner in [0, 2, 4, 6]:
        tm.record_result(winner)
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 2


def test_8player_complete_tournament_champion():
    tm = _8player()
    for winner in [0, 2, 4, 6]:   # QF: P1,P3,P5,P7 win
        tm.record_result(winner)
    tm.record_result(0)            # SF: P1 wins
    tm.record_result(4)            # SF: P5 wins
    tm.record_result(0)            # Final: P1 wins
    assert tm.is_complete() is True
    assert tm.champion().label == "P1"


# ── CPU slot ──────────────────────────────────────────────────────────────────

def test_cpu_slot_in_bracket():
    tm = TournamentManager([_human("P1"), _cpu("HARD"), _human("P2"), _cpu("INSANE")])
    tm.record_result(0)  # P1 beats CPU-HARD
    tm.record_result(2)  # P2 beats CPU-INSANE
    m = tm.next_match()
    assert m.slot_a == 0 and m.slot_b == 2
```

- [ ] **Step 2: Run tests — confirm they all fail**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/test_tournament.py -v 2>&1 | head -20
```

Expected: `ERROR` or `ModuleNotFoundError: No module named 'src.tournament'`

- [ ] **Step 3: Implement `src/tournament.py`**

Create `src/tournament.py`:

```python
from dataclasses import dataclass, field


@dataclass
class Slot:
    label: str
    is_cpu: bool
    difficulty: str  # EASY/MEDIUM/HARD/INSANE — ignored when is_cpu is False


@dataclass
class Match:
    slot_a: int        # index into TournamentManager.slots
    slot_b: int
    winner: int | None = None  # slot index of winner; None = not yet played


class TournamentManager:
    def __init__(self, slots: list[Slot]):
        assert len(slots) in (4, 8), f"Tournament requires 4 or 8 slots, got {len(slots)}"
        self.size: int = len(slots)
        self.slots: list[Slot] = slots
        self.rounds: list[list[Match]] = self._build_rounds()
        self.round_idx: int = 0
        self.match_idx: int = 0

    def _build_rounds(self) -> list[list[Match]]:
        first = [Match(i * 2, i * 2 + 1) for i in range(self.size // 2)]
        rounds: list[list[Match]] = [first]
        n_more = {4: 1, 8: 2}[self.size]
        for _ in range(n_more):
            prev_len = len(rounds[-1])
            rounds.append([Match(-1, -1) for _ in range(prev_len // 2)])
        return rounds

    def next_match(self) -> Match | None:
        if self.is_complete():
            return None
        return self.rounds[self.round_idx][self.match_idx]

    def record_result(self, winner_slot_idx: int) -> None:
        match = self.rounds[self.round_idx][self.match_idx]
        match.winner = winner_slot_idx
        # Propagate to next round
        next_round_idx = self.round_idx + 1
        if next_round_idx < len(self.rounds):
            next_match_pos = self.match_idx // 2
            next_match = self.rounds[next_round_idx][next_match_pos]
            if self.match_idx % 2 == 0:
                next_match.slot_a = winner_slot_idx
            else:
                next_match.slot_b = winner_slot_idx
        # Advance pointer
        self.match_idx += 1
        if self.match_idx >= len(self.rounds[self.round_idx]):
            self.round_idx += 1
            self.match_idx = 0

    def is_complete(self) -> bool:
        return all(m.winner is not None for m in self.rounds[-1])

    def champion(self) -> Slot | None:
        if not self.is_complete():
            return None
        return self.slots[self.rounds[-1][0].winner]
```

- [ ] **Step 4: Run tests — confirm they all pass**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/test_tournament.py -v
```

Expected: all 20 tests PASSED.

- [ ] **Step 5: Run full test suite to confirm no regressions**

```bash
python3 -m pytest tests/ -v
```

Expected: all existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/tournament.py tests/test_tournament.py
git commit -m "feat: add TournamentManager with 4/8-player single-elimination support"
```

---

## Task 3 — Menu "TOURNAMENT" option + Setup Screen

**Files:**
- Modify: `src/renderer.py` — update `draw_menu`, add `draw_tournament_setup`
- Modify: `src/game.py` — update menu handler, add setup state fields and handler

- [ ] **Step 1: Update `draw_menu` to include 4 items**

In `src/renderer.py`, replace the `draw_menu` function:

```python
def draw_menu(surface, font_title, font_large, font_small, selected: int,
              anim_ball_pos: tuple, menu_particles: list | None = None, hover_t: float = 0.0):
    draw_background(surface)
    if menu_particles is not None:
        _draw_menu_particles(surface, menu_particles, hover_t)
    draw_glow(surface, ACCENT_COLOR, (int(anim_ball_pos[0]), int(anim_ball_pos[1])), BALL_SIZE // 2)
    title = font_title.render("PY-PONG", True, P1_COLOR)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 140))
    for i, opt in enumerate(["1 v 1", "1 v CPU", "TOURNAMENT", "QUIT"]):
        y = 285 + i * 75
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

- [ ] **Step 2: Add `draw_tournament_setup` to `src/renderer.py`**

Append at the end of `src/renderer.py`:

```python
def draw_tournament_setup(surface, font_large, font_small, size: int,
                          slot_type_indices: list, selected_row: int,
                          menu_particles: list | None, hover_t: float):
    from src.constants import TOURNAMENT_SLOT_TYPES, DIFFICULTY_COLORS
    draw_background(surface)
    if menu_particles is not None:
        _draw_menu_particles(surface, menu_particles, hover_t)

    title = font_large.render("TOURNAMENT SETUP", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 100))

    # Size toggle
    size_lbl = font_small.render("PLAYERS:", True, (120, 120, 140))
    surface.blit(size_lbl, (SCREEN_W // 2 - 110, 170))
    for idx, n in enumerate([4, 8]):
        is_active = (n == size)
        col = ACCENT_COLOR if is_active else (60, 60, 80)
        box = pygame.Rect(SCREEN_W // 2 + idx * 58 - 10, 165, 46, 26)
        pygame.draw.rect(surface, (15, 15, 25), box, border_radius=4)
        pygame.draw.rect(surface, col, box, width=2, border_radius=4)
        t = font_small.render(str(n), True, col)
        surface.blit(t, (box.centerx - t.get_width() // 2, box.centery - t.get_height() // 2))
    tab_hint = font_small.render("TAB to toggle", True, (50, 50, 70))
    surface.blit(tab_hint, (SCREEN_W // 2 + 120, 170))

    # Slot rows
    row_h = 44
    y0 = 220
    for i in range(size):
        y = y0 + i * row_h
        is_sel = (i == selected_row)
        type_idx = slot_type_indices[i]
        type_label, is_cpu, difficulty = TOURNAMENT_SLOT_TYPES[type_idx]
        slot_col = DIFFICULTY_COLORS[difficulty] if is_cpu else P1_COLOR
        border_col = ACCENT_COLOR if is_sel else (55, 55, 70)

        row_lbl = font_small.render(f"P{i + 1}", True, (90, 90, 110))
        surface.blit(row_lbl, (SCREEN_W // 2 - 175, y + 6))

        box = pygame.Rect(SCREEN_W // 2 - 140, y, 280, 30)
        pygame.draw.rect(surface, (12, 12, 20), box, border_radius=4)
        pygame.draw.rect(surface, border_col, box, width=2, border_radius=4)

        inner_col = slot_col if is_sel else (70, 70, 90)
        arrows = "◀  " if is_sel else "   "
        arrows_r = "  ▶" if is_sel else "   "
        txt = font_small.render(f"{arrows}{type_label}{arrows_r}", True, inner_col)
        surface.blit(txt, (box.centerx - txt.get_width() // 2,
                           box.centery - txt.get_height() // 2))

    start_y = y0 + size * row_h + 16
    start_txt = font_small.render("START TOURNAMENT  [ENTER]", True, (110, 110, 130))
    surface.blit(start_txt, (SCREEN_W // 2 - start_txt.get_width() // 2, start_y))
    esc_txt = font_small.render("ESC  Back", True, (55, 55, 75))
    surface.blit(esc_txt, (SCREEN_W // 2 - esc_txt.get_width() // 2, SCREEN_H - 36))
```

- [ ] **Step 3: Add tournament setup fields to `Game.__init__`**

In `src/game.py`, inside `Game.__init__`, after the existing `self.cpu: CPUController | None = None` line (~line 74), add:

```python
        # Tournament
        self.tournament: "TournamentManager | None" = None
        self._tournament_match_slots: tuple[int, int] = (0, 1)
        self._ts_size: int = 4
        self._ts_slots: list[int] = [0, 0, 2, 2]
        self._ts_row: int = 0
```

- [ ] **Step 4: Update the menu imports in `src/game.py`**

In `src/game.py`, update the import from `src.constants` to include the new state constants:

```python
from src.constants import (
    SCREEN_W, SCREEN_H, FPS, HUD_HEIGHT, BG_COLOR,
    PADDLE_W, PADDLE_H, PADDLE_MARGIN, PADDLE_SPEED,
    BALL_SIZE, BALL_SPEED_INITIAL,
    MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED,
    TIMED_DURATION, SUDDEN_DEATH_DURATION, SET_WIN_SCORE,
    MATCH_WIN_SETS, CLASSIC_WIN_SCORE,
    STATE_MENU, STATE_MODE_SELECT, STATE_PLAYING,
    STATE_PAUSED, STATE_GAME_OVER, STATE_DIFFICULTY,
    STATE_TOURNAMENT_SETUP, STATE_BRACKET,
    OPPONENT_HUMAN, OPPONENT_CPU, DIFFICULTY_OPTIONS,
    SHAKE_HIT_TRAUMA, SHAKE_SCORE_TRAUMA,
    P1_COLOR, P2_COLOR,
    SMASH_BASE_CHARGE_RATE, SMASH_PER_POINT_CHARGE,
    TOURNAMENT_SLOT_TYPES,
)
```

- [ ] **Step 5: Update `_handle_menu_event` for 4-item menu**

Replace `_handle_menu_event` in `src/game.py`:

```python
    def _handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.menu_selected = (self.menu_selected - 1) % 4
                self.menu_hover_t = 0.0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % 4
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
                elif self.menu_selected == 2:
                    def _go_tournament():
                        self._ts_size = 4
                        self._ts_slots = [0, 0, 2, 2]
                        self._ts_row = 0
                        self.state = STATE_TOURNAMENT_SETUP
                    self.transition.start(_go_tournament)
                else:
                    self.transition.start(lambda: setattr(self, "_quit_pending", True))
```

- [ ] **Step 6: Add `_handle_tournament_setup_event` and `_start_tournament` to `Game`**

After `_handle_difficulty_event` in `src/game.py`, insert:

```python
    def _handle_tournament_setup_event(self, event):
        if event.type == pygame.KEYDOWN:
            n = self._ts_size
            if event.key in (pygame.K_UP, pygame.K_w):
                self._ts_row = (self._ts_row - 1) % n
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._ts_row = (self._ts_row + 1) % n
            elif event.key == pygame.K_LEFT:
                self._ts_slots[self._ts_row] = (
                    self._ts_slots[self._ts_row] - 1) % len(TOURNAMENT_SLOT_TYPES)
            elif event.key == pygame.K_RIGHT:
                self._ts_slots[self._ts_row] = (
                    self._ts_slots[self._ts_row] + 1) % len(TOURNAMENT_SLOT_TYPES)
            elif event.key == pygame.K_TAB:
                if self._ts_size == 4:
                    self._ts_size = 8
                    self._ts_slots.extend([2, 2, 2, 2])
                else:
                    self._ts_size = 4
                    self._ts_slots = self._ts_slots[:4]
                self._ts_row = min(self._ts_row, self._ts_size - 1)
            elif event.key == pygame.K_RETURN:
                self.transition.start(self._start_tournament)
            elif event.key == pygame.K_ESCAPE:
                self.menu_hover_t = 0.0
                self.transition.start(lambda: setattr(self, "state", STATE_MENU))

    def _start_tournament(self):
        from src.tournament import TournamentManager, Slot
        human_count = 0
        slots: list[Slot] = []
        for i, type_idx in enumerate(self._ts_slots[:self._ts_size]):
            _label, is_cpu, difficulty = TOURNAMENT_SLOT_TYPES[type_idx]
            if not is_cpu:
                human_count += 1
                label = f"P{human_count}"
            else:
                label = f"CPU-{difficulty}"
            slots.append(Slot(label=label, is_cpu=is_cpu, difficulty=difficulty))
        self.tournament = TournamentManager(slots)
        self.state = STATE_BRACKET
```

- [ ] **Step 7: Wire new states into `_handle_event`, `_update`, and `_draw`**

In `_handle_event`, update the transition-blocking guard and add dispatch cases:

```python
    def _handle_event(self, event):
        if self.transition.blocking and self.state in (
            STATE_MENU, STATE_DIFFICULTY, STATE_MODE_SELECT, STATE_GAME_OVER,
            STATE_TOURNAMENT_SETUP, STATE_BRACKET,
        ):
            return
        if self.state == STATE_MENU:
            return self._handle_menu_event(event)
        elif self.state == STATE_DIFFICULTY:
            return self._handle_difficulty_event(event)
        elif self.state == STATE_TOURNAMENT_SETUP:
            return self._handle_tournament_setup_event(event)
        elif self.state == STATE_BRACKET:
            return self._handle_bracket_event(event)
        elif self.state == STATE_MODE_SELECT:
            return self._handle_mode_select_event(event)
        elif self.state == STATE_PLAYING:
            return self._handle_playing_event(event)
        elif self.state == STATE_PAUSED:
            return self._handle_paused_event(event)
        elif self.state == STATE_GAME_OVER:
            return self._handle_gameover_event(event)
```

In `_update`, add:
```python
        elif self.state in (STATE_TOURNAMENT_SETUP, STATE_BRACKET):
            self._update_menu_particles(dt)
```
(insert this after the `elif self.state in (STATE_DIFFICULTY, STATE_MODE_SELECT):` branch)

In `_draw`, add before the `elif self.state == STATE_GAME_OVER:` branch:
```python
        elif self.state == STATE_TOURNAMENT_SETUP:
            renderer.draw_tournament_setup(
                game_surf, self.font_large, self.font_small,
                self._ts_size, self._ts_slots, self._ts_row,
                self.menu_particles, self.menu_hover_t,
            )
        elif self.state == STATE_BRACKET:
            renderer.draw_bracket(
                game_surf, self.tournament, self.font_large, self.font_small,
            )
```

- [ ] **Step 8: Add stub `_handle_bracket_event` (bracket renderer comes in Task 4)**

After `_handle_tournament_setup_event` in `src/game.py`, insert a minimal stub:

```python
    def _handle_bracket_event(self, event):
        pass  # implemented in Task 4
```

- [ ] **Step 9: Add stub `draw_bracket` to `src/renderer.py`**

Append at the end of `src/renderer.py`:

```python
def draw_bracket(surface, tournament, font_large, font_small):
    draw_background(surface)
    txt = font_small.render("BRACKET — coming soon", True, (120, 120, 140))
    surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H // 2))
```

- [ ] **Step 10: Run the test suite to confirm no regressions**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 11: Commit**

```bash
git add src/constants.py src/renderer.py src/game.py
git commit -m "feat: add Tournament menu option and setup screen"
```

---

## Task 4 — Bracket Screen

**Files:**
- Modify: `src/renderer.py` — replace stub `draw_bracket`, add helpers
- Modify: `src/game.py` — replace stub `_handle_bracket_event`, add `_end_tournament`, `_setup_tournament_match`

- [ ] **Step 1: Replace `draw_bracket` stub with full implementation in `src/renderer.py`**

Remove the stub and append these functions. `draw_bracket` comes last so helpers are defined first:

```python
def _slot_color(slot) -> tuple:
    from src.constants import DIFFICULTY_COLORS
    if not slot.is_cpu:
        return P1_COLOR
    return DIFFICULTY_COLORS[slot.difficulty]


def _is_eliminated(tournament, slot_idx: int) -> bool:
    for round_matches in tournament.rounds:
        for m in round_matches:
            if m.winner is not None:
                if (m.slot_a == slot_idx or m.slot_b == slot_idx) and m.winner != slot_idx:
                    return True
    return False


def _draw_bracket_box(surface, label: str, x: int, cy: int, w: int, h: int,
                      font, color: tuple, highlight: bool):
    rect = pygame.Rect(x, cy - h // 2, w, h)
    border_color = ACCENT_COLOR if highlight else color
    pygame.draw.rect(surface, (12, 12, 20), rect, border_radius=3)
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=3)
    txt = font.render(label, True, border_color)
    surface.blit(txt, (rect.centerx - txt.get_width() // 2,
                       rect.centery - txt.get_height() // 2))


def draw_bracket(surface, tournament, font_large, font_small):
    draw_background(surface)

    n_slots = tournament.size
    n_rounds = len(tournament.rounds)
    TOP, BOTTOM = 110, 640
    SLOT_W, SLOT_H = 120, 28
    available_h = BOTTOM - TOP

    col_width = (SCREEN_W - 160 - SLOT_W) // n_rounds
    col_xs = [80 + i * col_width for i in range(n_rounds + 1)]

    slot_ys = [TOP + (i + 0.5) * available_h / n_slots for i in range(n_slots)]

    # Compute Y-center of each match for every round
    match_cy: list[list[float]] = []
    for r in range(n_rounds):
        if r == 0:
            n_m = len(tournament.rounds[0])
            match_cy.append([(slot_ys[m * 2] + slot_ys[m * 2 + 1]) / 2 for m in range(n_m)])
        else:
            prev = match_cy[r - 1]
            n_m = len(tournament.rounds[r])
            match_cy.append([(prev[m * 2] + prev[m * 2 + 1]) / 2 for m in range(n_m)])

    next_match = tournament.next_match()

    # Draw initial slot boxes
    for i, sy in enumerate(slot_ys):
        slot = tournament.slots[i]
        eliminated = _is_eliminated(tournament, i)
        color = _slot_color(slot)
        if eliminated:
            color = tuple(max(0, c // 4) for c in color)
        is_in_next = (
            next_match is not None
            and tournament.round_idx == 0
            and tournament.match_idx < len(tournament.rounds[0])
            and (tournament.rounds[0][tournament.match_idx].slot_a == i
                 or tournament.rounds[0][tournament.match_idx].slot_b == i)
        )
        _draw_bracket_box(surface, slot.label, col_xs[0], int(sy),
                          SLOT_W, SLOT_H, font_small, color, highlight=is_in_next)

    # Draw connector lines and winner/champion boxes for each round
    for r, round_matches in enumerate(tournament.rounds):
        x_in = col_xs[r]
        x_out = col_xs[r + 1]

        for m_idx, match in enumerate(round_matches):
            cy = int(match_cy[r][m_idx])
            ya = int(slot_ys[m_idx * 2] if r == 0 else match_cy[r - 1][m_idx * 2])
            yb = int(slot_ys[m_idx * 2 + 1] if r == 0 else match_cy[r - 1][m_idx * 2 + 1])

            mid_x = x_in + SLOT_W + (x_out - x_in - SLOT_W) // 2
            line_col = (55, 55, 75)
            pygame.draw.line(surface, line_col, (x_in + SLOT_W, ya), (mid_x, ya), 1)
            pygame.draw.line(surface, line_col, (x_in + SLOT_W, yb), (mid_x, yb), 1)
            pygame.draw.line(surface, line_col, (mid_x, ya), (mid_x, yb), 1)
            pygame.draw.line(surface, line_col, (mid_x, cy), (x_out, cy), 1)

            is_final_round = (r == n_rounds - 1)
            is_next = (r == tournament.round_idx and m_idx == tournament.match_idx
                       and not tournament.is_complete())

            if is_final_round and tournament.is_complete():
                champion = tournament.champion()
                _draw_bracket_box(surface, champion.label, x_out, cy,
                                  SLOT_W, SLOT_H, font_small, _slot_color(champion), highlight=True)
                crown = font_small.render("CHAMPION", True, ACCENT_COLOR)
                surface.blit(crown, (x_out + SLOT_W // 2 - crown.get_width() // 2, cy - SLOT_H - 6))
            elif match.winner is not None:
                w_slot = tournament.slots[match.winner]
                _draw_bracket_box(surface, w_slot.label, x_out, cy,
                                  SLOT_W, SLOT_H, font_small, _slot_color(w_slot), highlight=False)
            elif is_next:
                _draw_bracket_box(surface, "NEXT ▶", x_out, cy,
                                  SLOT_W, SLOT_H, font_small, ACCENT_COLOR, highlight=True)
            else:
                _draw_bracket_box(surface, "?", x_out, cy,
                                  SLOT_W, SLOT_H, font_small, (50, 50, 70), highlight=False)

    # Round labels
    round_labels = (["SEMI-FINALS", "FINAL"] if n_rounds == 2
                    else ["QUARTER-FINALS", "SEMI-FINALS", "FINAL"])
    for r, label in enumerate(round_labels):
        txt = font_small.render(label, True, (65, 65, 85))
        surface.blit(txt, (col_xs[r] + SLOT_W // 2 - txt.get_width() // 2, TOP - 26))

    # Bottom prompt
    if tournament.is_complete():
        prompt = "ENTER  Return to menu    ESC  Return to menu"
    else:
        prompt = "ENTER  Start next match    ESC  Quit tournament"
    p_txt = font_small.render(prompt, True, (90, 90, 110))
    surface.blit(p_txt, (SCREEN_W // 2 - p_txt.get_width() // 2, SCREEN_H - 34))
```

- [ ] **Step 2: Replace stub `_handle_bracket_event` in `src/game.py`**

Replace the stub with:

```python
    def _handle_bracket_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.tournament.is_complete():
                    self.transition.start(self._end_tournament)
                else:
                    self._setup_tournament_match()
                    def _go_mode():
                        self.state = STATE_MODE_SELECT
                        self.mode_selected = 0
                    self.transition.start(_go_mode)
            elif event.key == pygame.K_ESCAPE:
                self.transition.start(self._end_tournament)
```

- [ ] **Step 3: Add `_end_tournament` and `_setup_tournament_match` to `src/game.py`**

After `_handle_bracket_event`, add:

```python
    def _end_tournament(self):
        self.tournament = None
        self._reset_to_menu()

    def _setup_tournament_match(self):
        match = self.tournament.next_match()
        slot_a = self.tournament.slots[match.slot_a]
        slot_b = self.tournament.slots[match.slot_b]
        # Normalize: CPU must be game player 2 (right paddle / CPUController)
        if slot_a.is_cpu and not slot_b.is_cpu:
            a_idx, b_idx = match.slot_b, match.slot_a
            slot_a, slot_b = slot_b, slot_a
        else:
            a_idx, b_idx = match.slot_a, match.slot_b
        self._tournament_match_slots = (a_idx, b_idx)
        if slot_b.is_cpu:
            self.opponent_type = OPPONENT_CPU
            self.cpu_difficulty = slot_b.difficulty
        else:
            self.opponent_type = OPPONENT_HUMAN
            self.cpu_difficulty = "MEDIUM"
```

- [ ] **Step 4: Fix mode select ESC to return to bracket when in tournament**

In `_handle_mode_select_event`, replace the `K_ESCAPE` branch:

```python
            elif event.key == pygame.K_ESCAPE:
                self.menu_hover_t = 0.0
                if self.tournament is not None:
                    self.transition.start(lambda: setattr(self, "state", STATE_BRACKET))
                elif self.opponent_type == OPPONENT_CPU:
                    self.transition.start(lambda: setattr(self, "state", STATE_DIFFICULTY))
                else:
                    self.transition.start(lambda: setattr(self, "state", STATE_MENU))
```

- [ ] **Step 5: Run the full test suite**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/renderer.py src/game.py
git commit -m "feat: implement bracket screen and setup→bracket flow"
```

---

## Task 5 — Match Integration (TDD)

**Files:**
- Modify: `tests/test_game_logic.py` — add tournament integration tests
- Modify: `src/game.py` — modify `_end_match()`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_game_logic.py`:

```python
# ── Tournament integration ────────────────────────────────────────────────────

from src.tournament import TournamentManager, Slot as TSlot
from src.constants import STATE_BRACKET


def _make_4p_tournament():
    slots = [
        TSlot("P1", False, "EASY"), TSlot("P2", False, "EASY"),
        TSlot("P3", False, "EASY"), TSlot("P4", False, "EASY"),
    ]
    return TournamentManager(slots)


def test_end_match_transitions_to_bracket_when_tournament_active():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._tournament_match_slots = (0, 1)
    g._end_match(winner=1)
    assert g.state == STATE_BRACKET


def test_end_match_records_correct_winner_slot_player1():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._tournament_match_slots = (0, 1)
    g._end_match(winner=1)         # game player 1 → slot index 0
    assert g.tournament.rounds[0][0].winner == 0


def test_end_match_records_correct_winner_slot_player2():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._tournament_match_slots = (0, 1)
    g._end_match(winner=2)         # game player 2 → slot index 1
    assert g.tournament.rounds[0][0].winner == 1


def test_end_match_without_tournament_goes_to_game_over():
    g = make_game()
    g.tournament = None
    g._end_match(winner=1)
    assert g.state == STATE_GAME_OVER


def test_setup_tournament_match_human_vs_human():
    g = make_game()
    g.tournament = _make_4p_tournament()
    g._setup_tournament_match()
    assert g.opponent_type == OPPONENT_HUMAN
    assert g._tournament_match_slots == (0, 1)


def test_setup_tournament_match_cpu_slot_b():
    from src.constants import OPPONENT_CPU
    slots = [
        TSlot("P1", False, "EASY"), TSlot("CPU-HARD", True, "HARD"),
        TSlot("P2", False, "EASY"), TSlot("P3", False, "EASY"),
    ]
    g = make_game()
    g.tournament = TournamentManager(slots)
    g._setup_tournament_match()    # match is slot 0 (human) vs slot 1 (CPU)
    assert g.opponent_type == OPPONENT_CPU
    assert g.cpu_difficulty == "HARD"
    assert g._tournament_match_slots == (0, 1)


def test_setup_tournament_match_cpu_slot_a_swaps_to_right():
    from src.constants import OPPONENT_CPU
    slots = [
        TSlot("CPU-EASY", True, "EASY"), TSlot("P1", False, "EASY"),
        TSlot("P2", False, "EASY"), TSlot("P3", False, "EASY"),
    ]
    g = make_game()
    g.tournament = TournamentManager(slots)
    g._setup_tournament_match()    # match is slot 0 (CPU) vs slot 1 (human) → must swap
    assert g.opponent_type == OPPONENT_CPU
    assert g._tournament_match_slots == (1, 0)  # human is now slot_a (left)
```

- [ ] **Step 2: Run tests — confirm new tests fail**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/test_game_logic.py -v -k "tournament" 2>&1 | tail -20
```

Expected: the 7 new tournament tests FAIL (`AssertionError` or `AttributeError`).

- [ ] **Step 3: Modify `_end_match` to intercept tournament results**

In `src/game.py`, in `_end_match`, add the tournament guard AFTER the winner is resolved but BEFORE `self.winner = winner`. The full modified method:

```python
    def _end_match(self, winner: int | None = None):
        if winner is None:
            if self.p1.score > self.p2.score:
                winner = 1
            elif self.p2.score > self.p1.score:
                winner = 2
            else:
                winner = 1

        if self.tournament is not None:
            winner_slot = self._tournament_match_slots[winner - 1]
            self.tournament.record_result(winner_slot)
            self._bg_channel.fadeout(500)
            self.state = STATE_BRACKET
            return

        self.winner = winner
        self._bg_channel.fadeout(500)
        if self.opponent_type == OPPONENT_CPU and winner == 2:
            self._play_sfx("losing")
        else:
            self._play_sfx("victory")
        self.particles.emit_score(SCREEN_W if winner == 1 else 0,
                                  P1_COLOR if winner == 1 else P2_COLOR)
        self.gameover_pulse = 0.0
        self.gameover_selected = 0
        self.state = STATE_GAME_OVER
```

- [ ] **Step 4: Run the tests — confirm all pass**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/ -v
```

Expected: ALL tests pass (including the 7 new tournament integration tests).

- [ ] **Step 5: Commit**

```bash
git add tests/test_game_logic.py src/game.py
git commit -m "feat: wire tournament result recording into _end_match"
```

---

## Task 6 — Mode Select Context Label + Final Polish

**Files:**
- Modify: `src/renderer.py` — pass tournament context to mode select
- Modify: `src/game.py` — pass tournament label to draw_mode_select

- [ ] **Step 1: Pass a tournament match label to `draw_mode_select`**

In `src/game.py`, in `_draw`, update the `STATE_MODE_SELECT` branch:

```python
        elif self.state == STATE_MODE_SELECT:
            if self.tournament is not None:
                m = self.tournament.next_match()
                if m is not None:
                    sa = self.tournament.slots[m.slot_a].label
                    sb = self.tournament.slots[m.slot_b].label
                    context = f"TOURNAMENT · {sa} vs {sb}"
                else:
                    context = "TOURNAMENT"
            elif self.opponent_type == OPPONENT_CPU:
                context = f"1vCPU · {self.cpu_difficulty}"
            else:
                context = None
            renderer.draw_mode_select(game_surf, self.font_large, self.font_small,
                                      self.mode_selected, context,
                                      self.menu_particles, self.menu_hover_t)
```

- [ ] **Step 2: Run the full test suite one final time**

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/game.py
git commit -m "feat: show match participants in mode-select context label for tournament"
```

---

## Running the Game

```bash
cd /home/aryan/Documents/GitHub/py-pong
python3 main.py
```

Manual test path:
1. Main menu → **TOURNAMENT** (arrow down twice, Enter)
2. Setup screen: adjust slots with ←/→, toggle size with Tab, confirm with Enter
3. Bracket screen: Enter to start match 1 → mode select → play → result posts to bracket
4. Repeat until champion highlighted
5. Enter or Esc → back to menu
