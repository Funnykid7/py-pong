# py-pong — Design Spec
**Date:** 2026-06-04  
**Status:** Approved

---

## Overview

A modernized 2-player local Pong built with pygame-ce. Classic rules, neon/synthwave aesthetic, power-ups, particle effects, screen shake, ball trails, dynamic music, and configurable game modes. Both players share one keyboard.

---

## File Structure

```
py-pong/
├── main.py                  # Entry point — creates window, runs game loop
├── src/
│   ├── constants.py         # Screen size, colors, speeds, timing constants
│   ├── entities.py          # Paddle, Ball, PowerUp classes
│   ├── effects.py           # ParticleSystem, Trail, ScreenShake
│   ├── renderer.py          # All draw calls — neon glow, HUD, menus
│   └── game.py              # GameState machine, input handling, update loop
├── assets/
│   └── sounds/              # Synth SFX + music tracks
└── requirements.txt         # pygame-ce>=2.5.0
```

---

## State Machine

States (enum in `game.py`): `MENU → MODE_SELECT → PLAYING → PAUSED → GAME_OVER → MENU`

Each state has its own `update()` and `draw()` branch — no separate scene classes, just enum dispatch.

---

## Entities (`src/entities.py`)

### Paddle
- `pygame.Rect` for collision, `pygame.Vector2` for position/velocity
- Height: 100px default
- Velocity-based movement with dt (smooth, framerate-independent)
- Stores: `score`, `active_powerup`, `powerup_timer`

### Ball
- `pygame.Vector2` position + velocity
- Exit angle on paddle hit based on contact point relative to paddle center:
  - Top third → steep upward angle
  - Center → flat
  - Bottom third → steep downward angle
- Speed increases 5% per rally hit, capped at 2× starting speed
- `spin` float: applies slight curve over time
- `trail_positions`: last 12 positions (consumed by renderer for trail drawing)
- On score: reset to center, 1-second countdown before relaunch

### PowerUp
- Spawns at random midfield position every 10–15 seconds (randomized interval)
- One power-up on field at a time
- Types (enum): `SPEED_BOOST`, `SLOW_BALL`, `BIG_PADDLE`, `SMALL_OPPONENT`, `MULTI_BALL`
- Collected by ball collision; activates for the last-touch player
- Duration: 7 seconds
- `MULTI_BALL`: spawns a second `Ball` instance; both tracked in a list in `game.py`
- Pulses visually (scale oscillation via renderer)

---

## Effects (`src/effects.py`)

### ParticleSystem
- Emits 40–60 particles on every score, from the goal wall
- Each particle: position, velocity, lifetime (0.4–0.8s), neon color (cyan / magenta / yellow)
- Culled each frame when lifetime expires
- Rendered as small glowing circles with alpha falloff

### Trail
- Ball stores last 12 positions
- Renderer draws shrinking circles with decreasing alpha
- Trail length visually stretches at high ball speeds

### ScreenShake
- `trauma` float (0.0–1.0)
- Score hit: `trauma = 1.0`; paddle hit: `trauma = 0.3`
- Decay per frame: `trauma *= 0.85`
- Camera offset: `trauma² × 12px` (quadratic falloff, applied to all draw calls)

---

## Rendering (`src/renderer.py`)

### Draw order per frame
1. Background (dark, near-black)
2. Center dashed line
3. Entities (paddles, ball, power-ups)
4. Trails
5. Particles
6. HUD
7. Screen-space effects (shake offset applied to all of 1–5)

### Neon Glow technique
- No external shader libs — pure pygame-ce
- For each glowing shape: blit 3 times onto a temp surface using `BLEND_ADD`:
  - Scale 1.0× — alpha 255
  - Scale 1.4× — alpha 80
  - Scale 1.8× — alpha 30

---

## Game Modes

Chosen on the Mode Select screen before each match:

| Mode | Rule |
|------|------|
| First to 11 | Classic; one continuous match |
| Best of 3 sets | Each set to 7 points; win 2 sets to win match |
| Timed (3 min) | Most points wins; tie → 60s sudden death |

---

## HUD

- Fixed 60px bar at top of screen
- Left: Player 1 score (neon cyan)
- Right: Player 2 score (neon magenta)
- Center: match clock (timed mode) or set indicators (best-of-3); empty in first-to-11
- Active power-up: small icon + countdown bar beneath each score
- Neon divider line separates HUD from play field
- Bottom of screen: persistent tiny control hint — `W/S` and `↑/↓`

---

## Menus

### Main Menu
- Large synthwave title
- Options: `PLAY` / `QUIT`
- Animated ball bouncing in background as decoration

### Mode Select
- Three mode cards: First to 11 / Best of 3 / Timed
- Navigate with arrow keys, confirm with Enter

### Pause (ESC)
- Darkened overlay over play field
- Options: `RESUME` / `QUIT TO MENU`

### Game Over
- Winner announced with particle burst
- Final score displayed
- Options: `REMATCH` / `MENU`
- Neon glow pulse on winner text

---

## Controls

| Action | Player 1 | Player 2 |
|--------|----------|----------|
| Move Up | W | ↑ |
| Move Down | S | ↓ |
| Pause | ESC | ESC |
| Menu navigate | Arrow keys + Enter | — |

---

## Audio

- **SFX:** `hit.wav` (paddle hit), `score.wav` (goal), `powerup.wav` (power-up collected), `win.wav` (match end)
- **Music:** `music_normal.ogg` (default loop), `music_intense.ogg` (rally ≥ 5 hits)
- Transition: 0.5s crossfade via two pygame mixer channels
- Missing audio files skipped silently (consistent with project conventions)

---

## Technical Notes

- Screen: 1280×720 (16:9, standard for modern displays)
- All movement uses `pygame.Vector2` with delta-time (`dt`)
- `pygame.image.load().convert_alpha()` on all surfaces
- Target: 60 FPS via `pygame.Clock.tick(60)`
- Color palette: background `#0a0a0f`, P1 cyan `#00f5ff`, P2 magenta `#ff00c8`, accent yellow `#ffe600`
