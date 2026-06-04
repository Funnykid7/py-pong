import math
import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, HUD_HEIGHT, BG_COLOR,
    P1_COLOR, P2_COLOR, ACCENT_COLOR, WHITE,
    BALL_SIZE, BALL_SPEED_INITIAL, BALL_SPEED_MAX_MULTIPLIER,
    PADDLE_H, POWERUP_SIZE, POWERUP_DURATION,
    MODE_TIMED, MODE_BEST_OF_3,
)


POWERUP_COLORS = {
    "SPEED_BOOST": (255, 230, 0),
    "SLOW_BALL": (100, 200, 255),
    "BIG_PADDLE": (0, 255, 100),
    "SMALL_OPPONENT": (255, 80, 80),
    "MULTI_BALL": (200, 100, 255),
}

POWERUP_LABELS = {
    "SPEED_BOOST": "FAST",
    "SLOW_BALL": "SLOW",
    "BIG_PADDLE": "BIG",
    "SMALL_OPPONENT": "SHRINK",
    "MULTI_BALL": "MULTI",
}


def draw_glow(surface: pygame.Surface, color: tuple, center: tuple, radius: int):
    for scale, alpha in [(1.8, 30), (1.4, 80), (1.0, 255)]:
        r = max(1, int(radius * scale))
        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, alpha), (r, r), r)
        surface.blit(glow_surf, (center[0] - r, center[1] - r), special_flags=pygame.BLEND_ADD)


