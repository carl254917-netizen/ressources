#Tetris

import sys
import subprocess
import random

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
install_and_import("requests")
install_and_import("os")
install_and_import("pygame")
install_and_import("Pillow", "PIL")
import pygame
import requests
import os
from io import BytesIO
from PIL import Image, ImageTk

# Initialisation
pygame.init()
pygame.mixer.init()

# Télécharger le son depuis une URL
def load_sound_from_url(url):
    response = requests.get(url)
    sound_data = BytesIO(response.content)
    return pygame.mixer.Sound(file=sound_data)

def load_music_from_url(url):
    response = requests.get(url)
    music_data = BytesIO(response.content)
    music_data.seek(0)  # ← rembobine le flux
    return music_data

# Téléchargement des ressources
logo_url = "https://upload.wikimedia.org/wikipedia/commons/7/7c/Tetris_GB_logo.png"
logo_path = "logo.png"

click_sound_url = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/pc-mouse-click.wav"
click_sound = load_sound_from_url(click_sound_url)

# Chargement de l'image en ligne
response = requests.get("https://raw.githubusercontent.com/carl254917-netizen/ressources/refs/heads/main/Tetris_logo.png")
image_data = BytesIO(response.content)
        
click_sound = pygame.mixer.Sound(click_sound)

# Paramètres de la grille
GRID_WIDTH, GRID_HEIGHT = 10, 22
CELL_SIZE = 30
GRID_X, GRID_Y = 200, 60
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 720
RED_LINE_Y = GRID_Y + (2 * CELL_SIZE)


# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
COLORS = [(0,255,255), (255,255,0), (255,0,255), (255,165,0), (0,0,255), (255,0,0), (0,255,0)]

# Tétriminos
TETROMINOS = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 0, 0], [1, 1, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]]   # S
]

volume=0.1

# Fonctions utilitaires
def rotate(shape, direction):
    if direction == "left":
        return [list(row) for row in zip(*shape[::-1])]
    else:
        return [list(row) for row in zip(*shape)][::-1]

def draw_grid_content(surface, grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x]:
                color = COLORS[grid[y][x] - 1]
                rect = pygame.Rect(GRID_X + x * CELL_SIZE, GRID_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, color, rect)

def draw_grid(surface):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(GRID_X + x * CELL_SIZE, GRID_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, WHITE, rect, 1)
    pygame.draw.line(surface, RED, (GRID_X, RED_LINE_Y), (GRID_X + GRID_WIDTH * CELL_SIZE, RED_LINE_Y), 2)

def draw_piece(surface, shape, x, y, color):
    for i, row in enumerate(shape):
        for j, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(GRID_X + (x + j) * CELL_SIZE, GRID_Y + (y + i) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, color, rect)

def check_collision(grid, shape, x, y):
    for i, row in enumerate(shape):
        for j, cell in enumerate(row):
            if cell:
                if x + j < 0 or x + j >= GRID_WIDTH or y + i >= GRID_HEIGHT or grid[y + i][x + j]:
                    return True
    return False

def merge_piece(grid, shape, x, y, color_index):
    for i, row in enumerate(shape):
        for j, cell in enumerate(row):
            if cell:
                grid[y + i][x + j] = color_index + 1

def clear_lines(grid):
    cleared = 0
    new_grid = [row for row in grid if any(cell == 0 for cell in row)]
    cleared = GRID_HEIGHT - len(new_grid)
    for _ in range(cleared):
        new_grid.insert(0, [0] * GRID_WIDTH)
    return new_grid, cleared

