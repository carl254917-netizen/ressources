# Arcade.py (Auto-Update Version)

import sys
import subprocess
import os

# --- CONFIGURATION DES MISES À JOUR ---
VERSION_ACTUELLE = "1.0"
# Remplace ces URL par les liens "Raw" de tes fichiers sur GitHub
URL_VERSION = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Arcade_version.txt"
URL_ARCADE_SCRIPT = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Arcade.py"

# --- INSTALLATION DES DÉPENDANCES ---
package = "requests"
try:
    import requests
except ImportError:
    print(f"Installation du module manquant : {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    import requests

# --- SYSTÈME D'AUTO-MISE À JOUR ---
def verifier_mise_a_jour():
    print(f"Version actuelle : {VERSION_ACTUELLE}")
    print("Vérification des mises à jour...")
    
    try:
        # Télécharge le numéro de version depuis GitHub
        reponse = requests.get(URL_VERSION, timeout=5)
        reponse.raise_for_status()
        derniere_version = reponse.text.strip()
        
        # Compare les versions
        if derniere_version != VERSION_ACTUELLE:
            print(f"Nouvelle version trouvée ({derniere_version}) ! Mise à jour en cours...")
            mettre_a_jour_le_script()
        else:
            print("Le programme est à jour.")
            
    except requests.exceptions.RequestException as e:
        print(f"Impossible de vérifier les mises à jour (Pas de connexion ou erreur) : {e}")

def mettre_a_jour_le_script():
    try:
        # Télécharge le nouveau code source
        reponse = requests.get(URL_ARCADE_SCRIPT, timeout=10)
        reponse.raise_for_status()
        nouveau_code = reponse.text
        
        # Écrase le fichier actuel (__file__) avec le nouveau code
        with open(__file__, 'w', encoding='utf-8') as fichier_local:
            fichier_local.write(nouveau_code)
            
        print("Mise à jour réussie. Redémarrage du programme...")
        
        # Redémarre le script instantanément avec la nouvelle version
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    except Exception as e:
        print(f"Erreur lors de la mise à jour : {e}")

# --- FONCTIONS DE JEUX ---
def run_remote_python_script(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        script_code = response.text
        exec(script_code, globals())
    except Exception as e:
        print(f"Erreur lors de l'exécution du script : {e}")

url_pixel_smash = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Pixel_Smash.py"
url_tetris = "https://raw.githubusercontent.com/carl254917-netizen/ressources/main/Tetris.py"

def a():
    run_remote_python_script(url_tetris)

def b():
    run_remote_python_script(url_pixel_smash)

# --- INTERFACE GRAPHIQUE ---
def menu():
    import tkinter as tk
    
    root = tk.Tk()
    root.title(f"Python Gamebar - v{VERSION_ACTUELLE}")
    root.configure(bg="black")

    window_width = 400
    window_height = 300
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    label = tk.Label(root, text="What game do you want to play?", fg="white", bg="black", font=("Helvetica", 16))
    label.pack(pady=20)

    button_a = tk.Button(root, text="Play Tetris", command=a, bg="#FF5733", fg="white", font=("Helvetica", 12), width=20)
    button_a.pack(pady=10)

    button_b = tk.Button(root, text="Play Pixel Smash", command=b, bg="#33C1FF", fg="white", font=("Helvetica", 12), width=20)
    button_b.pack(pady=10)

    root.mainloop()

# --- LANCEMENT ---
if __name__ == "__main__":
    verifier_mise_a_jour()
    menu()
