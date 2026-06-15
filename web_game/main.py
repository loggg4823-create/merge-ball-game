import pygame
import sys
import math
import random

# ============================
#      CONFIG
# ============================
BALL_RADIUS = 10            # base ball radius
GRAVITY = 0.3               # gravity
TERMINAL_VELOCITY = 7       # terminal velocity
GROUND_FRICTION = 0.7       # ground friction
WALL_BOUNCE = 0.4           # wall bounce
MERGE_SCALE = 1.35          # merge scale
GROUND_OFFSET = 20          # ground offset
DEADLINE_RATIO = 0.15       # deadline ratio
COLLISION_STIFFNESS = 0.3   # collision stiffness
COLLISION_DAMPING = 0.2     # collision damping
COUNTDOWN_SECONDS = 120     # countdown seconds
SPAWN_RATES = (0.65, 0.25, 0.10)  # spawn rates

# ============================
#     init
# ============================
pygame.init()
WIDTH, HEIGHT = 400, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Merge Ball!")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 20)
big_font = pygame.font.Font(None, 36)
huge_font = pygame.font.Font(None, 56)

GROUND_Y = HEIGHT - GROUND_OFFSET
DEADLINE_Y = int(HEIGHT * DEADLINE_RATIO)
balls = []
effects = []
ripples = []
game_over = False
score = 0
time_remaining = COUNTDOWN_SECONDS
deadline_timer = 0.0
ball_limit_warned = False

# ============================
#     colors
# ============================
TIER_COLORS = [
    (160, 210, 255),   # 1
    (100, 200, 255),   # 2
    (60, 180, 255),    # 3
    (50, 210, 200),    # 4
    (60, 230, 140),    # 5
    (140, 240, 80),    # 6
    (220, 230, 60),    # 7
    (255, 190, 60),    # 8
    (255, 130, 80),    # 9
]
LEVEL_NAMES = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]


def get_tier(radius):
    if radius < BALL_RADIUS:
        return 0
    n = math.log(radius / BALL_RADIUS) / math.log(MERGE_SCALE)
    return min(round(n), len(TIER_COLORS) - 1)


def get_color_for_tier(tier):
    return TIER_COLORS[min(tier, len(TIER_COLORS) - 1)]


# (sounds disabled on web for compatibility)


# ============================
#     visual fx
# ============================
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
        radius = progress * 50
        alpha = int(180 * (1 - progress))
        if alpha > 0 and radius > 0:
            color = (255, 255, 255, alpha)
            pygame.draw.circle(surface, color[:3], (int(self.x), int(self.y)), int(radius), 2)


class MergeEffect:
    def __init__(self, x, y, color, tier):
        self.x = x
        self.y = y
        self.color = color
        self.tier = tier
        self.life = 18
        self.max_life = 18
        self.particles = []
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 4)
            self.particles.append([0, angle, speed])

    def update(self):
        self.life -= 1
        for p in self.particles:
            p[0] += p[2]
        return self.life > 0

    def draw(self, surface):
        progress = 1 - self.life / self.max_life

        if progress < 0.12:
            alpha = int(80 * (1 - progress / 0.12))
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            surface.blit(flash, (0, 0))

        ring_radius = int(progress * 60)
        ring_alpha = int(180 * (1 - progress))
        if ring_alpha > 0 and ring_radius > 0:
            pygame.draw.circle(surface, (*self.color, ring_alpha)[:3],
                               (int(self.x), int(self.y)), ring_radius, 2)

        for p in self.particles:
            dist = p[0]
            angle = p[1]
            px = int(self.x + math.cos(angle) * dist)
            py = int(self.y + math.sin(angle) * dist)
            particle_alpha = int(255 * (1 - progress))
            size = max(1, int(3 * (1 - progress)))
            if particle_alpha > 0:
                pygame.draw.circle(surface, self.color, (px, py), size)


