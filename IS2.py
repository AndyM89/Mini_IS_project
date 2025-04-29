import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# Fonction pour initialiser la base de données
def initialiser_bdd():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
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
    connexion.commit()
    connexion.close()

# Fonction RK4
def pas_rk4(fonction, t, etat, pas_temps):
    k1 = fonction(t, etat)
    k2 = fonction(t + pas_temps/2, etat + pas_temps/2 * k1)
    k3 = fonction(t + pas_temps/2, etat + pas_temps/2 * k2)
    k4 = fonction(t + pas_temps, etat + pas_temps * k3)
    return etat + pas_temps/6 * (k1 + 2*k2 + 2*k3 + k4)

# Modèle physique du projectile
def modele_projectile(t, etat):
    x, y, vx, vy = etat
    vitesse = np.sqrt(vx**2 + vy**2)
    dxdt = vx
    dydt = vy
    dvxdt = -(coeff_resistance/masse) * vx * vitesse
    dvydt = -gravite - (coeff_resistance/masse) * vy * vitesse
    return np.array([dxdt, dydt, dvxdt, dvydt])

# Enregistrement dans la BDD
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

# Affichage des simulations passées
def afficher_historique():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("SELECT * FROM simulation")
    resultats = curseur.fetchall()
    historique = ""
    for ligne in resultats:
        historique += f"ID: {ligne[0]} | Vitesse: {ligne[1]} m/s | Angle: {ligne[2]}\u00b0 | Masse: {ligne[3]} kg | Distance max: {ligne[6]:.2f} m\n"
    connexion.close()
    messagebox.showinfo("Historique", historique)

# Lancer une simulation
def lancer_simulation():
    try:
        vitesse_initiale = float(entry_vitesse.get())
        angle_deg = float(entry_angle.get())
        global masse
        masse = float(entry_masse.get())
        rayon = float(entry_rayon.get())

        # Calculs
        angle_rad = np.radians(angle_deg)
        section_transversale = np.pi * rayon**2
        global coeff_resistance
        coeff_resistance = 0.5 * masse_volumique_air * coefficient_trainee * section_transversale
        vx0 = vitesse_initiale * np.cos(angle_rad)
        vy0 = vitesse_initiale * np.sin(angle_rad)
        etat_initial = np.array([0, 0, vx0, vy0])

        pas_temps = 0.01
        temps_max = 10
        steps = int(temps_max / pas_temps)
        temps = np.linspace(0, temps_max, steps)
        etats = np.zeros((steps, 4))
        etats[0] = etat_initial

        for i in range(1, steps):
            etats[i] = pas_rk4(modele_projectile, temps[i-1], etats[i-1], pas_temps)
            if etats[i, 1] < 0:
                etats[i, 1] = 0
                break

        x = etats[:i+1, 0]
        y = etats[:i+1, 1]
        distance_max = max(x)
        hauteur_max = max(y)

        enregistrer_simulation(vitesse_initiale, angle_deg, masse, rayon, distance_max, hauteur_max)
        messagebox.showinfo("Résultats", f"Distance max = {distance_max:.2f} m\nHauteur max = {hauteur_max:.2f} m")

        plt.figure(figsize=(10, 6))
        plt.plot(x, y, label=f"Vitesse = {vitesse_initiale} m/s, Angle = {angle_deg}°")
        plt.title("Trajectoire d'un projectile")
        plt.xlabel("Distance (m)")
        plt.ylabel("Hauteur (m)")
        plt.grid(True)
        plt.legend()
        plt.axhline(0, color='black', linewidth=0.5)
        plt.show()

    except ValueError:
        messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")

# Paramètres fixes
gravite = 9.81
masse_volumique_air = 1.225
coefficient_trainee = 0.47

# Initialisation de la BDD
initialiser_bdd()

# Interface graphique
root = tk.Tk()
root.title("Simulation de Projectile")

# Champs de saisie
tk.Label(root, text="Vitesse initiale (m/s)").grid(row=0, column=0)
entry_vitesse = tk.Entry(root)
entry_vitesse.grid(row=0, column=1)

tk.Label(root, text="Angle de lancement (°)").grid(row=1, column=0)
entry_angle = tk.Entry(root)
entry_angle.grid(row=1, column=1)

tk.Label(root, text="Masse du projectile (kg)").grid(row=2, column=0)
entry_masse = tk.Entry(root)
entry_masse.grid(row=2, column=1)

tk.Label(root, text="Rayon du projectile (m)").grid(row=3, column=0)
entry_rayon = tk.Entry(root)
entry_rayon.grid(row=3, column=1)

# Boutons
tk.Button(root, text="Lancer Simulation", command=lancer_simulation).grid(row=4, column=0, pady=10)
tk.Button(root, text="Afficher Historique", command=afficher_historique).grid(row=4, column=1, pady=10)
tk.Button(root, text="Quitter", command=root.quit).grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
