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
install_and_import("hashlib")
install_and_import("functools")

import pygame
import hashlib
import random
import math
from functools import lru_cache

# ==========================================
# CONFIGURATION ET CONSTANTES
# ==========================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CELL_SIZE = 50       # Taille d'une case
BLOCK_SIZE = 10      # Taille d'un bloc (10x10 cases)
FPS = 60

# Couleurs
COLOR_BG = (15, 15, 25)
COLOR_WALL = (0, 150, 200)
COLOR_PLAYER = (255, 100, 50)
COLOR_TEXT = (220, 230, 240)
COLOR_GRID = (30, 35, 50)
COLOR_START = (60, 100, 120)  # Case de départ plus claire
COLOR_ARTIFACT = (255, 230, 0) # Jaune
COLOR_COMPASS = (200, 200, 255, 100) # Semi-transparent

# États du jeu
STATE_MENU = 0
STATE_PLAYING = 1
STATE_SUCCESS = 2

# ==========================================
# MOTEUR MATHÉMATIQUE (LABYRINTHE INFINI)
# ==========================================

def deterministic_hash(*args):
    string_to_hash = ",".join(map(str, args)).encode('utf-8')
    return int(hashlib.md5(string_to_hash).hexdigest(), 16)

def get_block_parent(bx, by):
    if bx == 0 and by == 0: return None
    candidates = []
    if bx > 0:   candidates.append((bx - 1, by, 'W'))
    elif bx < 0: candidates.append((bx + 1, by, 'E'))
    if by > 0:   candidates.append((bx, by - 1, 'N'))
    elif by < 0: candidates.append((bx, by + 1, 'S'))
    idx = deterministic_hash(bx, by, "parent") % len(candidates)
    return candidates[idx]

@lru_cache(maxsize=256)
def generate_block(bx, by):
    seed = deterministic_hash(bx, by, "seed")
    local_rng = random.Random(seed)
    walls = {(cx, cy): set() for cx in range(BLOCK_SIZE) for cy in range(BLOCK_SIZE)}
    
    # Génération interne (DFS)
    visited = set()
    stack = [(0, 0)]
    visited.add((0, 0))
    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dcx, dcy, move, opp in [(-1,0,'W','E'), (1,0,'E','W'), (0,-1,'N','S'), (0,1,'S','N')]:
            ncx, ncy = cx + dcx, cy + dcy
            if 0 <= ncx < BLOCK_SIZE and 0 <= ncy < BLOCK_SIZE and (ncx, ncy) not in visited:
                neighbors.append((ncx, ncy, move, opp))
        if neighbors:
            ncx, ncy, move, opp = local_rng.choice(neighbors)
            walls[(cx, cy)].add(move)
            walls[(ncx, ncy)].add(opp)
            visited.add((ncx, ncy))
            stack.append((ncx, ncy))
        else: stack.pop()
            
    # Connexion au parent
    parent_info = get_block_parent(bx, by)
    if parent_info:
        _, _, direction = parent_info
        door_idx = deterministic_hash(bx, by, "door") % BLOCK_SIZE
        if direction == 'N': walls[(door_idx, 0)].add('N')
        elif direction == 'S': walls[(door_idx, BLOCK_SIZE-1)].add('S')
        elif direction == 'W': walls[(0, door_idx)].add('W')
        elif direction == 'E': walls[(BLOCK_SIZE-1, door_idx)].add('E')
    return walls

def cell_has_path(x, y, direction):
    bx, cx = divmod(x, BLOCK_SIZE)
    by, cy = divmod(y, BLOCK_SIZE)
    block_walls = generate_block(bx, by)
    if direction in block_walls[(cx, cy)]: return True
    
    # Symétrie voisin
    dx, dy, opp = 0, 0, ''
    if direction == 'N': dy, opp = -1, 'S'
    elif direction == 'S': dy, opp = 1, 'N'
    elif direction == 'W': dx, opp = -1, 'E'
    elif direction == 'E': dx, opp = 1, 'W'
    nbx, ncx = divmod(x + dx, BLOCK_SIZE)
    nby, ncy = divmod(y + dy, BLOCK_SIZE)
    neighbor_walls = generate_block(nbx, nby)
    return opp in neighbor_walls[(ncx, ncy)]

# ==========================================
# CLASSES DE JEU
# ==========================================

class GameSession:
    def __init__(self):
        self.level = 1
        self.reset_level()

    def reset_level(self):
        self.player_x = 0
        self.player_y = 0
        self.anim_x = 0.0
        self.anim_y = 0.0
        self.has_artifact = False
        
        # Placement de l'artefact : angle 100% aléatoire, distance proportionnelle au niveau
        # On utilise random.uniform directement sans graine (seed)
        angle = random.uniform(0, 2 * math.pi)
        distance = 15 + (self.level * 10) # La distance continue d'augmenter avec le niveau
        self.art_x = int(math.cos(angle) * distance)
        self.art_y = int(math.sin(angle) * distance)
        
        # Sécurité : s'assurer que l'artefact n'apparaît pas exactement sur la base (0,0)
        if self.art_x == 0 and self.art_y == 0: 
            self.art_x = 5

    def move(self, dx, dy, direction):
        if self.anim_x == self.player_x and self.anim_y == self.player_y:
            if cell_has_path(self.player_x, self.player_y, direction):
                self.player_x += dx
                self.player_y += dy
                # Check ramassage
                if self.player_x == self.art_x and self.player_y == self.art_y and not self.has_artifact:
                    self.has_artifact = True

    def update_animation(self):
        speed = 0.2
        if self.anim_x < self.player_x: self.anim_x = min(self.player_x, self.anim_x + speed)
        elif self.anim_x > self.player_x: self.anim_x = max(self.player_x, self.anim_x - speed)
        if self.anim_y < self.player_y: self.anim_y = min(self.player_y, self.anim_y + speed)
        elif self.anim_y > self.player_y: self.anim_y = max(self.player_y, self.anim_y - speed)

