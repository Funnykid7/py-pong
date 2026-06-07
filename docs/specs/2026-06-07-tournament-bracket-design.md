# Tournament / Bracket Mode — Design Spec

**Date:** 2026-06-07  
**Status:** Approved

---

## Overview

Add a single-elimination tournament mode to py-pong. Players (human or CPU) are seeded into a 4- or 8-player bracket. Matches play through the existing game loop unchanged; a new `TournamentManager` class tracks bracket state and advances to the next match after each result.

---

## Approach

**TournamentManager module** (`src/tournament.py`) — all bracket logic lives in a dedicated, pygame-free class. `Game` holds `self.tournament: TournamentManager | None = None` and delegates bracket decisions to it. This mirrors the `CPUController` pattern already in the codebase.

---

## State Flow

Two new states are added to the existing state machine:

```
STATE_TOURNAMENT_SETUP   — configure 4/8 slots (Human vs CPU + difficulty)
STATE_BRACKET            — display bracket, trigger next match
```

The menu gains a third option: **Tournament**.

Full flow:

```
STATE_MENU
  → [Tournament selected]
  → STATE_TOURNAMENT_SETUP
  → [Enter] → STATE_BRACKET (initial, all matches pending)
  → [Enter on bracket] → STATE_MODE_SELECT  (per-match mode pick)
  → STATE_PLAYING
  → _end_match() detects self.tournament is not None
      → tournament.record_result(winner_slot_idx)
      → state = STATE_BRACKET (updated)
  → … repeat for each match …
  → final recorded → bracket shows champion highlighted
  → [Esc / Enter] → STATE_MENU
```

The existing `STATE_GAME_OVER` screen is **bypassed** for tournament matches — the updated bracket IS the result screen.

---

## TournamentManager (`src/tournament.py`)

```python
@dataclass
class Slot:
    label: str        # "P1", "P2", "CPU-HARD", etc.
    is_cpu: bool
    difficulty: str   # EASY/MEDIUM/HARD/INSANE (ignored if not CPU)

@dataclass
class Match:
    slot_a: int       # index into TournamentManager.slots
    slot_b: int
    winner: int | None = None   # slot index of winner; None = not yet played

class TournamentManager:
    size: int                   # 4 or 8
    slots: list[Slot]           # length == size
    rounds: list[list[Match]]   # rounds[0]=QF/R1, rounds[-1]=Final
    round_idx: int              # active round
    match_idx: int              # next unplayed match within active round

    def next_match(self) -> Match | None
        # Returns the next unplayed match, or None if tournament is complete.

    def record_result(self, winner_slot_idx: int) -> None
        # Records winner, propagates slot into next round's match.
        # Advances match_idx (and round_idx when all matches in round are done).

    def is_complete(self) -> bool
        # True when the final match has a winner.

    def champion(self) -> Slot | None
        # Returns the winning Slot once is_complete() is True.
```

**Seeding:** Slots are paired sequentially — slots 0 & 1 in match 0, slots 2 & 3 in match 1, etc. No randomised seeding needed.

**Round structure:**
- 4-player: Round 1 (2 matches) → Final (1 match)
- 8-player: Quarter-Finals (4 matches) → Semi-Finals (2 matches) → Final (1 match)

`TournamentManager` has no pygame dependency and is fully unit-testable.

---

## Tournament Setup Screen (`STATE_TOURNAMENT_SETUP`)

**Single screen, slot grid layout** (Option A from visual review).

Layout:
```
TOURNAMENT SETUP

PLAYERS: [4]  [8]          ← Tab toggles

P1   [ HUMAN       ◀ ▶ ]
P2   [ HUMAN       ◀ ▶ ]
P3   [ CPU · MEDIUM ◀ ▶ ]
P4   [ CPU · HARD   ◀ ▶ ]

         [ START — ENTER ]
```

Controls:
| Key | Action |
|-----|--------|
| ↑ / ↓ | Move between slot rows (wraps) |
| ← / → | Cycle slot type: HUMAN → CPU-EASY → CPU-MEDIUM → CPU-HARD → CPU-INSANE → HUMAN |
| Tab | Toggle between 4-player and 8-player bracket (resizes slot list) |
| Enter | Confirm setup → `STATE_BRACKET` |
| Esc | Back to `STATE_MENU` |

