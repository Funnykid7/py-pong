import pygame
import math
import random
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
from src.entities import Paddle, Ball
from src.effects import ScreenShake, ParticleSystem, TransitionManager
from src.cpu import CPUController
import src.renderer as renderer


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU

        pygame.font.init()
        self.font_title = pygame.font.Font(None, 100)
        self.font_large = pygame.font.Font(None, 60)
        self.font_small = pygame.font.Font(None, 28)

        self.game_mode = MODE_FIRST_TO_11

        self.p1 = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
        self.p2 = Paddle(SCREEN_W - PADDLE_MARGIN - PADDLE_W // 2, 2)
        self.balls: list[Ball] = [Ball()]

        self.shake = ScreenShake()
        self.particles = ParticleSystem()
        self.transition = TransitionManager()
        self._quit_pending = False

        self.countdown = 0
        self.countdown_timer = 0.0
        self.time_left = float(TIMED_DURATION)
        self.sudden_death = False
        self.rally_count = 0

        self.p1_smash_meter = 0.0
        self.p2_smash_meter = 0.0
        self.p1_smash_ready = False
        self.p2_smash_ready = False
        self.smash_pulse_t = 0.0

        self.menu_selected = 0
        self.mode_selected = 0
        self.pause_selected = 0
        self.gameover_selected = 0
        self.gameover_pulse = 0.0
        self.winner = 0

        self.menu_ball_pos = pygame.Vector2(SCREEN_W // 2, SCREEN_H // 2)
        self.menu_ball_vel = pygame.Vector2(300, 220)

        self.menu_particles: list[dict] = self._make_menu_particles()
        self.menu_hover_t: float = 0.0

        self.opponent_type: str = OPPONENT_HUMAN
        self.cpu_difficulty: str = "MEDIUM"
        self.difficulty_selected: int = 1  # default highlight on MEDIUM
        self.cpu: CPUController | None = None

        # Tournament
        self.tournament: "TournamentManager | None" = None
        self._tournament_match_slots: tuple[int, int] = (0, 1)  # set by _setup_tournament_match; used in _end_match
        self._ts_size: int = 4
        self._ts_slots: list[int] = [0, 0, 2, 2]
        self._ts_row: int = 0

        self._init_audio()
        self._start_menu_music()

    def _init_audio(self):
        self.sfx: dict = {}
        for name, path in [
            ("hit",     "assets/sounds/ball hit.mp3"),
            ("point",   "assets/sounds/point.mp3"),
            ("victory", "assets/sounds/victory_screen.mp3"),
            ("losing",  "assets/sounds/losing_screen.mp3"),
            ("powerup", "assets/sounds/powerup.wav"),
        ]:
            try:
                self.sfx[name] = pygame.mixer.Sound(path)
            except Exception:
                self.sfx[name] = None

        self._menu_music_loaded = False
        try:
            pygame.mixer.music.load("assets/sounds/main theme.mp3")
            self._menu_music_loaded = True
        except Exception:
            pass

        self._bg_channel = pygame.mixer.Channel(0)
        self._bg_theme: pygame.mixer.Sound | None = None
        try:
            self._bg_theme = pygame.mixer.Sound("assets/sounds/background_theme.mp3")
            self._bg_theme.set_volume(0.05)
        except Exception:
            pass

    def _start_menu_music(self):
        if self._menu_music_loaded:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(-1)

    def _stop_menu_music(self):
        if self._menu_music_loaded:
            pygame.mixer.music.fadeout(500)  # async fade; countdown covers the 0.5s overlap

    def _play_sfx(self, name: str):
        sfx = self.sfx.get(name)
        if sfx:
            sfx.play()

    def _update_smash_meters(self, dt: float):
        p1_gap = max(0, self.p2.score - self.p1.score)
        self.p1_smash_meter = min(1.0, self.p1_smash_meter + (SMASH_BASE_CHARGE_RATE + p1_gap * SMASH_PER_POINT_CHARGE) * dt)
        if self.p1_smash_meter >= 1.0:
            self.p1_smash_ready = True

        if self.opponent_type != OPPONENT_CPU or (self.cpu and self.cpu.smash_enabled):
            p2_gap = max(0, self.p1.score - self.p2.score)
            self.p2_smash_meter = min(1.0, self.p2_smash_meter + (SMASH_BASE_CHARGE_RATE + p2_gap * SMASH_PER_POINT_CHARGE) * dt)
            if self.p2_smash_meter >= 1.0:
                self.p2_smash_ready = True

    def _activate_smash(self, player: int):
        if player == 1 and not self.p1_smash_ready:
            return
        if player == 2 and not self.p2_smash_ready:
            return
        activator = self.p1 if player == 1 else self.p2
        opponent = self.p2 if player == 1 else self.p1
        activator.activate_powerup("BIG_PADDLE")
        opponent.activate_powerup("SMALL_OPPONENT")
        self._play_sfx("powerup")
        if player == 1:
            self.p1_smash_meter = 0.0
            self.p1_smash_ready = False
        else:
            self.p2_smash_meter = 0.0
            self.p2_smash_ready = False

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    result = self._handle_event(event)
                    if result == "quit":
                        running = False
            self._update(dt)
            if self._quit_pending:
                running = False
            self._draw()
            pygame.display.flip()

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

    def _handle_difficulty_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.difficulty_selected = (self.difficulty_selected - 1) % 4
                self.menu_hover_t = 0.0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.difficulty_selected = (self.difficulty_selected + 1) % 4
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                diff = DIFFICULTY_OPTIONS[self.difficulty_selected]
                def _go_mode():
                    self.cpu_difficulty = diff
                    self.state = STATE_MODE_SELECT
                self.transition.start(_go_mode)
            elif event.key == pygame.K_ESCAPE:
                self.menu_hover_t = 0.0
                self.transition.start(lambda: setattr(self, "state", STATE_MENU))

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

    def _handle_mode_select_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.mode_selected = (self.mode_selected - 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_DOWN:
                self.mode_selected = (self.mode_selected + 1) % 3
                self.menu_hover_t = 0.0
            elif event.key == pygame.K_RETURN:
                modes = [MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED]
                mode = modes[self.mode_selected]
                def _start():
                    self.game_mode = mode
                    self._start_match()
                self.transition.start(_start)
            elif event.key == pygame.K_ESCAPE:
                self.menu_hover_t = 0.0
                if self.tournament is not None:
                    self.transition.start(lambda: setattr(self, "state", STATE_BRACKET))
                elif self.opponent_type == OPPONENT_CPU:
                    self.transition.start(lambda: setattr(self, "state", STATE_DIFFICULTY))
                else:
                    self.transition.start(lambda: setattr(self, "state", STATE_MENU))

    def _handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = STATE_PAUSED
                self.pause_selected = 0
            elif event.key == pygame.K_LSHIFT and self.countdown == 0:
                self._activate_smash(1)
            elif event.key == pygame.K_RSHIFT and self.countdown == 0 and self.opponent_type == OPPONENT_HUMAN:
                self._activate_smash(2)

    def _handle_paused_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = STATE_PLAYING
            elif event.key == pygame.K_UP:
                self.pause_selected = (self.pause_selected - 1) % 2
            elif event.key == pygame.K_DOWN:
                self.pause_selected = (self.pause_selected + 1) % 2
            elif event.key == pygame.K_RETURN:
                if self.pause_selected == 0:
                    self.state = STATE_PLAYING
                else:
                    self.transition.start(self._reset_to_menu)

    def _handle_gameover_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.gameover_selected = (self.gameover_selected - 1) % 2
            elif event.key == pygame.K_DOWN:
                self.gameover_selected = (self.gameover_selected + 1) % 2
            elif event.key == pygame.K_RETURN:
                if self.gameover_selected == 0:
                    self.transition.start(self._start_match)
                else:
                    self.transition.start(self._reset_to_menu)

    def _start_match(self):
        self._stop_menu_music()
        if self._bg_theme:
            self._bg_channel.play(self._bg_theme, loops=-1)
        self.p1.score = 0
        self.p2.score = 0
        self.p1.sets_won = 0
        self.p2.sets_won = 0
        self.p1.height = PADDLE_H
        self.p2.height = PADDLE_H
        self.p1.active_powerup = None
        self.p2.active_powerup = None
        self.time_left = float(TIMED_DURATION)
        self.sudden_death = False
        self.balls = [Ball()]
        self.particles.clear()
        self.rally_count = 0
        self.p1_smash_meter = 0.0
        self.p2_smash_meter = 0.0
        self.p1_smash_ready = False
        self.p2_smash_ready = False
        if self.opponent_type == OPPONENT_CPU:
            self.cpu = CPUController(self.cpu_difficulty)
        else:
            self.cpu = None
        self.state = STATE_PLAYING
        self._start_countdown()

    def _start_countdown(self):
        self.countdown = 3
        self.countdown_timer = 1.0

    def _reset_to_menu(self):
        self.state = STATE_MENU
        self.menu_selected = 0
        self.menu_hover_t = 0.0
        self.shake.trauma = 0.0
        self._bg_channel.stop()
        self._start_menu_music()

    def _update(self, dt: float):
        self.menu_hover_t = (self.menu_hover_t + dt) % (2 * math.pi)
        self.transition.update(dt)
        if self.state == STATE_MENU:
            self._update_menu(dt)
        elif self.state in (STATE_DIFFICULTY, STATE_MODE_SELECT):
            self._update_menu_particles(dt)
        elif self.state in (STATE_TOURNAMENT_SETUP, STATE_BRACKET):
            self._update_menu_particles(dt)
        elif self.state == STATE_PLAYING:
            self._update_playing(dt)
        elif self.state == STATE_GAME_OVER:
            self.gameover_pulse += dt
            self.particles.update(dt)

    def _update_menu(self, dt: float):
        self.menu_ball_pos += self.menu_ball_vel * dt
        if self.menu_ball_pos.x < 0 or self.menu_ball_pos.x > SCREEN_W:
            self.menu_ball_vel.x *= -1
        if self.menu_ball_pos.y < 0 or self.menu_ball_pos.y > SCREEN_H:
            self.menu_ball_vel.y *= -1
        self._update_menu_particles(dt)

    def _make_menu_particles(self) -> list[dict]:
        particles = []
        for _ in range(60):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(15, 40)
            particles.append({
                "pos": pygame.Vector2(
                    random.uniform(0, SCREEN_W),
                    random.uniform(0, SCREEN_H),
                ),
                "vel": pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed),
                "phase": random.uniform(0, 2 * math.pi),
                "color": random.choice([P1_COLOR, P2_COLOR]),
                "radius": random.randint(2, 4),
            })
        return particles

    def _update_menu_particles(self, dt: float):
        for p in self.menu_particles:
            p["pos"] += p["vel"] * dt
            if p["pos"].x < 0:
                p["pos"].x = SCREEN_W
            elif p["pos"].x > SCREEN_W:
                p["pos"].x = 0
            if p["pos"].y < 0:
                p["pos"].y = SCREEN_H
            elif p["pos"].y > SCREEN_H:
                p["pos"].y = 0

    def _update_playing(self, dt: float):
        if self.countdown > 0:
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.countdown -= 1
                self.countdown_timer = 1.0
            return

        keys = pygame.key.get_pressed()
        self.p1.vel.y = -PADDLE_SPEED if keys[pygame.K_w] else (PADDLE_SPEED if keys[pygame.K_s] else 0)
        if self.cpu is not None:
            self.cpu.update(dt, self.balls[0], self.p2)
        else:
            self.p2.vel.y = -PADDLE_SPEED if keys[pygame.K_UP] else (PADDLE_SPEED if keys[pygame.K_DOWN] else 0)

        self.p1.update(dt)
        self.p2.update(dt)
        for ball in self.balls:
            ball.update(dt)

        self._handle_collisions()
        self._update_smash_meters(dt)
        if self.cpu is not None and self.cpu.should_smash(self.balls[0], self.p1, self.p2_smash_ready):
            self._activate_smash(2)
        self.smash_pulse_t += dt
        self.shake.update(dt)
        self.particles.update(dt)

        if self.game_mode == MODE_TIMED:
            self.time_left -= dt
            if self.time_left <= 0:
                if not self.sudden_death and self.p1.score == self.p2.score:
                    self.sudden_death = True
                    self.time_left = float(SUDDEN_DEATH_DURATION)
                else:
                    self._end_match()


    def _handle_collisions(self):
        scored: list[tuple[int, Ball]] = []
        for ball in list(self.balls):
            # Wall bounce
            if ball.pos.y - BALL_SIZE // 2 <= HUD_HEIGHT:
                ball.pos.y = HUD_HEIGHT + BALL_SIZE // 2
                ball.bounce_wall()
            elif ball.pos.y + BALL_SIZE // 2 >= SCREEN_H:
                ball.pos.y = SCREEN_H - BALL_SIZE // 2
                ball.bounce_wall()

            # Paddle collisions
            if ball.vel.x < 0 and ball.rect.colliderect(self.p1.rect):
                ball.pos.x = self.p1.rect.right + BALL_SIZE // 2
                ball.bounce_paddle(self.p1)
                self.rally_count += 1
                self.shake.add_trauma(SHAKE_HIT_TRAUMA)
                self._play_sfx("hit")
            elif ball.vel.x > 0 and ball.rect.colliderect(self.p2.rect):
                ball.pos.x = self.p2.rect.left - BALL_SIZE // 2
                ball.bounce_paddle(self.p2)
                self.rally_count += 1
                self.shake.add_trauma(SHAKE_HIT_TRAUMA)
                self._play_sfx("hit")

            if ball.pos.x < 0:
                scored.append((2, ball))
            elif ball.pos.x > SCREEN_W:
                scored.append((1, ball))

        for scorer, ball in scored:
            if ball in self.balls:
                self._score(scorer, ball)

    def _score(self, scorer: int, scored_ball: Ball):
        if self.state != STATE_PLAYING:
            return
        self._play_sfx("point")
        wall_x = 0.0 if scorer == 2 else float(SCREEN_W)
        color = P2_COLOR if scorer == 2 else P1_COLOR
        self.particles.emit_score(wall_x, color)
        self.shake.add_trauma(SHAKE_SCORE_TRAUMA)

        if scorer == 1:
            self.p1.score += 1
        else:
            self.p2.score += 1

        if len(self.balls) > 1:
            self.balls.remove(scored_ball)
        else:
            scored_ball.reset()
            self._start_countdown()

        self.rally_count = 0

        if self.game_mode == MODE_FIRST_TO_11:
            if self.p1.score >= CLASSIC_WIN_SCORE:
                self._end_match(winner=1)
            elif self.p2.score >= CLASSIC_WIN_SCORE:
                self._end_match(winner=2)
        elif self.game_mode == MODE_BEST_OF_3:
            self._check_set_win()

    def _check_set_win(self):
        for player, paddle in [(1, self.p1), (2, self.p2)]:
            if paddle.score >= SET_WIN_SCORE:
                paddle.sets_won += 1
                self.p1.score = 0
                self.p2.score = 0
                self.p1_smash_meter = 0.0
                self.p2_smash_meter = 0.0
                self.p1_smash_ready = False
                self.p2_smash_ready = False
                if paddle.sets_won >= MATCH_WIN_SETS:
                    self._end_match(winner=player)
                else:
                    self._start_countdown()
                return

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
            self._bg_channel.fadeout(500)  # mirrors fadeout in non-tournament path below
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

    def _draw(self):
        if self.state == STATE_PLAYING:
            offset = self.shake.get_offset()
        else:
            offset = pygame.Vector2(0, 0)
        game_surf = pygame.Surface((SCREEN_W, SCREEN_H))

        if self.state == STATE_MENU:
            renderer.draw_menu(game_surf, self.font_title, self.font_large, self.font_small,
                               self.menu_selected, (self.menu_ball_pos.x, self.menu_ball_pos.y),
                               self.menu_particles, self.menu_hover_t)
        elif self.state == STATE_DIFFICULTY:
            renderer.draw_difficulty_select(game_surf, self.font_large, self.font_small,
                                            self.difficulty_selected,
                                            self.menu_particles, self.menu_hover_t)
        elif self.state == STATE_MODE_SELECT:
            context = f"1vCPU · {self.cpu_difficulty}" if self.opponent_type == OPPONENT_CPU else None
            renderer.draw_mode_select(game_surf, self.font_large, self.font_small,
                                      self.mode_selected, context,
                                      self.menu_particles, self.menu_hover_t)
        elif self.state in (STATE_PLAYING, STATE_PAUSED):
            renderer.draw_background(game_surf)
            for ball in self.balls:
                renderer.draw_ball(game_surf, ball)
            renderer.draw_paddle(game_surf, self.p1)
            renderer.draw_paddle(game_surf, self.p2)
            renderer.draw_particles(game_surf, self.particles.particles)
            is_cpu = self.opponent_type == OPPONENT_CPU
            cpu_smash_on = is_cpu and self.cpu is not None and self.cpu.smash_enabled
            p2_smash_val = self.p2_smash_meter if (not is_cpu or cpu_smash_on) else 0.0
            p2_ready_val = self.p2_smash_ready if (not is_cpu or cpu_smash_on) else False
            renderer.draw_hud(
                game_surf, self.p1, self.p2, self.font_large, self.font_small,
                self.game_mode,
                self.time_left if self.game_mode == MODE_TIMED else None,
                (self.p1.sets_won, self.p2.sets_won) if self.game_mode == MODE_BEST_OF_3 else None,
                self.p1_smash_meter, p2_smash_val,
                self.p1_smash_ready, p2_ready_val,
                self.smash_pulse_t,
                cpu_mode=is_cpu,
            )
            if self.countdown > 0:
                renderer.draw_countdown(game_surf, self.countdown, self.font_title)
            if self.state == STATE_PAUSED:
                renderer.draw_pause(game_surf, self.font_large, self.pause_selected)
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
        elif self.state == STATE_GAME_OVER:
            renderer.draw_game_over(game_surf, self.winner, self.p1, self.p2,
                                    self.font_title, self.font_large,
                                    self.gameover_selected, self.gameover_pulse,
                                    cpu_mode=(self.opponent_type == OPPONENT_CPU))
            renderer.draw_particles(game_surf, self.particles.particles)

        self.transition.draw(game_surf)
        self.screen.fill(BG_COLOR)
        self.screen.blit(game_surf, (int(offset.x), int(offset.y)))
