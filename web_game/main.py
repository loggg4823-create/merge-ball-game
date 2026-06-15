import pygame
import sys
import math
import random
import asyncio

pygame.init()
WIDTH, HEIGHT = 400, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Merge Ball!")
clock = pygame.time.Clock()

# ===== CONFIG =====
BALL_RADIUS = 10
GRAVITY = 0.3
TERMINAL_VELOCITY = 7
GROUND_FRICTION = 0.7
WALL_BOUNCE = 0.4
MERGE_SCALE = 1.35
GROUND_OFFSET = 20
DEADLINE_RATIO = 0.15
COUNTDOWN_SECONDS = 120
SPAWN_RATES = (0.65, 0.25, 0.10)

GROUND_Y = HEIGHT - GROUND_OFFSET
DEADLINE_Y = int(HEIGHT * DEADLINE_RATIO)

font = pygame.font.Font(None, 20)
big_font = pygame.font.Font(None, 36)
huge_font = pygame.font.Font(None, 56)

TIER_COLORS = [
    (160, 210, 255), (100, 200, 255), (60, 180, 255),
    (50, 210, 200), (60, 230, 140), (140, 240, 80),
    (220, 230, 60), (255, 190, 60), (255, 130, 80),
]
LEVEL_NAMES = ["Lv1", "Lv2", "Lv3", "Lv4", "Lv5", "Lv6", "Lv7", "Lv8", "Lv9"]


def get_tier(radius):
    if radius < BALL_RADIUS:
        return 0
    n = math.log(radius / BALL_RADIUS) / math.log(MERGE_SCALE)
    return min(round(n), len(TIER_COLORS) - 1)


def get_color_for_tier(tier):
    return TIER_COLORS[min(tier, len(TIER_COLORS) - 1)]


