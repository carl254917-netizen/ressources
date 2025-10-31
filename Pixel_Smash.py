# Pixel Smash
import sys
import subprocess

# Fonction pour installer un module si nécessaire
def install_and_import(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installation du module manquant : {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        __import__(import_name)

# Vérifie et installe les modules nécessaires
install_and_import("pygame")

import math
import random
import pygame

# Initialisation
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Smash")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 24)
BIG_FONT = pygame.font.SysFont("Arial", 48)

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
RED = (200, 50, 50)
ORANGE = (255, 165, 0)
GREEN = (50, 200, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 50, 180)

incertitude_rebond=5

def normalize_vector(vx, vy, target_speed):
    length = math.sqrt(vx**2 + vy**2)
    if length == 0:
        return target_speed, -target_speed  # valeur par défaut
    scale = target_speed / length
    return [vx * scale, vy * scale]


# Classes
class Paddle:
    def __init__(self, speed):
        self.width = 100
        self.height = 15
        self.rect = pygame.Rect(WIDTH // 2 - self.width // 2, HEIGHT - 40, self.width, self.height)
        self.speed = speed  # vitesse initiale

    def set_speed(self, new_speed):
        self.speed = new_speed

    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        self.rect.clamp_ip(screen.get_rect())

    def draw(self):
        pygame.draw.rect(screen, BLUE, self.rect)

class Ball:
    def __init__(self, speed):
        self.radius = 10
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, self.radius * 2, self.radius * 2)
        self.base_speed = speed
        self.velocity = [0, 0]
        self.target_velocity = [speed, -speed]
        self.launch_timer = 0  # Compteur de lancement (en frames)
        self.launch_duration = 120  # 2 secondes à 60 FPS
        self.fire = False
        self.magnetic = False
        self.slow_timer = 0
        self.fire_timer = 0
        self.magnet_timer = 0
        self.attached_to_paddle = False
        self.just_bounced = False  # Pour éviter les rebonds multiples
        self.bigball_timer = 0
        self.original_radius = self.radius

    def move(self, paddle, keys):
        # Si attachée à la raquette
        if self.attached_to_paddle:
            self.rect.midbottom = paddle.rect.midtop
            if keys[pygame.K_SPACE]:
                self.attached_to_paddle = False
                self.launch_timer = 0  # relance progressive
            return

        if self.launch_timer < self.launch_duration:
            self.launch_timer += 1
            t = self.launch_timer / self.launch_duration
            self.velocity[0] = self.target_velocity[0] * t
            self.velocity[1] = self.target_velocity[1] * t
        else:
            # Une fois lancée, la vitesse reste constante
            self.velocity = self.target_velocity[:]

        factor = 0.5 if self.slow_timer > 0 else 1
        if self.slow_timer > 0:
            self.slow_timer -= 1

        self.rect.x += int(self.velocity[0] * factor)
        self.rect.y += int(self.velocity[1] * factor)

        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.rect.x *= 0.99
            self.just_bounced_bord=True
            self.velocity[0] *= -1
            self.target_velocity[0] *= -1
        if self.rect.top <= 0:
            self.velocity[1] *= -1
            self.target_velocity[1] *= -1

        if self.fire_timer > 0:
            self.fire_timer -= 1
        if self.fire_timer == 0:
            self.fire = False

        if self.magnet_timer > 0:
            self.magnet_timer -= 1
        if self.magnet_timer == 0:
            self.magnetic = False
        
        if self.bigball_timer > 0:
            self.bigball_timer -= 1
            if self.bigball_timer == 0:
                self.radius = self.original_radius

    def draw(self):
        if self.fire:
            color = RED
        elif self.magnetic:
            color = PURPLE
        elif self.slow_timer > 0:
            color = ORANGE
        else:
            color = WHITE
        pygame.draw.circle(screen, color, self.rect.center, self.radius)

class Block:
    def __init__(self, x, y, hits):
        self.rect = pygame.Rect(x, y, 70, 25)
        self.hits = hits

    def draw(self):
        color = RED if self.hits == 3 else ORANGE if self.hits == 2 else GREEN
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

class Bonus:
    def __init__(self, x, y, kind):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.kind = kind
        self.speed = 3

    def move(self):
        self.rect.y += self.speed

    def draw(self):
        color_map = {
            "expand": BLUE,
            "fire": RED,
            "magnet": PURPLE,
            "slow": ORANGE,
            "bigball": WHITE
        }
        color = color_map.get(self.kind, YELLOW)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        label = FONT.render(self.kind[0].upper(), True, BLACK)
        screen.blit(label, (self.rect.x + 4, self.rect.y + 2))

# Fonctions
def create_level():
    blocks = []
    for row in range(5):
        for col in range(10):
            x = col * 75 + 10
            y = row * 30 + 50
            hits = 3 - (row % 3)
            blocks.append(Block(x, y, hits))
    return blocks

def draw_hud(score, lives, level):
    hud = FONT.render(f"Score: {score}   Lives: {lives}   Level: {level}", True, WHITE)
    screen.blit(hud, (20, 10))

def show_message(text, subtext="Press SPACE to continue", Wait=True):
    screen.fill(BLACK)
    title = BIG_FONT.render(text, True, WHITE)
    subtitle = FONT.render(subtext, True, GRAY)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, HEIGHT // 2 + 10))
    pygame.display.flip()
    if Wait:
        wait_for_space()

def wait_for_space():
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False

# Boucle principale
def main():
    level = 1
    speed = 6 # ← C’est ici que tu définis la vitesse initiale
    paddle = Paddle(speed)
    ball = Ball(speed)
    blocks = create_level()
    bonuses = []

    score = 0
    lives = 3
    running = True

    show_message("PIXEL SMASH", "Press SPACE to start")

    while running:
        screen.fill(BLACK)
        keys = pygame.key.get_pressed()
        pygame.mouse.set_visible(False)

        # Relance manuelle si la balle est attachée à la raquette
        if ball.attached_to_paddle and keys[pygame.K_SPACE]:
            ball.attached_to_paddle = False
            ball.launch_timer = 0
            ball.target_velocity = normalize_vector(1, -1, ball.base_speed)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        paddle.move(keys)
        ball.move(paddle, keys)

        # Collision balle / raquette
        if ball.rect.colliderect(paddle.rect):
            if not ball.just_bounced:
                if ball.magnetic:
                    ball.attached_to_paddle = True
                    ball.velocity = [0, 0]
                    ball.target_velocity = [ball.base_speed, -ball.base_speed]
                else:
                    offset = (ball.rect.centerx - paddle.rect.centerx) / (paddle.width // 2)
                    vx = ball.base_speed * offset + incertitude_rebond*(random.random()*0.5)
                    vy = -ball.base_speed
                    ball.velocity = list(normalize_vector(vx, vy, ball.base_speed))
                    ball.target_velocity = ball.velocity[:]  # pour garder la cohérence
                    ball.launch_timer = ball.launch_duration  # désactive l’interpolation
                ball.just_bounced = True
        else:
            ball.just_bounced = False

        # Collision balle / blocs
        hit_blocks = [block for block in blocks if ball.rect.colliderect(block.rect)]
        if hit_blocks:
            if not ball.fire:
                ball.velocity[1] *= -1  # rebond une seule fois
                ball.target_velocity[1] *= -1
            for block in hit_blocks:
                block.hits -= 1
                score += 10
                if block.hits <= 0:
                    blocks.remove(block)
                    if random.random() < 0.2: # probabilité d'avoir un bonus
                        kind = random.choice(["expand", "fire", "magnet", "slow", "bigball"])
                        bonuses.append(Bonus(block.rect.x + 25, block.rect.y, kind))

        # Perte de balle
        if ball.rect.bottom >= HEIGHT:
            lives -= 1
            ball = Ball(speed)
            if lives <= 0:
                show_message("GAME OVER", subtext="", Wait=False)
                running = False
                pygame.time.wait(3000)

        # Bonus
        for bonus in bonuses[:]:
            bonus.move()
            if bonus.rect.colliderect(paddle.rect):
                if bonus.kind == "expand":
                    paddle.width = min(paddle.width + 30, 200)
                    paddle.rect.width = paddle.width
                elif bonus.kind == "fire":
                    ball.fire = True
                    ball.fire_timer = 300  # 5 secondes à 60 FPS
                elif bonus.kind == "magnet":
                    ball.magnetic = True
                    ball.magnet_timer = 300
                elif bonus.kind == "slow":
                    ball.slow_timer = 300
                elif bonus.kind == "bigball":
                    ball.radius = int(ball.original_radius * 1.7)
                    ball.bigball_timer = 300  # 5 secondes

                bonuses.remove(bonus)
            elif bonus.rect.top > HEIGHT:
                bonuses.remove(bonus)

        # Niveau terminé
        if not blocks:
            level += 1
            speed += 1
            paddle.set_speed(speed)
            ball = Ball(speed)
            blocks = create_level()
            show_message(f"Niveau {level}")

        # Dessin
        paddle.draw()
        ball.draw()
        for block in blocks:
            block.draw()
        for bonus in bonuses:
            bonus.draw()
        draw_hud(score, lives, level)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

main()



