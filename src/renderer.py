import math
import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, HUD_HEIGHT, BG_COLOR,
    P1_COLOR, P2_COLOR, ACCENT_COLOR, WHITE,
    BALL_SIZE, BALL_SPEED_INITIAL, BALL_SPEED_MAX_MULTIPLIER,
    PADDLE_H, POWERUP_DURATION,
    MODE_TIMED, MODE_BEST_OF_3,
    DIFFICULTY_OPTIONS, DIFFICULTY_COLORS,
)


POWERUP_LABELS = {
    "SPEED_BOOST": "FAST",
    "SLOW_BALL": "SLOW",
    "BIG_PADDLE": "BIG",
    "SMALL_OPPONENT": "SHRINK",
    "MULTI_BALL": "MULTI",
}

_PARTICLE_SURFS: dict[int, pygame.Surface] = {}


def _draw_menu_particles(surface: pygame.Surface, menu_particles: list, hover_t: float):
    for p in menu_particles:
        alpha = max(0, min(255, int(160 + 80 * math.sin(hover_t + p["phase"]))))
        r = p["radius"]
        if r not in _PARTICLE_SURFS:
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            _PARTICLE_SURFS[r] = s
        dot_surf = _PARTICLE_SURFS[r]
        dot_surf.fill((0, 0, 0, 0))
        pygame.draw.circle(dot_surf, (*p["color"], alpha), (r, r), r)
        surface.blit(dot_surf, (int(p["pos"].x) - r, int(p["pos"].y) - r))


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
             game_mode: str, time_left, sets,
             p1_smash: float, p2_smash: float,
             p1_ready: bool, p2_ready: bool, smash_pulse_t: float,
             cpu_mode: bool = False):
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

    if p1.active_powerup:
        _draw_powerup_hud(surface, p1, font_small, SCREEN_W // 8, P1_COLOR)
    else:
        _draw_smash_meter(surface, SCREEN_W // 8, p1_smash, p1_ready, smash_pulse_t,
                          P1_COLOR, "[LSHIFT]", font_small)

    if p2.active_powerup:
        _draw_powerup_hud(surface, p2, font_small, 7 * SCREEN_W // 8, P2_COLOR)
    else:
        p2_shift = "" if cpu_mode else "[RSHIFT]"
        _draw_smash_meter(surface, 7 * SCREEN_W // 8, p2_smash, p2_ready, smash_pulse_t,
                          P2_COLOR, p2_shift, font_small)

    hint_text = "W/S" if cpu_mode else "W/S                    ↑/↓"
    hint = font_small.render(hint_text, True, (60, 60, 80))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 22))