class Ball:
    def __init__(self, x, y, radius, vx=0, vy=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.mass = (radius ** 2) / 3
        self.tier = get_tier(radius)
        self.color = get_color_for_tier(self.tier)

    def update(self):
        self.vy += GRAVITY
        if self.vy > TERMINAL_VELOCITY:
            self.vy = TERMINAL_VELOCITY
        self.x += self.vx
        self.y += self.vy
        if self.y + self.radius >= GROUND_Y:
            self.y = GROUND_Y - self.radius
            self.vy = 0
            self.vx *= GROUND_FRICTION
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx * WALL_BOUNCE
        elif self.x + self.radius >= WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -self.vx * WALL_BOUNCE
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = -self.vy * WALL_BOUNCE
        if abs(self.vx) < 0.05:
            self.vx = 0

    def draw(self, surface):
        r = int(self.radius)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)
        hl = (int(self.x - r * 0.3), int(self.y - r * 0.3))
        pygame.draw.circle(surface, (255, 255, 255, 80), hl, max(1, r // 3))
        pygame.draw.circle(surface, (255, 255, 255, 40), (int(self.x), int(self.y)), r, 1)


class SpawnRipple:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 20
        self.max_life = 20

    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        progress = 1 - self.life / self.max_life
        r = progress * 50
        a = int(180 * (1 - progress))
        if a > 0:
            pygame.draw.circle(surface, (255, 255, 255, a), (int(self.x), int(self.y)), int(r), 2)


def do_collision(a, b):
    dx, dy = b.x - a.x, b.y - a.y
    dist = math.hypot(dx, dy)
    min_dist = a.radius + b.radius
    if dist >= min_dist or dist == 0:
        return False

    nx, ny = dx / dist, dy / dist
    overlap = min_dist - dist

    if a.tier == b.tier:
        nr = a.radius * MERGE_SCALE
        mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
        tm = a.mass + b.mass
        nvx = (a.vx * a.mass + b.vx * b.mass) / tm
        nvy = (a.vy * a.mass + b.vy * b.mass) / tm
        new_b = Ball(mx, my, nr, nvx, nvy)
        if a in balls and b in balls:
            ia, ib = balls.index(a), balls.index(b)
            if ia < ib:
                balls.pop(ib); balls.pop(ia)
            else:
                balls.pop(ia); balls.pop(ib)
            balls.append(new_b)
        return True

    tm = a.mass + b.mass
    up, lo = (a, b) if a.y < b.y else (b, a)
    h = overlap * abs(nx) * 1.1
    if h > 0.5:
        if up.x < lo.x:
            up.x -= h * (lo.mass / tm)
            lo.x += h * (up.mass / tm)
        else:
            up.x += h * (lo.mass / tm)
            lo.x -= h * (up.mass / tm)
    elif abs(nx) < 0.15 and overlap > 1:
        nudge = random.uniform(0.5, 1.5) * (-1 if random.random() < 0.5 else 1)
        up.x += nudge
    up.y -= overlap * max(0.3, abs(ny)) * 1.1
    return False


balls = []
ripples = []
effects = []
game_over = False
score = 0
time_remaining = COUNTDOWN_SECONDS
deadline_timer = 0.0


async def main():
    global balls, ripples, effects, game_over, score, time_remaining, deadline_timer

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    balls.clear(); ripples.clear(); effects.clear()
                    score = 0
                    time_remaining = COUNTDOWN_SECONDS
                    deadline_timer = 0.0
                    game_over = False
                elif event.pos[1] < DEADLINE_Y:
                    rnd = random.random()
                    st = 0
                    if rnd < SPAWN_RATES[1] + SPAWN_RATES[2]:
                        st = 1 if rnd < SPAWN_RATES[1] else 2
                    r = BALL_RADIUS * (MERGE_SCALE ** st)
                    balls.append(Ball(event.pos[0], event.pos[1], r))
                    ripples.append(SpawnRipple(event.pos[0], event.pos[1]))

        if not game_over:
            time_remaining -= dt
            if time_remaining <= 0:
                time_remaining = 0
                game_over = True

            for ball in balls:
                ball.update()

            for _ in range(3):
                i = 0
                while i < len(balls):
                    j = i + 1
                    while j < len(balls):
                        merged = do_collision(balls[i], balls[j])
                        if merged:
                            j = i + 1
                        else:
                            j += 1
                    i += 1

            for ball in balls:
                if ball.x - ball.radius < 0:
                    ball.x = ball.radius
                elif ball.x + ball.radius > WIDTH:
                    ball.x = WIDTH - ball.radius
                if ball.y - ball.radius < 0:
                    ball.y = ball.radius
                if ball.y + ball.radius > GROUND_Y:
                    ball.y = GROUND_Y - ball.radius

        ripples = [r for r in ripples if r.update()]

        screen.fill((20, 20, 30))
        pygame.draw.rect(screen, (40, 40, 55), (0, GROUND_Y, WIDTH, GROUND_OFFSET))
        pygame.draw.line(screen, (70, 70, 90), (0, GROUND_Y), (WIDTH, GROUND_Y), 1)

        for b in balls:
            b.draw(screen)
        for r in ripples:
            r.draw(screen)

        pygame.draw.line(screen, (220, 40, 40), (0, DEADLINE_Y), (WIDTH, DEADLINE_Y), 2)
        dl = font.render("DEADLINE", True, (200, 50, 50))
        screen.blit(dl, (WIDTH - dl.get_width() - 8, DEADLINE_Y + 4))

        m, s = int(time_remaining) // 60, int(time_remaining) % 60
        tc = (255, 220, 100) if time_remaining > 30 else (255, 100, 100)
        tt = big_font.render(f"{m:02d}:{s:02d}", True, tc)
        screen.blit(tt, (WIDTH // 2 - tt.get_width() // 2, 25))
        st = font.render(f"Score: {score}", True, (200, 200, 220))
        screen.blit(st, (10, 10))

        if game_over:
            ov = pygame.Surface((WIDTH, HEIGHT))
            ov.fill((0, 0, 0))
            ov.set_alpha(180)
            screen.blit(ov, (0, 0))
            gt = huge_font.render("GAME OVER", True, (255, 60, 60))
            screen.blit(gt, (WIDTH // 2 - gt.get_width() // 2, HEIGHT // 2 - 70))
            rt = big_font.render(f"Score: {score}", True, (255, 220, 100))
            screen.blit(rt, (WIDTH // 2 - rt.get_width() // 2, HEIGHT // 2))
            rt2 = font.render("Click to Restart", True, (180, 180, 200))
            screen.blit(rt2, (WIDTH // 2 - rt2.get_width() // 2, HEIGHT // 2 + 80))

        pygame.display.flip()

    pygame.quit()


asyncio.run(main())
