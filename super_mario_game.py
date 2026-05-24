# -*- coding: utf-8 -*-
import sys
import subprocess

# --- VÉRIFICATION ET INSTALLATION DES DÉPENDANCES ---
try:
    import pygame
except ImportError:
    print("Pygame n'est pas installé. Tentative d'installation automatique...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
        import pygame
    except Exception as e:
        print(f"Erreur lors de l'installation de Pygame : {e}")
        print("Veuillez installer pygame manuellement avec : pip install pygame")
        sys.exit(1)

from pygame.locals import *

# --- CONFIGURATION ET CONSTANTES ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Couleurs (Thématique rétro/soignée)
COLOR_SKY = (92, 148, 252)
COLOR_DARK_SKY = (20, 20, 40)
COLOR_CASTLE = (50, 50, 50)
COLOR_ICE_BG = (180, 220, 255)
COLOR_SKY_BG = (255, 200, 180)

COLOR_GROUND = (200, 76, 12)
COLOR_ICE = (150, 200, 255)
COLOR_CLOUD = (230, 240, 255)
COLOR_BRICK = (200, 76, 12)
COLOR_GOLD = (252, 216, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 168, 0)
COLOR_RED = (216, 40, 0)
COLOR_BLUE = (0, 0, 184)
COLOR_TEXT = (255, 255, 255)
COLOR_UI_BG = (40, 40, 40)
COLOR_UI_HOVER = (100, 100, 100)

TILE_SIZE = 40

# --- EN-TÊTES ET GRAPHISMES PROCÉDURAUX (PROPRES) ---
def creer_surface_bloc(couleur, type_bloc):
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    surf.fill(couleur)
    pygame.draw.rect(surf, (255, 255, 255, 100), (0, 0, TILE_SIZE, TILE_SIZE), 2)
    pygame.draw.rect(surf, (0, 0, 0, 80), (2, 2, TILE_SIZE-2, TILE_SIZE-2), 2)
    
    if type_bloc == "brick":
        pygame.draw.line(surf, (0, 0, 0, 100), (0, TILE_SIZE//2), (TILE_SIZE, TILE_SIZE//2), 2)
        pygame.draw.line(surf, (0, 0, 0, 100), (TILE_SIZE//2, 0), (TILE_SIZE//2, TILE_SIZE//2), 2)
        pygame.draw.line(surf, (0, 0, 0, 100), (TILE_SIZE//4, TILE_SIZE//2), (TILE_SIZE//4, TILE_SIZE), 2)
        pygame.draw.line(surf, (0, 0, 0, 100), (3*TILE_SIZE//4, TILE_SIZE//2), (3*TILE_SIZE//4, TILE_SIZE), 2)
    elif type_bloc == "question":
        pygame.draw.circle(surf, COLOR_GOLD, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3)
        pygame.draw.rect(surf, (255, 255, 255, 150), (TILE_SIZE//2 - 3, TILE_SIZE//4, 6, 12))
        pygame.draw.circle(surf, (255, 255, 255, 150), (TILE_SIZE//2, 3*TILE_SIZE//4 - 4), 3)
    return surf

# --- CLASSES DU JEU ---

class Joueur(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.est_grand = False
        self.creer_image()
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Vecteurs de mouvement
        self.vx = 0
        self.vy = 0
        self.vitesse = 5
        self.puissance_saut_base = -13
        self.puissance_saut = self.puissance_saut_base
        self.en_sol = False
        self.invincible = 0
        self.timer_champignon = 0
        self.score_niveau = 0
        self.pieces_recoltees = 0
        self.est_mort = False

    def creer_image(self):
        w = 60 if self.est_grand else 30
        h = 76 if self.est_grand else 38
        s = 2 if self.est_grand else 1 # Scale multiplier
        
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, COLOR_RED, (4*s, 0, 22*s, 12*s)) # Casquette / Tête
        pygame.draw.rect(self.image, (240, 180, 140), (6*s, 10*s, 18*s, 12*s)) # Visage
        pygame.draw.rect(self.image, COLOR_BLUE, (4*s, 22*s, 22*s, 16*s)) # Salopette
        pygame.draw.rect(self.image, COLOR_GOLD, (8*s, 26*s, 4*s, 4*s)) # Bouton L
        pygame.draw.rect(self.image, COLOR_GOLD, (18*s, 26*s, 4*s, 4*s)) # Bouton R

    def grandir(self):
        if not self.est_grand:
            self.est_grand = True
            old_bottom = self.rect.bottom
            old_x = self.rect.x  # On sauvegarde l'ancienne coordonnée X
            
            self.creer_image()
            self.rect = self.image.get_rect()
            
            self.rect.x = old_x  # On restaure la coordonnée X
            self.rect.bottom = old_bottom
            self.puissance_saut = -16
        # 60 FPS * 10 secondes = 600 frames d'effet
        self.timer_champignon = 600

    def retrecir(self, par_degat=True):
        self.est_grand = False
        old_bottom = self.rect.bottom
        old_x = self.rect.x  # On sauvegarde l'ancienne coordonnée X
        
        self.creer_image()
        self.rect = self.image.get_rect()
        
        self.rect.x = old_x  # On restaure la coordonnée X
        self.rect.bottom = old_bottom
        self.puissance_saut = self.puissance_saut_base
        self.timer_champignon = 0
        
        # On donne des frames d'invincibilité UNIQUEMENT si c'est un dégât
        if par_degat:
            self.invincible = 120
    
    def update(self, plateformes, ennemis, bonus, declencheurs_fin, projectiles):
        if self.est_mort:
            self.vy += 0.5
            self.rect.y += self.vy
            return

        # Gravité
        self.vy += 0.6
        if self.vy > 12:
            self.vy = 12

        # Déplacement horizontal
        self.rect.x += self.vx
        self.gerer_collisions_horizontales(plateformes)

        # Déplacement vertical
        self.rect.y += self.vy
        self.gerer_collisions_verticales(plateformes)

        # Gérer les autres interactions
        self.verifier_collisions_objets(ennemis, bonus, declencheurs_fin, projectiles)

        # Clignotement / Décompte invincibilité
        if self.invincible > 0:
            self.invincible -= 1

        # NOUVELLE LOGIQUE DU CHAMPIGNON
        if self.timer_champignon > 0:
            self.timer_champignon -= 1
            if self.timer_champignon == 0 and self.est_grand:
                # Le temps est écoulé, on rétrécit sans invincibilité (par_degat=False)
                self.retrecir(par_degat=False)

        # Chute mortelle
        if self.rect.y > SCREEN_HEIGHT + 100:
            self.mourir()

    def sauter(self):
        if self.en_sol:
            self.vy = self.puissance_saut
            self.en_sol = False

    def gerer_collisions_horizontales(self, plateformes):
        liste_collisions = pygame.sprite.spritecollide(self, plateformes, False)
        for bloc in liste_collisions:
            if self.vx > 0:
                self.rect.right = bloc.rect.left
            elif self.vx < 0:
                self.rect.left = bloc.rect.right

    def gerer_collisions_verticales(self, plateformes):
        liste_collisions = pygame.sprite.spritecollide(self, plateformes, False)
        self.en_sol = False
        for bloc in liste_collisions:
            if self.vy > 0:
                self.rect.bottom = bloc.rect.top
                self.vy = 0
                self.en_sol = True
            elif self.vy < 0:
                self.rect.top = bloc.rect.bottom
                self.vy = 0
                if hasattr(bloc, 'activer') and not bloc.active:
                    bloc.activer(self)

    def subit_degat(self):
        if self.invincible <= 0:
            if self.est_grand:
                self.retrecir()
            else:
                self.mourir()

    def verifier_collisions_objets(self, ennemis, bonus, declencheurs_fin, projectiles):
        # Ennemis (Goombas et Tireurs)
        collisions_ennemis = pygame.sprite.spritecollide(self, ennemis, False)
        for ennemi in collisions_ennemis:
            # Invincible par une étoile
            if self.invincible > 120:
                ennemi.ecraser()
                self.score_niveau += 100
            # Tomber dessus
            elif self.vy > 0 and self.rect.bottom <= ennemi.rect.top + 25:
                ennemi.ecraser()
                self.vy = -10
                self.score_niveau += 100
            else:
                self.subit_degat()

        # Projectiles
        collisions_proj = pygame.sprite.spritecollide(self, projectiles, False)
        for p in collisions_proj:
            p.kill()
            if self.invincible <= 120: # L'étoile protège des tirs
                self.subit_degat()

        # Bonus
        collisions_bonus = pygame.sprite.spritecollide(self, bonus, False)
        for obj in collisions_bonus:
            if obj.type == "piece":
                self.pieces_recoltees += 1
                self.score_niveau += 50
                obj.kill()
            elif obj.type == "champignon":
                self.score_niveau += 500
                self.grandir()
                obj.kill()
            elif obj.type == "etoile":
                self.score_niveau += 1000
                self.invincible = 600 # 10s d'invincibilité pure (60fps * 10)
                obj.kill()

        # Fin de niveau
        if pygame.sprite.spritecollideany(self, declencheurs_fin):
            self.vx = 0
            pygame.event.post(pygame.event.Event(USEREVENT + 1))

    def mourir(self):
        if not self.est_mort:
            self.est_mort = True
            self.vy = -10
            pygame.time.set_timer(USEREVENT + 2, 1500)

class Bloc(pygame.sprite.Sprite):
    def __init__(self, x, y, type_bloc="ground", style="day"):
        super().__init__()
        self.type_bloc = type_bloc
        self.active = False
        
        if type_bloc == "ground":
            couleur = COLOR_GROUND
            if style == "ice": couleur = COLOR_ICE
            elif style == "sky": couleur = COLOR_CLOUD
            self.image = creer_surface_bloc(couleur, "ground")
        elif type_bloc == "brick":
            self.image = creer_surface_bloc(COLOR_BRICK, "brick")
        elif type_bloc == "question":
            self.image = creer_surface_bloc(COLOR_GOLD, "question")
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def activer(self, joueur):
        if self.type_bloc == "question":
            self.active = True
            self.image = creer_surface_bloc((120, 120, 120), "solid")
            
            # Déterminisme simple pour varier les bonus
            if self.rect.x % 7 == 0:
                bonus_groupe.add(Bonus(self.rect.x + 8, self.rect.y - TILE_SIZE, "etoile"))
            elif self.rect.x % 3 == 0:
                bonus_groupe.add(Bonus(self.rect.x + 8, self.rect.y - TILE_SIZE, "champignon"))
            else:
                joueur.pieces_recoltees += 1
                joueur.score_niveau += 50

class Ennemi(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (165, 42, 42), (16, 16), 16)
        pygame.draw.rect(self.image, (240, 220, 200), (8, 20, 16, 12))
        pygame.draw.circle(self.image, COLOR_BLACK, (10, 12), 2)
        pygame.draw.circle(self.image, COLOR_BLACK, (22, 12), 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = -2
        self.vy = 0
        self.est_ecrase = False
        self.compteur_mort = 0

    def update(self, plateformes):
        if self.est_ecrase:
            self.compteur_mort += 1
            if self.compteur_mort > 30:
                self.kill()
            return

        self.vy += 0.5
        self.rect.y += self.vy
        
        collisions = pygame.sprite.spritecollide(self, plateformes, False)
        for bloc in collisions:
            if self.vy > 0:
                self.rect.bottom = bloc.rect.top
                self.vy = 0

        self.rect.x += self.vx
        collisions = pygame.sprite.spritecollide(self, plateformes, False)
        for bloc in collisions:
            if self.vx > 0:
                self.rect.right = bloc.rect.left
                self.vx = -self.vx
            elif self.vx < 0:
                self.rect.left = bloc.rect.right
                self.vx = -self.vx

    def ecraser(self):
        self.est_ecrase = True
        self.vx = 0
        self.image = pygame.Surface((32, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (165, 42, 42), (0, 0, 32, 10))

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COLOR_GOLD, (6, 6), 6)
        pygame.draw.circle(self.image, COLOR_RED, (6, 6), 3)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.vx = 5 * direction

    def update(self, plateformes):
        self.rect.x += self.vx
        if pygame.sprite.spritecollideany(self, plateformes):
            self.kill()

class EnnemiTireur(Ennemi):
    def __init__(self, x, y):
        super().__init__(x, y)
        # Personnalisation graphique (Plante/Tortue Verte)
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(self.image, COLOR_GREEN, (4, 4, 24, 28), border_radius=5)
        pygame.draw.rect(self.image, (200, 255, 200), (8, 8, 16, 12))
        pygame.draw.circle(self.image, COLOR_RED, (10, 14), 3)
        pygame.draw.circle(self.image, COLOR_RED, (22, 14), 3)
        
        self.timer_tir = 0
        self.direction = -1

    def update(self, plateformes):
        super().update(plateformes)
        if not self.est_ecrase:
            self.direction = 1 if self.vx > 0 else -1
            self.timer_tir += 1
            if self.timer_tir >= 100: # Tire toutes les ~1.5 secondes
                self.timer_tir = 0
                projectiles_groupe.add(Projectile(self.rect.centerx, self.rect.centery, self.direction))

class Bonus(pygame.sprite.Sprite):
    def __init__(self, x, y, type_bonus="piece"):
        super().__init__()
        self.type = type_bonus
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        
        if self.type == "piece":
            pygame.draw.circle(self.image, COLOR_GOLD, (12, 12), 10)
            pygame.draw.circle(self.image, (255, 255, 255), (12, 12), 6, 2)
        elif self.type == "champignon":
            pygame.draw.circle(self.image, COLOR_RED, (12, 12), 12)
            pygame.draw.rect(self.image, (255, 220, 200), (6, 12, 12, 12))
            pygame.draw.circle(self.image, COLOR_WHITE, (7, 6), 3)
            pygame.draw.circle(self.image, COLOR_WHITE, (17, 6), 3)
        elif self.type == "etoile":
            points = [(12,0), (15,8), (24,9), (17,15), (19,24), (12,19), (5,24), (7,15), (0,9), (9,8)]
            pygame.draw.polygon(self.image, COLOR_GOLD, points)
            pygame.draw.polygon(self.image, COLOR_WHITE, points, 1)
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class FinDeNiveau(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (200, 200, 200), (8, 0, 4, SCREEN_HEIGHT))
        pygame.draw.polygon(self.image, COLOR_GREEN, [(12, 40), (12, 80), (40, 60)])
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = 0

# --- DONNÉES DES CARTES / NIVEAUX (DOUBLÉES EN LONGUEUR) ---
NIVEAUX_MAPS = [
    {
        "style": "day",
        "structure": [
            "                                                                                                                                                                                                        ",
            "                                                                                                                                                                                                        ",
            "                                                                                                                                                                                                        ",
            "                                                                                                         C                                                                                              ",
            "                                                 C  C  C                                                                             C  C                                                               ",
            "                                                BBBBBBBB                                                                            BBBBBB                                                              ",
            "                      Q  B  Q  B                                                                      Q  B  Q                                                                                           ",
            "                                          BBB              BBBB                     BBBBBB                                                                  BBBB             C   C                      ",
            "             C  C     BBBBBBBBBB         BBBBB            BBBBBB             C   C                    BB  BB           Q    Q                C   C         BBBBBB                                       ",
            "            BBBBBB                      BBBBBBB          BBBBBBBB           Q B Q B                                                         BBBBBBB       BBBBBBBB          Q B Q B                     ",
            "     P                     E           BBBBBBBBB    E   BBBBBBBBBB            B       E      B         B           E   E      B            BBBBBBBBB     BBBBBBBBBB                                  F  ",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        ]
    },
    {
        "style": "night",
        "structure": [
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "                                                                                                                                                                                                            ",
            "                                      C                                                                                                                                                                     ",
            "        C  C  C                                          C  C  C                            C  C                                          C  C  C                                                           ",
            "       BBBBBBBB                       Q                 BBBBBBBB                           BBBBBB                         Q              BBBBBBBB                                                           ",
            "                                                  BB                                                                                                      BB                                                ",
            "                 BBBBBB            B        EB                               C                            BBBBBB               B                     C                                                      ",
            "                BBBBBBBB          BBGGGGGGGGBBB                                                          BBBBBBBB             BBGGGGGGGGBBB                                                                 ",
            "                                 BBGGGGGGGGGGBBB                       BBBB     BB                                           BBGGGGGGGGGGBBB                       BBBB                                     ",
            "    P            E              BBGGGGGGGGGGGGBBB  E       E          BBBBBB   BBBB         T  B       B                E   BBGGGGGGGGGGGGBBB     E    T          BBBBBB                     F              ",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG           ",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG           ",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG           "
        ]
    },
    {
        "style": "castle",
        "structure": [
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
            "                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                            ",
            "              C   C   C                      C   C   C                                                    C   C                               C   C   C                                                     ",
            "             Q B Q B Q B                    Q B Q B Q B                                                  Q B Q B                             Q B Q B Q B                                                    ",
            "                                                                                C                                                                                                C                          ",
            "              B   B   B                     B   B                                                          B   B                              B   B                                                         ",
            "       BBB                  BBBBB                      BBBBB                   BBB                  BBB                 BBBBB                        BBBBB                    BBB                           ",
            "      BBBBB                BBBBBBB                    BBBBBBB                 BBBBB                BB                  BBBBBBB                      BBBBBBB                  BBBBB                          ",
            "     BBBQBBB              BBBBBBBBB                  BBBBBBBBB               BBBBBBB              BBBQBQB             BBBBBBBBB     B              BBBBBBBBB                BBBBBBB                         ",
            "  P            T      E  BBBBBBBBBBB    BT  E       BBBBBBBBBBB   BT  E     BBBBBBBBB                  T     E       BBBBBBBBBBB    BT            BBBBBBBBBBB   BT  E      BBBBBBBBB            F           ",
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB          ",
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB          ",
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBB   BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB          "
        ]
    },
    {
        "style": "ice",
        "structure": [
            "                                                                                                                                                                                                            ",
            "                                                                                                                                                       C                                                    ",
            "                                                                                                                                                                                                            ",
            "                                             C  C  C                                                                                                                                                        ",
            "                                            BBBBBBBB                         Q                                C  C                                  Q  B  Q                                                 ",
            "                 Q  B  Q                                                                                     BBBBBB                                                                                         ",
            "                                                                    B        B        B                                    E                                                                                ",
            "                                      BBB                  BBBBB                                    BBB                   BBBBB             BBBBBB             BBBB                  C   C                  ",
            "          C  C                       BBBBB                BBBBBBB                                  BBBBB                 BBBBBBB           BBBBBBBB           BBBBBB                                        ",
            "         BBBBBB                     BBBBBBB              BBBBBBBBB            C  C                BBBBBBB               BBBBBBBBB         BBBBBBBBBB         BBBBBBBB               Q B Q B                 ",
            "  P                  T            EBBBBBBBBB     BE     BBBBBBBBBBB          BBBBBB      E       BBBBBBBBB       BT                 EB   BBBBBBBBBBBB   E   BBBBBBBBBB                                   F  ",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        ]
    },
    {
        "style": "sky",
        "structure": [
            "                                                                                                             C  C  C                                                                                      ",
            "                                                                                            C  C                                                                        C                                 ",
            "           C  C           C  C  C                                          C  C           BE     B         B    ET   Q                    C  C                                                            ",
            "          BBBBBB         BBBBBBBB                                         BBBBBB           BBBBBB           BBBBBBBBB                    BBBBBB                                                           ",
            "                                               Q  B  Q                                                                         Q                                     Q  B  Q                              ",
            "                                                                                                                                                                                                          ",
            "      B            B                  BBBBB               BBBBB        B          B                BBBBB                BBBBB        B        BBBBBB                                                      ",
            "                                     BBBBBBB             BBBBBBB                                  BBBBBBB              BBBBBBB               BBBBBB                                BBBB                   ",
            "             Q      E   Q           BBBBBBBBB           BBBBBBBBB           Q      T   Q         BBBBBBBBB            BBBBBBBBB             BBBC C  BB         B   E  E B         BBBBBB                  ",
            "  P           GGGGGGGGGG           BBBBBBBBBBB    E    BBBBBBBBBBB           GGGGGGGGGG         BBBBBBBBBBB   T  E   BBBBBBBBBBB           BBB  E   BBB         GGGGGGGG         BBBBBBBB               F ",
            "GGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "GGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "GGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGG   GGGGGGGGGGGGGG   GGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        ]
    }
]

# --- BOUTONS ---
class Bouton:
    def __init__(self, x, y, largeur, hauteur, texte, action_id):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.action_id = action_id
        self.survole = False

    def dessiner(self, surface, font):
        couleur = COLOR_UI_HOVER if self.survole else COLOR_UI_BG
        pygame.draw.rect(surface, couleur, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_WHITE, self.rect, 2, border_radius=8)
        texte_surf = font.render(self.texte, True, COLOR_TEXT)
        texte_rect = texte_surf.get_rect(center=self.rect.center)
        surface.blit(texte_surf, texte_rect)

    def verifier_survol(self, pos_souris):
        self.survole = self.rect.collidepoint(pos_souris)
        return self.survole

# --- GESTIONNAIRE JEU ---
class GestionnaireJeu:
    def __init__(self):
        pygame.init()
        self.ecran = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros Réinvention PC")
        self.horloge = pygame.time.Clock()
        self.font_titre = pygame.font.SysFont("Impact", 48)
        self.font_menu = pygame.font.SysFont("Arial", 24)
        self.font_jeu = pygame.font.SysFont("Consolas", 20)
        
        # Progression en mémoire (n'est plus sauvegardée sur le disque dur)
        self.progression = {"niveau_max": 1, "pieces_totat": 0}
        self.etat = "MENU_PRINCIPAL"
        self.index_niveau_actuel = 0
        
        global bonus_groupe, projectiles_groupe
        bonus_groupe = pygame.sprite.Group()
        projectiles_groupe = pygame.sprite.Group()

        self.boutons_principaux = [
            Bouton(300, 250, 200, 50, "Jouer", "choix_niveau"),
            Bouton(300, 330, 200, 50, "Quitter", "quitter")
        ]
        self.creer_boutons_niveaux()

    def creer_boutons_niveaux(self):
        self.boutons_niveaux = []
        for i in range(len(NIVEAUX_MAPS)):
            unlocked = (i + 1) <= self.progression["niveau_max"]
            texte = f"Niveau {i+1}" if unlocked else f"Niveau {i+1} (Verrouillé)"
            # Layout adaptatif
            x = 100 if i < 3 else 450
            y = 200 + ((i % 3) * 70)
            btn = Bouton(x, y, 250, 50, texte, f"run_level_{i}" if unlocked else "locked")
            self.boutons_niveaux.append(btn)
            
        # Bouton Retour (désormais centré)
        self.boutons_niveaux.append(Bouton(275, 480, 250, 50, "Retour", "menu_principal"))

    def charger_niveau(self, index):
        self.index_niveau_actuel = index
        self.plateformes = pygame.sprite.Group()
        self.ennemis = pygame.sprite.Group()
        self.bonus = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.declencheurs_fin = pygame.sprite.Group()
        
        global bonus_groupe, projectiles_groupe
        bonus_groupe = self.bonus
        projectiles_groupe = self.projectiles
        
        map_info = NIVEAUX_MAPS[index]
        self.style_niveau = map_info["style"]
        structure = map_info["structure"]
        
        for ligne_idx, ligne in enumerate(structure):
            for col_idx, char in enumerate(ligne):
                x = col_idx * TILE_SIZE
                y = ligne_idx * TILE_SIZE
                
                if char == "G":
                    self.plateformes.add(Bloc(x, y, "ground", self.style_niveau))
                elif char == "B":
                    self.plateformes.add(Bloc(x, y, "brick"))
                elif char == "Q":
                    self.plateformes.add(Bloc(x, y, "question"))
                elif char == "P":
                    self.joueur = Joueur(x, y)
                elif char == "E":
                    self.ennemis.add(Ennemi(x, y))
                elif char == "T":
                    self.ennemis.add(EnnemiTireur(x, y))
                elif char == "C":
                    self.bonus.add(Bonus(x + 8, y + 8, "piece"))
                elif char == "F":
                    self.declencheurs_fin.add(FinDeNiveau(x, y))
                    
        self.camera_x = 0
        self.score_affiche = 0
        self.temps_restant = 400
        self.timer_secondes = pygame.time.get_ticks()

    def gerer_evenements(self):
        pos_souris = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
                
            elif event.type == USEREVENT + 1:
                self.etat = "ECRAN_VICTOIRE"
                prochain_niveau = self.index_niveau_actuel + 2
                if prochain_niveau > self.progression["niveau_max"] and prochain_niveau <= len(NIVEAUX_MAPS):
                    self.progression["niveau_max"] = prochain_niveau
                self.progression["pieces_totat"] += self.joueur.pieces_recoltees
                self.creer_boutons_niveaux()
                
            elif event.type == USEREVENT + 2:
                pygame.time.set_timer(USEREVENT + 2, 0)
                self.etat = "GAME_OVER"

            if self.etat == "MENU_PRINCIPAL":
                for btn in self.boutons_principaux:
                    btn.verifier_survol(pos_souris)
                    if event.type == MOUSEBUTTONDOWN and event.button == 1 and btn.survole:
                        if btn.action_id == "choix_niveau":
                            self.etat = "CHOIX_NIVEAU"
                        elif btn.action_id == "quitter":
                            return False
                            
            elif self.etat == "CHOIX_NIVEAU":
                for btn in self.boutons_niveaux:
                    btn.verifier_survol(pos_souris)
                    if event.type == MOUSEBUTTONDOWN and event.button == 1 and btn.survole:
                        if btn.action_id.startswith("run_level_"):
                            idx = int(btn.action_id.split("_")[-1])
                            self.charger_niveau(idx)
                            self.etat = "EN_JEU"
                        elif btn.action_id == "menu_principal":
                            self.etat = "MENU_PRINCIPAL"
                            
            elif self.etat in ["GAME_OVER", "ECRAN_VICTOIRE"]:
                if event.type == MOUSEBUTTONDOWN or event.type == KEYDOWN:
                    self.etat = "CHOIX_NIVEAU"

            elif self.etat == "EN_JEU":
                if event.type == KEYDOWN:
                    if event.key in [K_SPACE, K_UP, K_w]:
                        self.joueur.sauter()
                    if event.key == K_ESCAPE:
                        self.etat = "CHOIX_NIVEAU"

        if self.etat == "EN_JEU" and not self.joueur.est_mort:
            touches = pygame.key.get_pressed()
            # Simulation glissade basique sur niveau glace
            friction = 1.0 if self.style_niveau != "ice" else 0.95 

            if touches[K_LEFT] or touches[K_a]:
                self.joueur.vx = -self.joueur.vitesse
            elif touches[K_RIGHT] or touches[K_d]:
                self.joueur.vx = self.joueur.vitesse
            else:
                if self.style_niveau == "ice":
                    self.joueur.vx *= friction
                    if abs(self.joueur.vx) < 0.5: self.joueur.vx = 0
                else:
                    self.joueur.vx = 0

        return True

    def mettre_a_jour(self):
        if self.etat == "EN_JEU":
            self.joueur.update(self.plateformes, self.ennemis, self.bonus, self.declencheurs_fin, self.projectiles)
            self.ennemis.update(self.plateformes)
            self.projectiles.update(self.plateformes)
            
            maintenant = pygame.time.get_ticks()
            if maintenant - self.timer_secondes >= 1000:
                self.temps_restant -= 1
                self.timer_secondes = maintenant
                if self.temps_restant <= 0:
                    self.joueur.mourir()

            if self.joueur.rect.x - self.camera_x > SCREEN_WIDTH * 0.5:
                self.camera_x = self.joueur.rect.x - SCREEN_WIDTH * 0.5

    def dessiner(self):
        if self.etat == "EN_JEU":
            if self.style_niveau == "day": self.ecran.fill(COLOR_SKY)
            elif self.style_niveau == "night": self.ecran.fill(COLOR_DARK_SKY)
            elif self.style_niveau == "castle": self.ecran.fill(COLOR_CASTLE)
            elif self.style_niveau == "ice": self.ecran.fill(COLOR_ICE_BG)
            elif self.style_niveau == "sky": self.ecran.fill(COLOR_SKY_BG)
        else:
            self.ecran.fill((30, 40, 60))

        if self.etat == "MENU_PRINCIPAL":
            titre = self.font_titre.render("SUPER PYGAME BROS", True, COLOR_GOLD)
            self.ecran.blit(titre, (titre.get_width()//4, 100))
            for btn in self.boutons_principaux:
                btn.dessiner(self.ecran, self.font_menu)
                
        elif self.etat == "CHOIX_NIVEAU":
            titre = self.font_titre.render("SÉLECTION DU NIVEAU", True, COLOR_WHITE)
            self.ecran.blit(titre, (140, 80))
            for btn in self.boutons_niveaux:
                btn.dessiner(self.ecran, self.font_menu)
                
        elif self.etat == "EN_JEU":
            for plat in self.plateformes:
                self.ecran.blit(plat.image, (plat.rect.x - self.camera_x, plat.rect.y))
            for b in self.bonus:
                self.ecran.blit(b.image, (b.rect.x - self.camera_x, b.rect.y))
            for e in self.ennemis:
                self.ecran.blit(e.image, (e.rect.x - self.camera_x, e.rect.y))
            for p in self.projectiles:
                self.ecran.blit(p.image, (p.rect.x - self.camera_x, p.rect.y))
            for fin in self.declencheurs_fin:
                self.ecran.blit(fin.image, (fin.rect.x - self.camera_x, fin.rect.y))
                
            # Effet visuel étoile (filtre or/jaune) ou clignotement dégâts
            if self.joueur.invincible > 120 and (self.joueur.invincible // 4) % 2 == 0:
                img_copy = self.joueur.image.copy()
                img_copy.fill(COLOR_GOLD, special_flags=pygame.BLEND_MULT)
                self.ecran.blit(img_copy, (self.joueur.rect.x - self.camera_x, self.joueur.rect.y))
            elif not (self.joueur.invincible > 0 and self.joueur.invincible <= 120 and (self.joueur.invincible // 4) % 2 == 0):
                self.ecran.blit(self.joueur.image, (self.joueur.rect.x - self.camera_x, self.joueur.rect.y))
            
            txt_score = self.font_jeu.render(f"SCORE: {self.joueur.score_niveau:05d}", True, COLOR_WHITE)
            txt_pieces = self.font_jeu.render(f"PIÈCES: {self.joueur.pieces_recoltees:02d}", True, COLOR_GOLD)
            txt_temps = self.font_jeu.render(f"TEMPS: {self.temps_restant:03d}", True, COLOR_WHITE)
            txt_niv = self.font_jeu.render(f"NIVEAU {self.index_niveau_actuel + 1}", True, COLOR_WHITE)
            
            self.ecran.blit(txt_score, (20, 20))
            self.ecran.blit(txt_pieces, (250, 20))
            self.ecran.blit(txt_temps, (500, 20))
            self.ecran.blit(txt_niv, (680, 20))
            
        elif self.etat == "GAME_OVER":
            txt_go = self.font_titre.render("GAME OVER", True, COLOR_RED)
            txt_sub = self.font_menu.render("Appuyez sur une touche pour continuer...", True, COLOR_WHITE)
            self.ecran.blit(txt_go, (280, 220))
            self.ecran.blit(txt_sub, (220, 320))
            
        elif self.etat == "ECRAN_VICTOIRE":
            txt_vic = self.font_titre.render("NIVEAU COMPLÉTÉ !", True, COLOR_GREEN)
            txt_sub = self.font_menu.render("Magnifique ! Cliquez pour continuer.", True, COLOR_WHITE)
            self.ecran.blit(txt_vic, (200, 220))
            self.ecran.blit(txt_sub, (240, 320))

        pygame.display.flip()

    def executer(self):
        boucle = True
        while boucle:
            boucle = self.gerer_evenements()
            self.mettre_a_jour()
            self.dessiner()
            self.horloge.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    jeu = GestionnaireJeu()
    jeu.executer()