# ============================
#     Ball 
# ============================
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
        self.growing = 0
        self.display_radius = radius

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

        if self.growing > 0:
            self.growing -= 1
            total = 18
            progress = 1 - self.growing / total
            eased = 1 - pow(1 - progress, 3)
            self.display_radius = max(1, self.radius * eased)

    def draw(self, surface):
        r = int(self.display_radius if self.growing > 0 else self.radius)
        if r <= 0:
            return
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)
        highlight_pos = (int(self.x - r * 0.3), int(self.y - r * 0.3))
        highlight_r = max(1, r // 3)
        pygame.draw.circle(surface, (255, 255, 255, 80), highlight_pos, highlight_r)
        pygame.draw.circle(surface, (255, 255, 255, 40), (int(self.x), int(self.y)), r, 1)


# ============================
#     collision & merge
# ============================
def resolve_collision(a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    dist = math.hypot(dx, dy)
    min_dist = a.radius + b.radius

    if dist >= min_dist or dist == 0:
        return False

    nx = dx / dist
    ny = dy / dist
    overlap = min_dist - dist

    if a.tier == b.tier and a.radius * b.radius > 0:
        merge_balls(a, b)
        return True
    else:
        elastic_bounce(a, b, nx, ny, overlap)
        return False


def merge_balls(a, b):
    global score, effects

    new_radius = a.radius * MERGE_SCALE
    new_x = (a.x + b.x) / 2
    new_y = (a.y + b.y) / 2
    total_mass = a.mass + b.mass
    new_vx = (a.vx * a.mass + b.vx * b.mass) / total_mass
    new_vy = (a.vy * a.mass + b.vy * b.mass) / total_mass

    new_tier = get_tier(new_radius)
    bonus = max(0, new_tier - 2) * 2
    score += new_tier + bonus

    effects.append(MergeEffect(new_x, new_y, a.color, new_tier))

    new_ball = Ball(new_x, new_y, new_radius, new_vx, new_vy)
    new_ball.growing = 18
    new_ball.display_radius = 0

    # audio disabled on web

    global balls
    if a in balls and b in balls:
        idx_a = balls.index(a)
        idx_b = balls.index(b)
        if idx_a < idx_b:
            balls.pop(idx_b)
            balls.pop(idx_a)
        else:
            balls.pop(idx_a)
            balls.pop(idx_b)
        balls.append(new_ball)


def elastic_bounce(a, b, nx, ny, overlap):
    total_mass = a.mass + b.mass

    if a.y < b.y:
        upper, lower = a, b
    else:
        upper, lower = b, a

    horiz = overlap * abs(nx) * 1.1
    if horiz > 0.5:
        if upper.x < lower.x:
            upper.x -= horiz * (lower.mass / total_mass)
            lower.x += horiz * (upper.mass / total_mass)
        else:
            upper.x += horiz * (lower.mass / total_mass)
            lower.x -= horiz * (upper.mass / total_mass)
    elif abs(nx) < 0.15 and overlap > 1:
        nudge = random.uniform(0.5, 1.5) * (1 if random.random() < 0.5 else -1)
        upper.x += nudge

    vert = overlap * max(0.3, abs(ny)) * 1.1
    upper.y -= vert


# ============================
#     main loop
# ============================
running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_over:
                balls.clear()
                effects.clear()
                ripples.clear()
                score = 0
                time_remaining = COUNTDOWN_SECONDS
                deadline_timer = 0.0
                game_over = False
            elif event.pos[1] < DEADLINE_Y:
                rnd = random.random()
                if rnd < SPAWN_RATES[1] + SPAWN_RATES[2]:
                    spawn_tier = 1 if rnd < SPAWN_RATES[1] else 2
                else:
                    spawn_tier = 0
                r = BALL_RADIUS * (MERGE_SCALE ** spawn_tier)
                new_ball = Ball(event.pos[0], event.pos[1], r)
                balls.append(new_ball)
                ripples.append(SpawnRipple(event.pos[0], event.pos[1]))
                # audio disabled on web

    if not game_over:
        time_remaining -= dt
        if time_remaining <= 0:
            time_remaining = 0
            game_over = True
            # audio disabled on web

        ball_above = any(ball.y - ball.radius < DEADLINE_Y for ball in balls)
        if ball_above:
            deadline_timer += dt
            if deadline_timer >= 3.0:
                game_over = True
                # audio disabled on web
        else:
            deadline_timer = 0

        ball_limit_warned = len(balls) >= 500

        for ball in balls:
            ball.update()

        for _ in range(3):
            i = 0
            while i < len(balls):
                j = i + 1
                while j < len(balls):
                    merged = resolve_collision(balls[i], balls[j])
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
    effects = [e for e in effects if e.update()]

    screen.fill((20, 20, 30))

    pygame.draw.rect(screen, (40, 40, 55), (0, GROUND_Y, WIDTH, GROUND_OFFSET))
    pygame.draw.line(screen, (70, 70, 90), (0, GROUND_Y), (WIDTH, GROUND_Y), 1)

    for ball in balls:
        ball.draw(screen)
    for r in ripples:
        r.draw(screen)
    for e in effects:
        e.draw(screen)

    # Deadline 
    pygame.draw.line(screen, (220, 40, 40), (0, DEADLINE_Y), (WIDTH, DEADLINE_Y), 2)
    pygame.draw.line(screen, (255, 60, 60, 40), (0, DEADLINE_Y + 1), (WIDTH, DEADLINE_Y + 1), 1)
    dl_label = font.render(" DEADLINE", True, (200, 50, 50))
    screen.blit(dl_label, (WIDTH - dl_label.get_width() - 8, DEADLINE_Y + 4))

    # Deadline 
    if not game_over and deadline_timer > 0.5:
        warn_color = (255, min(200, int(200 * deadline_timer / 3.0)), 50)
        warn_text = big_font.render(f" {3.0 - deadline_timer:.1f}s", True, warn_color)
        screen.blit(warn_text, (WIDTH // 2 - warn_text.get_width() // 2, DEADLINE_Y + 30))

    if ball_limit_warned:
        limit_text = font.render(" Balls", True, (255, 180, 50))
        screen.blit(limit_text, (WIDTH // 2 - limit_text.get_width() // 2, DEADLINE_Y + 60))

    # HUD
    mins = int(time_remaining) // 60
    secs = int(time_remaining) % 60
    timer_text = big_font.render(f"{mins:02d}:{secs:02d}", True,
                                 (255, 220, 100) if time_remaining > 30 else (255, 100, 100))
    timer_rect = timer_text.get_rect(center=(WIDTH // 2, 25))
    screen.blit(timer_text, timer_rect)

    score_text = font.render(f"Score: {score}", True, (200, 200, 220))
    screen.blit(score_text, (10, 10))

    if balls:
        max_tier = max(b.tier for b in balls)
        info = font.render(
            f"Balls: {len(balls)} | Max: {LEVEL_NAMES[min(max_tier, len(LEVEL_NAMES)-1)]}",
            True, (160, 160, 180))
    else:
        info = font.render("Balls: 0", True, (160, 160, 180))
    screen.blit(info, (10, 35))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        go_text = huge_font.render("GAME OVER", True, (255, 60, 60))
        screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 70))

        result_text = big_font.render(f"Final Score: {score}", True, (255, 220, 100))
        screen.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, HEIGHT // 2))

        if balls:
            max_tier = max(b.tier for b in balls)
            tier_text = font.render(
                f"Best: {LEVEL_NAMES[min(max_tier, len(LEVEL_NAMES)-1)]}",
                True, (200, 200, 220))
            screen.blit(tier_text, (WIDTH // 2 - tier_text.get_width() // 2, HEIGHT // 2 + 40))

        restart_text = font.render("Click to Restart", True, (180, 180, 200))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 80))

    pygame.display.flip()

pygame.quit()