# Écran d'accueil
def show_menu():
    menu_screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Tetris Menu")
    logo = pygame.image.load(image_data)
    font = pygame.font.SysFont(None, 40)
    button = pygame.Rect(90, 220, 220, 50)
    running = True
    while running:
        menu_screen.fill((200, 200, 200))
        menu_screen.blit(pygame.transform.scale(logo, (200, 100)), (100, 50))
        pygame.draw.rect(menu_screen, (100, 100, 250), button)
        text = font.render("Nouvelle Partie", True, WHITE)
        text_rect = text.get_rect(center=button.center)
        menu_screen.blit(text, text_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and button.collidepoint(event.pos):
                click_sound.play()
                running = False
        pygame.display.flip()

# Boucle principale du jeu
def run_game():
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    GRID_PIXEL_WIDTH = GRID_WIDTH * CELL_SIZE
    GRID_PIXEL_HEIGHT = GRID_HEIGHT * CELL_SIZE
    global GRID_X
    GRID_X = (SCREEN_WIDTH - GRID_PIXEL_WIDTH) // 2
    global GRID_Y
    GRID_Y = (SCREEN_HEIGHT - GRID_PIXEL_HEIGHT) // 2
    global RED_LINE_Y
    RED_LINE_Y = GRID_Y + (2 * CELL_SIZE)
    pygame.mouse.set_visible(False)
    pygame.display.set_caption("Tetris")
    music_url = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Tetris_Soundtrack.mp3"
    music_data = load_music_from_url(music_url)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.load(music_data)
    pygame.mixer.music.play(-1)  # Boucle infinie

    clock = pygame.time.Clock()
    grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    score = 0
    font = pygame.font.SysFont(None, 30)

    current_piece_index = random.randint(0, 6)
    next_piece_index = random.randint(0, 6)
    current_piece = TETROMINOS[current_piece_index]
    next_piece = TETROMINOS[next_piece_index]
    x, y = GRID_WIDTH // 2 - len(current_piece[0]) // 2, 0
    fall_time = 0
    fall_speed = 500
    game_time = 0
    speed_increment_interval = 10000  # toutes les 10 secondes

    running = True
    while running:
        screen.fill(BLACK)
        draw_grid(screen)
        draw_grid_content(screen, grid)
        draw_piece(screen, current_piece, x, y, COLORS[current_piece_index])
        screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
        draw_piece(screen, next_piece, GRID_WIDTH + 2, 2, COLORS[next_piece_index])

        fall_time += clock.get_rawtime()
        game_time += clock.get_rawtime()
        if game_time > speed_increment_interval:
            fall_speed = max(150, fall_speed * 0.95)  # vitesse minimale = 100 ms
            game_time = 0  # réinitialise le compteur

        clock.tick()

        if fall_time > fall_speed:
            if not check_collision(grid, current_piece, x, y + 1):
                y += 1
            else:
                merge_piece(grid, current_piece, x, y, current_piece_index)
                grid, cleared = clear_lines(grid)
                if cleared:
                    score += cleared ** 2
                current_piece_index = next_piece_index
                next_piece_index = random.randint(0, 6)
                current_piece = TETROMINOS[current_piece_index]
                next_piece = TETROMINOS[next_piece_index]
                x, y = GRID_WIDTH // 2 - len(current_piece[0]) // 2, 0
                if check_collision(grid, current_piece, x, y):
                    running = False
            fall_time = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_LEFT and not check_collision(grid, current_piece, x - 1, y):
                    x -= 1
                    fall_time += -100
                elif event.key == pygame.K_RIGHT and not check_collision(grid, current_piece, x + 1, y):
                    x += 1
                    fall_time += -100
                elif event.key == pygame.K_DOWN and not check_collision(grid, current_piece, x, y + 1):
                    y += 1
                    fall_time += -100
                elif event.key == pygame.K_q and not check_collision(grid, current_piece, x - 1, y):
                    x -= 1
                    fall_time += -100
                elif event.key == pygame.K_d and not check_collision(grid, current_piece, x + 1, y):
                    x += 1
                    fall_time += -100
                elif event.key == pygame.K_s and not check_collision(grid, current_piece, x, y + 1):
                    y += 1
                elif event.key == pygame.K_KP_6:
                    rotated = rotate(current_piece, "right")
                    if not check_collision(grid, rotated, x, y):
                        current_piece = rotated
                        fall_time += -100
                elif event.key == pygame.K_KP_4:
                    rotated = rotate(current_piece, "left")
                    if not check_collision(grid, rotated, x, y):
                        current_piece = rotated
                        fall_time += -100
            elif event.type == pygame.MOUSEWHEEL:
                rotated = rotate(current_piece, "right" if event.y > 0 else "left")
                if not check_collision(grid, rotated, x, y):
                    current_piece = rotated

        pygame.display.flip()

    screen.fill(BLACK)
    screen.blit(font.render(f"Game Over! Score: {score}", True, RED), (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.display.quit()
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

# Lancement
show_menu()
run_game()