When toggling from 4 → 8 players, four new slots are appended (defaulting to CPU-MEDIUM). When toggling 8 → 4, the bottom four slots are removed.

---

## Bracket Screen (`STATE_BRACKET`)

**Classic horizontal bracket tree** (Option A from visual review), matching the game's dark neon aesthetic.

- Matches flow left → right by round (R1 / QF → SF → Final).
- Each slot is a labelled box (P1 / CPU-HARD / etc.) in its player color (P1_COLOR / P2_COLOR for humans; DIFFICULTY_COLORS for CPU).
- Connector lines link match pairs to their winner slot in the next round.
- The **next unplayed match** is highlighted with ACCENT_COLOR (yellow) border and a "NEXT MATCH" label.
- Already-played match winners are shown with full opacity; pending slots are dimmed.
- When `tournament.is_complete()`, the champion's slot is highlighted with a crown label and the prompt changes to "RETURN TO MENU".

Controls:
| Key | Action |
|-----|--------|
| Enter | Start the next match → `STATE_MODE_SELECT` (disabled when `tournament.is_complete()`) |
| Enter (when complete) | → `STATE_MENU` |
| Esc | Quit tournament → `STATE_MENU` (no confirmation) |

---

## Match Integration

When a tournament match starts, `Game._start_match()` reads `tournament.next_match()` to get `(slot_a_idx, slot_b_idx)` and configures the session.

**CPU assignment rule:** `CPUController` always drives game player 2 (right paddle / `self.p2`). To preserve this, the match is normalised before starting:
- If `slot_a` is CPU and `slot_b` is Human → swap them so the Human is always game player 1 (left) and the CPU is game player 2 (right).
- Both Human or both CPU → no swap needed.

`Game` stores `self._tournament_match_slots: tuple[int, int]` (slot_a_idx, slot_b_idx) **after** the swap, so `_resolve_tournament_winner` can map correctly:
- `winner == 1` (game player 1 won) → `self._tournament_match_slots[0]`
- `winner == 2` (game player 2 won) → `self._tournament_match_slots[1]`

Setup based on normalised slots:
- Both Human → `opponent_type = OPPONENT_HUMAN`, `self.cpu = None`
- slot_b is CPU → `opponent_type = OPPONENT_CPU`, `self.cpu = CPUController(slot_b.difficulty)`
- Both CPU → `opponent_type = OPPONENT_CPU`, `self.cpu = CPUController(slot_b.difficulty)` (slot_a auto-plays via existing right-paddle CPU; left-paddle CPU is not supported — treat left CPU as Human for display purposes, future work)

All existing gameplay mechanics are fully active for tournament matches: smash meter, power-ups, all game modes (mode is chosen per-match via the existing `STATE_MODE_SELECT` flow).

`_end_match()` gains a guard:

```python
def _end_match(self, winner: int | None = None):
    # ... existing winner resolution ...
    if self.tournament is not None:
        slot_idx = self._resolve_tournament_winner(winner)
        self.tournament.record_result(slot_idx)
        self.state = STATE_BRACKET
        return   # skip normal game-over flow
    # ... existing game-over flow ...
```

---

## New Files

| File | Purpose |
|------|---------|
| `src/tournament.py` | `Slot`, `Match`, `TournamentManager` |

## Modified Files

| File | Change |
|------|--------|
| `src/constants.py` | Add `STATE_TOURNAMENT_SETUP`, `STATE_BRACKET` |
| `src/game.py` | Add tournament state handlers, modify `_end_match()`, add `self.tournament` |
| `src/renderer.py` | Add `draw_tournament_setup()`, `draw_bracket()` |
| `tests/test_tournament.py` | Unit tests for `TournamentManager` (new) |

---

## Out of Scope

- Double elimination
- Tournament save/resume across app restarts
- Player name entry (slots are auto-labelled)
- Randomised seeding / bracket shuffling
