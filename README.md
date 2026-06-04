# py-pong 🎮

A modernized, feature-rich 2-player local Pong game built with **pygame-ce**, featuring neon/synthwave aesthetics, dynamic power-ups, particle effects, and multiple game modes.

---

## Features ✨

- **Classic Pong Gameplay** with modern twists
- **Neon Synthwave Aesthetic** — vibrant cyan, magenta, and yellow color scheme with glow effects
- **Multiple Game Modes:**
  - **First to 11** — classic single-match mode
  - **Best of 3 Sets** — competitive 3-set format (first to 7 per set)
  - **Timed (3 minutes)** — most points win, with 60s sudden death on tie
- **Power-ups** — randomly spawning gameplay modifiers:
  - 🚀 Speed Boost
  - 🐢 Slow Ball
  - 🏓 Big Paddle
  - 👽 Small Opponent
  - 🎯 Multi-Ball (dual balls on field)
- **Visual Effects:**
  - Ball trails with adaptive length
  - Particle bursts on scoring
  - Screen shake on collisions and scores
  - Neon glow rendering (no external shaders)
- **Audio:**
  - Dynamic music with intensity-based transitions
  - Sound effects for hits, scores, power-ups, and victories
- **Smash Meter System** — charge power shots for extra impact
- **Framerate-Independent Physics** — smooth movement with delta-time updates

---

## Installation

### Requirements

- **Python 3.8+**
- **pygame-ce** ≥ 2.5.0
- **pytest** ≥ 8.0.0 (for running tests)

### Setup

1. **Clone or extract the repository:**
   ```bash
   git clone https://github.com/yourusername/py-pong.git
   cd py-pong
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Play

### Running the Game

```bash
python main.py
```

### Controls

| Action | Player 1 | Player 2 |
|--------|----------|----------|
| Move Up | **W** | **↑** (Up Arrow) |
| Move Down | **S** | **↓** (Down Arrow) |
| Pause | **ESC** | **ESC** |
| Menu Navigate | **Arrow Keys + Enter** | — |

### Gameplay

1. **Main Menu** — Press `PLAY` to start or `QUIT` to exit
2. **Mode Selection** — Choose your preferred game mode (navigate with arrow keys, confirm with Enter)
3. **Play** — Control your paddle and keep the ball in play
4. **Scoring** — Ball must pass opponent's paddle to score
5. **Power-ups** — Collect random power-ups spawning on the field for temporary advantages
6. **Pause** — Press ESC anytime to pause/unpause or return to menu
7. **Game Over** — After winning, choose `REMATCH` for a quick replay or `MENU` to select new settings

#### Smash Meter

- Builds as you hit the ball and score points
- When charged, your paddle gets a power shot boost
- Visual indicator under your score in the HUD

---

## Game Modes Explained

### First to 11 (Classic)
- Single continuous match
- First player to reach 11 points wins
- Perfect for quick casual matches

### Best of 3 Sets
- Three sets, each to 7 points
- Win 2 sets to win the match
- Ideal for competitive play with multiple rounds

### Timed (3 Minutes)
- Fixed 3-minute game clock
- Highest score wins
- If tied at end: 60-second sudden death (next point wins)
- Great for intense, action-packed sessions

---

## Project Structure

```
py-pong/
├── main.py                      # Entry point — initializes pygame and runs game loop
├── requirements.txt             # Python dependencies
├── LICENSE                      # Project license
│
├── src/                         # Core game source code
│   ├── __init__.py
│   ├── constants.py             # Screen size, colors, speeds, timing constants
│   ├── entities.py              # Paddle, Ball, PowerUp classes
│   ├── effects.py               # ParticleSystem, Trail, ScreenShake
│   ├── game.py                  # Game state machine, input, update loop
│   └── renderer.py              # All draw calls, UI, neon glow effects
│
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_entities.py         # Entity behavior tests
│   ├── test_effects.py          # Effects system tests
│   └── test_game_logic.py       # Game state and logic tests
│
├── assets/                      # Game assets
│   └── sounds/                  # Audio files (SFX and music)
│       ├── ball hit.mp3         # Paddle hit sound
│       ├── main theme.mp3       # Default background music
│       └── [other audio files]
│
└── docs/                        # Design documentation
    └── superpowers/
        ├── specs/               # Technical specifications
        └── plans/               # Development plans and roadmap
