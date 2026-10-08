import pygame
from .bird import Bird
from .pipe import Pipe
from .sounds import Sounds

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 150, 0)

READY, PLAYING, GAME_OVER = "ready", "playing", "game_over"
RESTART_DELAY_MS = 500  # stops a held/late Space press from instantly restarting

DIFFICULTIES = {
    "Easy":   {"speed": 3, "gap": 180, "interval": 110},
    "Medium": {"speed": 4, "gap": 150, "interval": 90},
    "Hard":   {"speed": 6, "gap": 120, "interval": 70},
}
DIFFICULTY_KEYS = {
    pygame.K_1: "Easy",   pygame.K_KP1: "Easy",
    pygame.K_2: "Medium", pygame.K_KP2: "Medium",
    pygame.K_3: "Hard",   pygame.K_KP3: "Hard",
}


def circle_rect_collide(cx, cy, r, rect):
    # Closest point on the rect to the circle's center
    nearest_x = max(rect.left, min(cx, rect.right))
    nearest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - nearest_x
    dy = cy - nearest_y
    return dx * dx + dy * dy <= r * r


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 64)
        self.quit_requested = False
        self.sounds = Sounds()
        self.reset()

    def reset(self, difficulty="Medium"):
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.pipe_speed = settings["speed"]
        self.pipe_gap = settings["gap"]
        self.pipe_interval = settings["interval"]
        self.bird = Bird(self.width // 4, self.height // 2)
        self._spawn_timer = 0
        self.pipes = [Pipe(self.width + 100, self.height, gap=self.pipe_gap, speed=self.pipe_speed)]
        self.score = 0
        self.state = READY
        self.game_over_time = 0

    def handle_event(self, event):
        flap_pressed = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) \
            or event.type == pygame.MOUSEBUTTONDOWN

        if self.state == READY and flap_pressed:
            self.state = PLAYING
            self.bird.flap()  # first flap starts the game
            self.sounds.flap.play()
        elif self.state == PLAYING and flap_pressed:
            self.bird.flap()
            self.sounds.flap.play()
        elif self.state == GAME_OVER and event.type == pygame.KEYDOWN:
            if pygame.time.get_ticks() - self.game_over_time < RESTART_DELAY_MS:
                return
            if event.key in DIFFICULTY_KEYS:
                self.reset(DIFFICULTY_KEYS[event.key])
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.quit_requested = True

    def handle_input(self):
        pass

    def end_game(self):
        self.state = GAME_OVER
        self.game_over_time = pygame.time.get_ticks()
        self.sounds.die.play()

    def update(self):
        if self.state != PLAYING:  # bird and pipes stay still in READY and GAME_OVER
            return

        self.bird.update()

        if self.bird.y - self.bird.radius <= 0 or self.bird.y + self.bird.radius >= self.height:
            self.end_game()
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.pipe_interval:
            self._spawn_timer = 0
            self.pipes.append(Pipe(self.width, self.height, gap=self.pipe_gap, speed=self.pipe_speed))

        for pipe in self.pipes:
            pipe.move()
            cx, cy = self.bird.center()
            r = self.bird.radius
            if circle_rect_collide(cx, cy, r, pipe.top_rect()) or \
               circle_rect_collide(cx, cy, r, pipe.bottom_rect()):
                self.end_game()
                return

            if not pipe.scored and pipe.x + pipe.width < self.bird.x:
                pipe.scored = True
                self.score += 1
                self.sounds.score.play()

        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def _draw_centered(self, screen, text, font, y):
        surf = font.render(text, True, WHITE)
        screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))

    def render(self, screen):
        for pipe in self.pipes:
            pygame.draw.rect(screen, GREEN, pipe.top_rect())
            pygame.draw.rect(screen, GREEN, pipe.bottom_rect())

        pygame.draw.circle(screen, WHITE, (int(self.bird.x), int(self.bird.y)), self.bird.radius)

        if self.state == READY:
            self._draw_centered(screen, "Press Space to start", self.font, self.height // 2 + 60)

        elif self.state == PLAYING:
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            screen.blit(score_text, (10, 10))

        elif self.state == GAME_OVER:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))  # dim the frozen scene
            screen.blit(overlay, (0, 0))
            cy = self.height // 2
            self._draw_centered(screen, "Game Over", self.big_font, cy - 50)
            self._draw_centered(screen, f"Score: {self.score}", self.font, cy + 10)
            self._draw_centered(screen, f"Difficulty: {self.difficulty}", self.font, cy + 45)
            self._draw_centered(screen, "1 Easy    2 Medium    3 Hard", self.font, cy + 85)
            self._draw_centered(screen, "Q / Esc to quit", self.font, cy + 120)