# ==========================================
# INITIALISATION ET BOUCLE PYGAME
# ==========================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Maze Artifact")
    clock = pygame.time.Clock()
    
    font_large = pygame.font.SysFont("Verdana", 80, bold=True)
    font_med = pygame.font.SysFont("Verdana", 24)
    font_small = pygame.font.SysFont("Consolas", 18)
    
    game = GameSession()
    state = STATE_MENU
    
    while True:
        delta_time = clock.tick(FPS) / 1000.0
        ticks = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if state == STATE_MENU and event.key == pygame.K_SPACE:
                    state = STATE_PLAYING
                elif state == STATE_SUCCESS and event.key == pygame.K_SPACE:
                    game.level += 1
                    game.reset_level()
                    state = STATE_PLAYING

        if state == STATE_PLAYING:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_z]: game.move(0, -1, 'N')
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]: game.move(0, 1, 'S')
            elif keys[pygame.K_LEFT] or keys[pygame.K_q]: game.move(-1, 0, 'W')
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: game.move(1, 0, 'E')
            
            game.update_animation()
            
            # Condition de victoire : Retour base avec artefact
            if game.has_artifact and game.player_x == 0 and game.player_y == 0 and game.anim_x == 0 and game.anim_y == 0:
                state = STATE_SUCCESS

        # --- RENDU ---
        screen.fill(COLOR_BG)

        if state == STATE_MENU:
            # Titre
            title_surf = font_large.render("THE MAZE", True, COLOR_WALL)
            screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 100))
            
            # Instructions
            instr = [
                "Welcome into the Maze. Your objective is to navigate its twists",
                "and turns to find the Artifact, and bring it back to base,",
                "where you started. By repeatedly exploring the Maze, you will",
                "begin to know it, and to find your way around it better."
            ]
            for i, line in enumerate(instr):
                surf = font_med.render(line, True, COLOR_TEXT)
                screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, 300 + i*40))
            
            # Texte clignotant
            alpha = int(127 + 128 * math.sin(ticks * 0.003))
            flash_surf = font_med.render("Press [space] to continue", True, (alpha, alpha, alpha))
            screen.blit(flash_surf, (SCREEN_WIDTH//2 - flash_surf.get_width()//2, 550))

        elif state == STATE_PLAYING:
            # Calcul caméra
            off_x = SCREEN_WIDTH//2 - game.anim_x * CELL_SIZE - CELL_SIZE//2
            off_y = SCREEN_HEIGHT//2 - game.anim_y * CELL_SIZE - CELL_SIZE//2
            
            # Grille et contenu
            start_x = int((-off_x) // CELL_SIZE) - 1
            end_x = int((SCREEN_WIDTH - off_x) // CELL_SIZE) + 1
            start_y = int((-off_y) // CELL_SIZE) - 1
            end_y = int((SCREEN_HEIGHT - off_y) // CELL_SIZE) + 1

            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    sx, sy = x * CELL_SIZE + off_x, y * CELL_SIZE + off_y
                    
                    # Case départ
                    if x == 0 and y == 0:
                        pygame.draw.rect(screen, COLOR_START, (sx, sy, CELL_SIZE, CELL_SIZE))
                    
                    # Artefact
                    if x == game.art_x and y == game.art_y and not game.has_artifact:
                        pygame.draw.circle(screen, COLOR_ARTIFACT, (int(sx + CELL_SIZE//2), int(sy + CELL_SIZE//2)), CELL_SIZE//4)
                    
                    # Murs
                    if not cell_has_path(x, y, 'N'):
                        pygame.draw.line(screen, COLOR_WALL, (sx, sy), (sx + CELL_SIZE, sy), 2)
                    if not cell_has_path(x, y, 'W'):
                        pygame.draw.line(screen, COLOR_WALL, (sx, sy), (sx, sy + CELL_SIZE), 2)

            # Joueur
            px, py = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
            pygame.draw.circle(screen, COLOR_PLAYER, (px, py), CELL_SIZE//3)
            
            # Boussole
            target_x = 0 if game.has_artifact else game.art_x
            target_y = 0 if game.has_artifact else game.art_y
            dx = target_x - game.anim_x
            dy = target_y - game.anim_y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0.1:
                angle = math.atan2(dy, dx)
                # Dessin d'un triangle indicateur autour du joueur
                point_dist = CELL_SIZE * 0.8
                ptr_x = px + math.cos(angle) * point_dist
                ptr_y = py + math.sin(angle) * point_dist
                pygame.draw.circle(screen, (255, 255, 255, 120), (int(ptr_x), int(ptr_y)), 5)

            # HUD
            hud1 = font_small.render(f"Level: {game.level}", True, COLOR_TEXT)
            hud2 = font_small.render("Objective: " + ("Return to Base" if game.has_artifact else "Find the Artifact"), True, COLOR_ARTIFACT if not game.has_artifact else COLOR_WALL)
            screen.blit(hud1, (20, 20))
            screen.blit(hud2, (20, 45))

        elif state == STATE_SUCCESS:
            msg = "Congratulations, you have brought the Artifact back to base!"
            surf = font_med.render(msg, True, COLOR_ARTIFACT)
            screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, 300))
            
            alpha = int(127 + 128 * math.sin(ticks * 0.003))
            cont = font_med.render("Press space for the next level", True, (alpha, alpha, alpha))
            screen.blit(cont, (SCREEN_WIDTH//2 - cont.get_width()//2, 400))

        pygame.display.flip()

if __name__ == "__main__":
    main()
