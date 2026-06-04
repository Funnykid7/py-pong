import random
import pygame
from src.constants import (
    SCREEN_W, SCREEN_H, FPS, HUD_HEIGHT, BG_COLOR,
    PADDLE_W, PADDLE_H, PADDLE_MARGIN, PADDLE_SPEED,
    BALL_SIZE, BALL_SPEED_INITIAL,
    POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX, POWERUP_DURATION,
    MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED,
    TIMED_DURATION, SUDDEN_DEATH_DURATION, SET_WIN_SCORE,
    MATCH_WIN_SETS, CLASSIC_WIN_SCORE,
    STATE_MENU, STATE_MODE_SELECT, STATE_PLAYING,
    STATE_PAUSED, STATE_GAME_OVER,
    SHAKE_HIT_TRAUMA, SHAKE_SCORE_TRAUMA,
    P1_COLOR, P2_COLOR,
)
from src.entities import Paddle, Ball, PowerUp, PowerUpType
from src.effects import ScreenShake, ParticleSystem
import src.renderer as renderer


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU

        pygame.font.init()
        self.font_title = pygame.font.SysFont(None, 100)
        self.font_large = pygame.font.SysFont(None, 60)
        self.font_small = pygame.font.SysFont(None, 28)

        self.game_mode = MODE_FIRST_TO_11

        self.p1 = Paddle(PADDLE_MARGIN + PADDLE_W // 2, 1)
        self.p2 = Paddle(SCREEN_W - PADDLE_MARGIN - PADDLE_W // 2, 2)
        self.balls: list[Ball] = [Ball()]
        self.powerup: PowerUp | None = None

        self.shake = ScreenShake()
        self.particles = ParticleSystem()

        self.countdown = 0
        self.countdown_timer = 0.0
        self.powerup_spawn_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)
        self.time_left = float(TIMED_DURATION)
        self.sudden_death = False
        self.rally_count = 0

        self.menu_selected = 0
        self.mode_selected = 0
        self.pause_selected = 0
        self.gameover_selected = 0
        self.gameover_pulse = 0.0
        self.winner = 0

        self.menu_ball_pos = pygame.Vector2(SCREEN_W // 2, SCREEN_H // 2)
        self.menu_ball_vel = pygame.Vector2(300, 220)

        self._init_audio()
        self._start_menu_music()

    def _init_audio(self):
        self.sfx: dict = {}
        for name, path in [
            ("hit", "assets/sounds/ball hit.mp3"),
            ("score", "assets/sounds/score.wav"),
            ("powerup", "assets/sounds/powerup.wav"),
            ("win", "assets/sounds/win.wav"),
        ]:
            try:
                self.sfx[name] = pygame.mixer.Sound(path)
            except Exception:
                self.sfx[name] = None

        self.music_channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
        self.music_normal = None
        self.music_intense = None
        try:
            self.music_normal = pygame.mixer.Sound("assets/sounds/music_normal.ogg")
            self.music_intense = pygame.mixer.Sound("assets/sounds/music_intense.ogg")
        except Exception:
            pass
        self.current_music = "normal"

        self._menu_music_loaded = False
        try:
            pygame.mixer.music.load("assets/sounds/main theme.mp3")
            self._menu_music_loaded = True
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

    def _update_music(self):
        if not self.music_normal or not self.music_intense:
            return
        if self.rally_count >= 5 and self.current_music == "normal":
            self.music_channels[0].fadeout(500)
            self.music_channels[1].play(self.music_intense, loops=-1, fade_ms=500)
            self.music_channels[0], self.music_channels[1] = self.music_channels[1], self.music_channels[0]
            self.current_music = "intense"
        elif self.rally_count < 5 and self.current_music == "intense":
            self.music_channels[0].fadeout(500)
            self.music_channels[1].play(self.music_normal, loops=-1, fade_ms=500)
            self.music_channels[0], self.music_channels[1] = self.music_channels[1], self.music_channels[0]
            self.current_music = "normal"

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
            self._draw()
            pygame.display.flip()

    def _handle_event(self, event):
        if self.state == STATE_MENU:
            return self._handle_menu_event(event)
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
                self.menu_selected = (self.menu_selected - 1) % 2
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % 2
            elif event.key == pygame.K_RETURN:
                if self.menu_selected == 0:
                    self.state = STATE_MODE_SELECT
                else:
                    return "quit"

    def _handle_mode_select_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.mode_selected = (self.mode_selected - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.mode_selected = (self.mode_selected + 1) % 3
            elif event.key == pygame.K_RETURN:
                modes = [MODE_FIRST_TO_11, MODE_BEST_OF_3, MODE_TIMED]
                self.game_mode = modes[self.mode_selected]
                self._start_match()

    def _handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = STATE_PAUSED
            self.pause_selected = 0

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
                    self._reset_to_menu()

    def _handle_gameover_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.gameover_selected = (self.gameover_selected - 1) % 2
            elif event.key == pygame.K_DOWN:
                self.gameover_selected = (self.gameover_selected + 1) % 2
            elif event.key == pygame.K_RETURN:
                if self.gameover_selected == 0:
                    self._start_match()
                else:
                    self._reset_to_menu()

    def _start_match(self):
        self._stop_menu_music()
        if self.music_normal:
            self.music_channels[0].play(self.music_normal, loops=-1)
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
        self.powerup = None
        self.powerup_spawn_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)
        self.particles.clear()
        self.rally_count = 0
        self.state = STATE_PLAYING
        self._start_countdown()

    def _start_countdown(self):
        self.countdown = 3
        self.countdown_timer = 1.0

    def _reset_to_menu(self):
        self.state = STATE_MENU
        self.menu_selected = 0
        self._start_menu_music()

    def _update(self, dt: float):
        if self.state == STATE_MENU:
            self._update_menu(dt)
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

    def _update_playing(self, dt: float):
        if self.countdown > 0:
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.countdown -= 1
                self.countdown_timer = 1.0
            return

        keys = pygame.key.get_pressed()
        self.p1.vel.y = -PADDLE_SPEED if keys[pygame.K_w] else (PADDLE_SPEED if keys[pygame.K_s] else 0)
        self.p2.vel.y = -PADDLE_SPEED if keys[pygame.K_UP] else (PADDLE_SPEED if keys[pygame.K_DOWN] else 0)

        self.p1.update(dt)
        self.p2.update(dt)
        for ball in self.balls:
            ball.update(dt)

        self._handle_collisions()
        self._update_powerup(dt)
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

        self._update_music()

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
        self._play_sfx("score")
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
        self.winner = winner
        self._play_sfx("win")
        self.particles.emit_score(SCREEN_W if winner == 1 else 0,
                                  P1_COLOR if winner == 1 else P2_COLOR)
        self.gameover_pulse = 0.0
        self.gameover_selected = 0
        self.state = STATE_GAME_OVER

    def _update_powerup(self, dt: float):
        if self.powerup is None:
            self.powerup_spawn_timer -= dt
            if self.powerup_spawn_timer <= 0:
                self.powerup = PowerUp()
                self.powerup_spawn_timer = random.uniform(POWERUP_SPAWN_MIN, POWERUP_SPAWN_MAX)

        if self.powerup:
            self.powerup.update(dt)
            for ball in self.balls:
                if self.powerup.check_collection(ball):
                    self._activate_powerup(self.powerup, ball)
                    self.powerup = None
                    break

    def _activate_powerup(self, powerup: PowerUp, ball: Ball):
        self._play_sfx("powerup")
        beneficiary = self.p1 if ball.last_touch == 1 else self.p2
        opponent = self.p2 if ball.last_touch == 1 else self.p1

        ptype = powerup.type
        if ptype == PowerUpType.SPEED_BOOST:
            for b in self.balls:
                b.vel *= 1.5
            beneficiary.activate_powerup(ptype)
        elif ptype == PowerUpType.SLOW_BALL:
            for b in self.balls:
                b.vel *= 0.6
            beneficiary.activate_powerup(ptype)
        elif ptype == PowerUpType.BIG_PADDLE:
            beneficiary.activate_powerup(ptype)
        elif ptype == PowerUpType.SMALL_OPPONENT:
            opponent.activate_powerup(ptype)
        elif ptype == PowerUpType.MULTI_BALL:
            new_ball = Ball()
            new_ball.last_touch = ball.last_touch
            self.balls.append(new_ball)
            beneficiary.activate_powerup(ptype)

    def _draw(self):
        offset = self.shake.get_offset()
        game_surf = pygame.Surface((SCREEN_W, SCREEN_H))

        if self.state == STATE_MENU:
            renderer.draw_menu(game_surf, self.font_title, self.font_large, self.font_small,
                               self.menu_selected, (self.menu_ball_pos.x, self.menu_ball_pos.y))
        elif self.state == STATE_MODE_SELECT:
            renderer.draw_mode_select(game_surf, self.font_large, self.font_small, self.mode_selected)
        elif self.state in (STATE_PLAYING, STATE_PAUSED):
            renderer.draw_background(game_surf)
            for ball in self.balls:
                renderer.draw_ball(game_surf, ball)
            renderer.draw_paddle(game_surf, self.p1)
            renderer.draw_paddle(game_surf, self.p2)
            if self.powerup:
                renderer.draw_powerup(game_surf, self.powerup)
            renderer.draw_particles(game_surf, self.particles.particles)
            renderer.draw_hud(
                game_surf, self.p1, self.p2, self.font_large, self.font_small,
                self.game_mode,
                self.time_left if self.game_mode == MODE_TIMED else None,
                (self.p1.sets_won, self.p2.sets_won) if self.game_mode == MODE_BEST_OF_3 else None,
            )
            if self.countdown > 0:
                renderer.draw_countdown(game_surf, self.countdown, self.font_title)
            if self.state == STATE_PAUSED:
                renderer.draw_pause(game_surf, self.font_large, self.pause_selected)
        elif self.state == STATE_GAME_OVER:
            renderer.draw_game_over(game_surf, self.winner, self.p1, self.p2,
                                    self.font_title, self.font_large,
                                    self.gameover_selected, self.gameover_pulse)
            renderer.draw_particles(game_surf, self.particles.particles)

        self.screen.fill(BG_COLOR)
        self.screen.blit(game_surf, (int(offset.x), int(offset.y)))