def _draw_smash_meter(surface, cx: int, meter: float, ready: bool, pulse_t: float,
                      color: tuple, shift_label: str, font_small):
    bar_w = 100
    bar_x = cx - bar_w // 2
    bar_y = HUD_HEIGHT - 14
    pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, 6), border_radius=3)
    if ready:
        pulse_alpha = int(180 + 75 * math.sin(pulse_t * 6))
        pulse_surf = pygame.Surface((bar_w, 6), pygame.SRCALPHA)
        pygame.draw.rect(pulse_surf, (*ACCENT_COLOR, pulse_alpha), pulse_surf.get_rect(), border_radius=3)
        surface.blit(pulse_surf, (bar_x, bar_y))
        label_txt = font_small.render(f"READY! {shift_label}".strip(), True, ACCENT_COLOR)
    else:
        fill_w = int(bar_w * meter)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, 6), border_radius=3)
        label_txt = font_small.render("SMASH", True, color)
    surface.blit(label_txt, (cx - label_txt.get_width() // 2, bar_y - label_txt.get_height() - 3))


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


def draw_mode_select(surface, font_large, font_small, selected: int,
                     context_label: str | None = None, menu_particles: list | None = None,
                     hover_t: float = 0.0):
    draw_background(surface)
    if menu_particles is not None:
        _draw_menu_particles(surface, menu_particles, hover_t)
    title = font_large.render("SELECT MODE", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 160))
    modes = [
        ("FIRST TO 11", "Classic — first to 11 points wins"),
        ("BEST OF 3 SETS", "Win 2 sets of 7 points each"),
        ("TIMED  3 MIN", "Most points in 3 minutes — tie = sudden death"),
    ]
    for i, (label, desc) in enumerate(modes):
        y = 280 + i * 110
        if i == selected:
            t = 0.15 * (0.5 + 0.5 * math.sin(hover_t * 2))
            color = (
                int(ACCENT_COLOR[0] + (WHITE[0] - ACCENT_COLOR[0]) * t),
                int(ACCENT_COLOR[1] + (WHITE[1] - ACCENT_COLOR[1]) * t),
                int(ACCENT_COLOR[2] + (WHITE[2] - ACCENT_COLOR[2]) * t),
            )
            base_surf = font_large.render(label, True, color)
            w, h = base_surf.get_size()
            scaled = pygame.transform.smoothscale(base_surf, (int(w * 1.08), int(h * 1.08)))
            surface.blit(scaled, (SCREEN_W // 2 - scaled.get_width() // 2,
                                  y - (scaled.get_height() - h) // 2))
            bar_w = int(w + 8 * math.sin(hover_t * 3))
            pygame.draw.rect(surface, color, (SCREEN_W // 2 - bar_w // 2, y + h + 6, bar_w, 2))
        else:
            dim = (int(WHITE[0] * 0.6), int(WHITE[1] * 0.6), int(WHITE[2] * 0.6))
            text = font_large.render(label, True, dim)
            surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
        desc_text = font_small.render(desc, True, (120, 120, 140))
        surface.blit(desc_text, (SCREEN_W // 2 - desc_text.get_width() // 2, y + 44))
    if context_label:
        ctx = font_small.render(context_label, True, (80, 80, 100))
        surface.blit(ctx, (SCREEN_W // 2 - ctx.get_width() // 2, SCREEN_H - 50))


def draw_difficulty_select(surface, font_large, font_small, selected: int,
                           menu_particles: list | None = None, hover_t: float = 0.0):
    draw_background(surface)
    if menu_particles is not None:
        _draw_menu_particles(surface, menu_particles, hover_t)
    title = font_large.render("SELECT DIFFICULTY", True, WHITE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 160))
    for i, name in enumerate(DIFFICULTY_OPTIONS):
        y = 290 + i * 90
        if i == selected:
            base_color = DIFFICULTY_COLORS[name]
            t = 0.15 * (0.5 + 0.5 * math.sin(hover_t * 2))
            color = (
                int(base_color[0] + (WHITE[0] - base_color[0]) * t),
                int(base_color[1] + (WHITE[1] - base_color[1]) * t),
                int(base_color[2] + (WHITE[2] - base_color[2]) * t),
            )
            base_surf = font_large.render(name, True, color)
            w, h = base_surf.get_size()
            scaled = pygame.transform.smoothscale(base_surf, (int(w * 1.08), int(h * 1.08)))
            surface.blit(scaled, (SCREEN_W // 2 - scaled.get_width() // 2,
                                  y - (scaled.get_height() - h) // 2))
            bar_w = int(w + 8 * math.sin(hover_t * 3))
            pygame.draw.rect(surface, color, (SCREEN_W // 2 - bar_w // 2, y + h + 6, bar_w, 2))
        else:
            bc = DIFFICULTY_COLORS[name]
            dim = (int(bc[0] * 0.6), int(bc[1] * 0.6), int(bc[2] * 0.6))
            text = font_large.render(name, True, dim)
            surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, y))
    hint = font_small.render("ESC  Back", True, (60, 60, 80))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 50))


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


def draw_game_over(surface, winner: int, p1, p2, font_title, font_large, selected: int, pulse_t: float, cpu_mode: bool = False):
    draw_background(surface)
    color = P1_COLOR if winner == 1 else P2_COLOR
    if cpu_mode and winner == 2:
        winner_label = "CPU WINS!"
    else:
        winner_label = f"PLAYER {winner} WINS!"
    winner_surf = font_title.render(winner_label, True, color)
    surface.blit(winner_surf, (SCREEN_W // 2 - winner_surf.get_width() // 2, 200))
    score_text = font_large.render(f"{p1.score}  —  {p2.score}", True, WHITE)
    surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, 310))
    for i, opt in enumerate(["REMATCH", "MENU"]):
        c = ACCENT_COLOR if i == selected else WHITE
        text = font_large.render(opt, True, c)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 420 + i * 70))


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


def draw_bracket(surface, tournament, font_large, font_small):
    draw_background(surface)
    txt = font_small.render("BRACKET — coming soon", True, (120, 120, 140))
    surface.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, SCREEN_H // 2))