```

---

## Architecture

### State Machine

The game follows a clear state flow:

```
MENU → MODE_SELECT → PLAYING ⟷ PAUSED → GAME_OVER → MENU
```

State transitions are handled in `game.py` with enum-based dispatch — no separate scene classes.

### Core Systems

#### **Entities** (`src/entities.py`)
- **Paddle:** Dual-vector movement with velocity-based physics
- **Ball:** Position/velocity with angle-based exit from paddle contact, speed scaling per rally
- **PowerUp:** Spawns randomly every 10–15 seconds, one active at a time

#### **Effects** (`src/effects.py`)
- **ScreenShake:** Quadratic trauma decay applied as camera offset
- **ParticleSystem:** 40–60 particles per score event with neon colors
- **Trail:** Ball's last 12 positions rendered with alpha fade

#### **Rendering** (`src/renderer.py`)
- Neon glow via 3× blits with `BLEND_ADD`
- HUD with active power-up icons and charge bars
- Layered draw order: background → entities → trails → particles → UI

#### **Game Logic** (`src/game.py`)
- Physics updates with delta-time
- Paddle collision and ball bouncing
- Smash meter charging and activation
- Power-up spawning and duration tracking

---

## Testing

Run the full test suite with pytest:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_game_logic.py
```

### Test Coverage

- **Entity behavior** — paddle movement, ball physics, power-up collection
- **Effect systems** — screen shake, particle emission, trails
- **Game logic** — scoring, state transitions, win conditions

---

## Technical Details

### Display & Performance

- **Resolution:** 1280×720 (16:9)
- **Target FPS:** 60
- **Rendering:** pygame-ce with hardware acceleration
- **Physics:** Delta-time independent for smooth framerate scaling

### Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Background | Near-black | `#0a0a0f` |
| Player 1 (P1) | Cyan | `#00f5ff` |
| Player 2 (P2) | Magenta | `#ff00c8` |
| Accent | Yellow | `#ffe600` |

### Audio

- **Channels:** Dual mixer for crossfading music
- **SFX:** Hit, score, power-up, and victory sounds
- **Music:** Dynamic theme selection based on rally intensity
- **Graceful Degradation:** Missing audio files don't crash the game

---

## Development

### Code Style

- Pure Python with pygame-ce — no external rendering libraries
- Type hints for clarity
- Entity-component-style architecture
- Constants centralized in `src/constants.py`

### Building & Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes and add tests
4. Run `pytest` to ensure all tests pass
5. Submit a pull request

---

## Known Issues & Limitations

- Audio files are optional; game runs silently if missing
- Designed for 2-player local play only (no AI opponent)
- Tested on Python 3.8+

---

## Roadmap & Future Ideas

- **AI Opponent Mode** — single-player vs computer
- **Online Multiplayer** — networked 2-player
- **Customization** — color themes, custom controls, difficulty levels
- **Leaderboards** — local high-score tracking
- **Mobile Port** — touch-optimized version

---

## License

This project is licensed under the terms specified in the `LICENSE` file. See the LICENSE file for details.

---

## Credits & Acknowledgments

Built with **pygame-ce** — the community edition of pygame focused on modern Python support and active development.

Inspired by the classic Pong arcade game, reimagined with contemporary aesthetics and gameplay mechanics.

---

## Getting Help

- **Check the docs/** directory for detailed design specifications
- **Review test cases** in `tests/` for usage examples
- **Inspect `src/constants.py`** to tweak game parameters
- **Open an issue** if you encounter bugs or have feature requests

---

Enjoy the game! 🎮✨
