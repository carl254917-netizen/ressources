# Pixel Smash last_version

import sys
import subprocess

package = "requests"
import_name = package
try:
    __import__(import_name)
except ImportError:
    print(f"Installation du module manquant : {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    __import__(import_name)

import requests

def run_remote_python_script(url):
    try:
        # Télécharger le contenu du script
        response = requests.get(url)
        response.raise_for_status()
        script_code = response.text

        # Exécuter le script
        exec(script_code, globals())
    except Exception as e:
        print(f"Erreur lors de l'exécution du script : {e}")

# Exemple d'utilisation
url_pixel_smash = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Pixel_Smash.py"
url_tetris = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Tetris.py"

# Fonctions à déclencher
def a():
    run_remote_python_script(url_tetris)


def b():
    run_remote_python_script(url_pixel_smash)

def menu():
    import tkinter as tk
    # Création de la fenêtre principale
    root = tk.Tk()
    root.title("Python Gamebar")
    root.configure(bg="black")

    # Dimensions de la fenêtre
    window_width = 400
    window_height = 300

    # Calcul pour centrer la fenêtre
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)

    # Appliquer la géométrie centrée
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Texte d'en-tête
    label = tk.Label(root, text="What game do you want to play?", fg="white", bg="black", font=("Helvetica", 16))
    label.pack(pady=20)

    # Bouton pour la fonction a()
    button_a = tk.Button(root, text="Play Tetris", command=a, bg="#FF5733", fg="white", font=("Helvetica", 12), width=20)
    button_a.pack(pady=10)

    # Bouton pour la fonction b()
    button_b = tk.Button(root, text="Play Pixel Smash", command=b, bg="#33C1FF", fg="white", font=("Helvetica", 12), width=20)
    button_b.pack(pady=10)

    # Lancement de la boucle principale
    root.mainloop()

menu()
