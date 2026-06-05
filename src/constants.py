# Screen
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
HUD_HEIGHT = 60

# Colors
BG_COLOR = (10, 10, 15)
P1_COLOR = (0, 245, 255)
P2_COLOR = (255, 0, 200)
ACCENT_COLOR = (255, 230, 0)
WHITE = (255, 255, 255)

# Paddle
PADDLE_W = 14
PADDLE_H = 100
PADDLE_SPEED = 500
PADDLE_MARGIN = 40

# Ball
BALL_SIZE = 14
BALL_SPEED_INITIAL = 400
BALL_SPEED_MAX_MULTIPLIER = 2.0
BALL_SPEED_INCREMENT = 0.05
BALL_TRAIL_LENGTH = 12

# PowerUp
POWERUP_SIZE = 24
POWERUP_SPAWN_MIN = 10.0
POWERUP_SPAWN_MAX = 15.0
POWERUP_DURATION = 7.0

# Game modes
MODE_FIRST_TO_11 = "first_to_11"
MODE_BEST_OF_3 = "best_of_3"
MODE_TIMED = "timed"
TIMED_DURATION = 180.0
SUDDEN_DEATH_DURATION = 60.0
SET_WIN_SCORE = 7
MATCH_WIN_SETS = 2
CLASSIC_WIN_SCORE = 11

# States
STATE_MENU = "menu"
STATE_MODE_SELECT = "mode_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"

# Screen shake
SHAKE_MAX_OFFSET = 12
SHAKE_SCORE_TRAUMA = 1.0
SHAKE_HIT_TRAUMA = 0.3
SHAKE_DECAY = 0.85

# Particles
PARTICLE_COUNT_SCORE = 50
PARTICLE_LIFETIME_MIN = 0.4
PARTICLE_LIFETIME_MAX = 0.8

# Final Smash meter
SMASH_BASE_CHARGE_RATE = 0.025   # fills in ~40s at zero gap
SMASH_PER_POINT_CHARGE = 0.020   # additional rate per point behind

# CPU / opponent mode
STATE_DIFFICULTY = "difficulty"
OPPONENT_HUMAN = "human"
OPPONENT_CPU = "cpu"

DIFFICULTY_OPTIONS = ["EASY", "MEDIUM", "HARD", "INSANE"]

DIFFICULTY_COLORS = {
    "EASY":   (105, 255,  71),
    "MEDIUM": (255, 215,  64),
    "HARD":   (255, 109,   0),
    "INSANE": (255,  23,  68),
}

CPU_PARAMS = {
    "EASY":   {"max_speed": 180, "reaction_delay": 0.35, "dead_zone": 20},
    "MEDIUM": {"max_speed": 320, "reaction_delay": 0.18, "dead_zone": 15},
    "HARD":   {"max_speed": 480, "reaction_delay": 0.06, "dead_zone": 10},
    "INSANE": {"max_speed": 650, "reaction_delay": 0.00, "dead_zone":  5},
}
