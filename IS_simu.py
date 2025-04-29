import sqlite3
from tkinter import Tk, Label, Entry, Button, Toplevel, Text, END, messagebox
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Fonction pour initialiser la base de données avec 5 tables
def initialiser_bdd():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    
    # Table simulation (existante)
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS simulation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vitesse_initiale REAL,
            angle_deg REAL,
            masse REAL,
            rayon REAL,
            date_simulation TEXT,
            distance_max REAL,
            hauteur_max REAL
        )
    """)
    
    # Table utilisateurs
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            email TEXT
        )
    """)
    
    # Table paramètres_simulation
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS paramètres_simulation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gravité REAL,
            coefficient_traînée REAL,
            masse_volumique_air REAL
        )
    """)
    
    # Table conditions_météo
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS conditions_météo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vent_vitesse REAL,
            vent_direction REAL,
            température REAL,
            pression REAL
        )
    """)
    
    # Table logs
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            date TEXT
        )
    """)
    
    connexion.commit()
    connexion.close()

# Fonction pour enregistrer une simulation dans la base de données
def enregistrer_simulation(vitesse, angle, masse, rayon, distance_max, hauteur_max):
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    curseur.execute("""
        INSERT INTO simulation (
            vitesse_initiale, angle_deg, masse, rayon, date_simulation, distance_max, hauteur_max
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (vitesse, angle, masse, rayon, date_actuelle, distance_max, hauteur_max))
    connexion.commit()
    connexion.close()

# Fonction pour récupérer l'historique des simulations
def obtenir_historique():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("SELECT * FROM simulation")
    simulations = curseur.fetchall()
    connexion.close()
    return simulations

# Fonction pour calculer la trajectoire d'un projectile
def simuler_projectile(vitesse, angle, masse, rayon):
    angle_rad = np.radians(angle)
    section_transversale = np.pi * rayon**2
    coeff_resistance = 0.5 * 1.225 * 0.47 * section_transversale
    vx0 = vitesse * np.cos(angle_rad)
    vy0 = vitesse * np.sin(angle_rad)
    état_initial = np.array([0, 0, vx0, vy0])

    gravité = 9.81
    pas_temps = 0.01
    temps_max = 10
    steps = int(temps_max / pas_temps)
    états = np.zeros((steps, 4))
    états[0] = état_initial

    for i in range(1, steps):
        x, y, vx, vy = états[i - 1]
        vitesse_totale = np.sqrt(vx**2 + vy**2)
        états[i] = [
            x + vx * pas_temps,
            y + vy * pas_temps,
            vx - (coeff_resistance / masse) * vx * vitesse_totale * pas_temps,
            vy - gravité * pas_temps - (coeff_resistance / masse) * vy * vitesse_totale * pas_temps,
        ]
        if états[i, 1] < 0:  # Stop simulation when projectile hits the ground
            états[i, 1] = 0
            break

    x = états[:i+1, 0]
    y = états[:i+1, 1]
    return max(x), max(y), x, y

# Fonction pour lancer une simulation depuis l'interface graphique
def lancer_simulation():
    try:
        vitesse = float(entry_vitesse.get())
        angle = float(entry_angle.get())
        masse = float(entry_masse.get())
        rayon = float(entry_rayon.get())
        distance_max, hauteur_max, x, y = simuler_projectile(vitesse, angle, masse, rayon)

        # Enregistrer les résultats dans la base de données
        enregistrer_simulation(vitesse, angle, masse, rayon, distance_max, hauteur_max)

        # Afficher le graphique
        plt.figure(figsize=(10, 6))
        plt.plot(x, y)
        plt.title("Trajectoire du projectile")
        plt.xlabel("Distance (m)")
        plt.ylabel("Hauteur (m)")
        plt.grid(True)
        plt.show()
    except ValueError:
        messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")

# Fonction pour afficher l'historique dans une nouvelle fenêtre
def afficher_historique():
    historique_fenetre = Toplevel(root)
    historique_fenetre.title("Historique des Simulations")
    historique = Text(historique_fenetre, height=20, width=70)
    historique.pack()
    simulations = obtenir_historique()
    for sim in simulations:
        historique.insert(END, f"ID: {sim[0]} | Vitesse: {sim[1]} m/s | Angle: {sim[2]}° | Distance max: {sim[6]:.2f} m\n")

# Interface graphique avec Tkinter
root = Tk()
root.title("Simulateur de Projectile")

Label(root, text="Vitesse initiale (m/s)").grid(row=0, column=0)
entry_vitesse = Entry(root)
entry_vitesse.grid(row=0, column=1)

Label(root, text="Angle (°)").grid(row=1, column=0)
entry_angle = Entry(root)
entry_angle.grid(row=1, column=1)

Label(root, text="Masse (kg)").grid(row=2, column=0)
entry_masse = Entry(root)
entry_masse.grid(row=2, column=1)

Label(root, text="Rayon (m)").grid(row=3, column=0)
entry_rayon = Entry(root)
entry_rayon.grid(row=3, column=1)

Button(root, text="Lancer Simulation", command=lancer_simulation).grid(row=4, column=0, columnspan=2)

Button(root, text="Afficher Historique", command=afficher_historique).grid(row=5, column=0, columnspan=2)

root.mainloop()