def draw_glow_rect(surface: pygame.Surface, color: tuple, rect: pygame.Rect):
    for scale, alpha in [(1.4, 30), (1.2, 80), (1.0, 255)]:
        w = max(1, int(rect.width * scale))
        h = max(1, int(rect.height * scale))
        glow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*color, alpha), glow_surf.get_rect(), border_radius=4)
        cx, cy = rect.center
        surface.blit(glow_surf, (cx - w // 2, cy - h // 2), special_flags=pygame.BLEND_ADD)


def draw_background(surface: pygame.Surface):
    surface.fill(BG_COLOR)
    dash_h, gap = 20, 12
    x = SCREEN_W // 2 - 1
    y = HUD_HEIGHT
    while y < SCREEN_H:
        pygame.draw.rect(surface, (50, 50, 70), (x, y, 2, min(dash_h, SCREEN_H - y)))
        y += dash_h + gap


def draw_hud(surface, p1, p2, font_large, font_small,
             game_mode: str, time_left, sets):
    pygame.draw.rect(surface, (15, 15, 25), (0, 0, SCREEN_W, HUD_HEIGHT))
    pygame.draw.line(surface, (40, 40, 60), (0, HUD_HEIGHT), (SCREEN_W, HUD_HEIGHT), 1)

    p1_text = font_large.render(str(p1.score), True, P1_COLOR)
    p2_text = font_large.render(str(p2.score), True, P2_COLOR)
    surface.blit(p1_text, (SCREEN_W // 4 - p1_text.get_width() // 2, 8))
    surface.blit(p2_text, (3 * SCREEN_W // 4 - p2_text.get_width() // 2, 8))

    if game_mode == MODE_TIMED and time_left is not None:
        mins = int(time_left) // 60
        secs = int(time_left) % 60
        clock_text = font_large.render(f"{mins}:{secs:02d}", True, WHITE)
        surface.blit(clock_text, (SCREEN_W // 2 - clock_text.get_width() // 2, 8))
    elif game_mode == MODE_BEST_OF_3 and sets is not None:
        s1, s2 = sets
        set_text = font_small.render(f"Sets  {s1} — {s2}", True, (180, 180, 200))
        surface.blit(set_text, (SCREEN_W // 2 - set_text.get_width() // 2, 20))

    _draw_powerup_hud(surface, p1, font_small, SCREEN_W // 4, P1_COLOR)
    _draw_powerup_hud(surface, p2, font_small, 3 * SCREEN_W // 4, P2_COLOR)

    hint = font_small.render("W/S                    ↑/↓", True, (60, 60, 80))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 22))


def _draw_powerup_hud(surface, paddle, font_small, cx, color):
    if not paddle.active_powerup:
        return
    label = POWERUP_LABELS.get(paddle.active_powerup, "?")
    pct = max(0.0, paddle.powerup_timer / POWERUP_DURATION)
    bar_w = 80
    bar_x = cx - bar_w // 2
    bar_y = HUD_HEIGHT - 14
    pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, 6), border_radius=3)
    pygame.draw.rect(surface, color, (bar_x, bar_y, int(bar_w * pct), 6), border_radius=3)
    txt = font_small.render(label, True, color)
    surface.blit(txt, (cx - txt.get_width() // 2, bar_y - 16))


def draw_paddle(surface: pygame.Surface, paddle):
    draw_glow_rect(surface, paddle.color, paddle.rect)


def draw_ball(surface: pygame.Surface, ball):
    for i, pos in enumerate(ball.trail_positions):
        if not ball.trail_positions:
            break
        frac = i / len(ball.trail_positions)
        alpha = int(180 * frac)
        r = max(1, int((BALL_SIZE // 2) * frac))
        speed_ratio = min(1.0, ball.current_speed / (BALL_SPEED_INITIAL * BALL_SPEED_MAX_MULTIPLIER))
        color = (
            int(P1_COLOR[0] * (1 - speed_ratio) + ACCENT_COLOR[0] * speed_ratio),
            int(P1_COLOR[1] * (1 - speed_ratio) + ACCENT_COLOR[1] * speed_ratio),
            int(P1_COLOR[2] * (1 - speed_ratio) + ACCENT_COLOR[2] * speed_ratio),
        )
        trail_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(trail_surf, (*color, alpha), (r, r), r)
        surface.blit(trail_surf, (int(pos.x) - r, int(pos.y) - r))
    draw_glow(surface, ACCENT_COLOR, (int(ball.pos.x), int(ball.pos.y)), BALL_SIZE // 2)


def draw_powerup(surface: pygame.Surface, powerup):
    color = POWERUP_COLORS.get(powerup.type, WHITE)
    scale = 1.0 + 0.15 * math.sin(powerup.pulse_t * 4)
    r = max(1, int(POWERUP_SIZE // 2 * scale))
    draw_glow(surface, color, (int(powerup.pos.x), int(powerup.pos.y)), r)


def draw_particles(surface: pygame.Surface, particles: list):
    for p in particles:
        if p.alpha > 0:
            draw_glow(surface, p.color, (int(p.pos.x), int(p.pos.y)), p.radius)


def draw_countdown(surface: pygame.Surface, count: int, font_huge):
    if count > 0:
        text = font_huge.render(str(count), True, WHITE)
        x = SCREEN_W // 2 - text.get_width() // 2
        y = SCREEN_H // 2 - text.get_height() // 2
        surface.blit(text, (x, y))


def draw_menu(surface, font_title, font_large, font_small, selected: int, anim_ball_pos: tuple):
    draw_background(surface)
    draw_glow(surface, ACCENT_COLOR, (int(anim_ball_pos[0]), int(anim_ball_pos[1])), BALL_SIZE // 2)
    title = font_title.render("PY-PONG", True, P1_COLOR)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))
    for i, opt in enumerate(["PLAY", "QUIT"]):
        color = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(opt, True, color)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 370 + i * 70))


def draw_mode_select(surface, font_large, font_small, selected: int):
    draw_background(surface)
    title = font_large.render("SELECT MODE", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 160))
    modes = [
        ("FIRST TO 11", "Classic — first to 11 points wins"),
        ("BEST OF 3 SETS", "Win 2 sets of 7 points each"),
        ("TIMED  3 MIN", "Most points in 3 minutes — tie = sudden death"),
    ]
    for i, (label, desc) in enumerate(modes):
        y = 280 + i * 110
        color = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(label, True, color)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
        desc_text = font_small.render(desc, True, (120, 120, 140))
        surface.blit(desc_text, (SCREEN_W // 2 - desc_text.get_width() // 2, y + 44))


def draw_pause(surface, font_large, selected: int):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    title = font_large.render("PAUSED", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 260))
    for i, opt in enumerate(["RESUME", "QUIT TO MENU"]):
        color = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(opt, True, color)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 360 + i * 70))


def draw_game_over(surface, winner: int, p1, p2, font_title, font_large, selected: int, pulse_t: float):
    draw_background(surface)
    color = P1_COLOR if winner == 1 else P2_COLOR
    winner_surf = font_title.render(f"PLAYER {winner} WINS!", True, color)
    surface.blit(winner_surf, (SCREEN_W // 2 - winner_surf.get_width() // 2, 200))
    score_text = font_large.render(f"{p1.score}  —  {p2.score}", True, WHITE)
    surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, 310))
    for i, opt in enumerate(["REMATCH", "MENU"]):
        c = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(opt, True, c)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 420 + i * 70))
