import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# Fonction pour initialiser la base de données
def initialiser_bdd():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()

    # Table utilisateur
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)

    # Table projectile
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS projectile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            masse REAL,
            rayon REAL
        )
    """)

    # Table conditions
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gravite REAL,
            masse_volumique_air REAL,
            coefficient_trainee REAL
        )
    """)

    # Table session
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER,
            date_session TEXT,
            FOREIGN KEY(utilisateur_id) REFERENCES utilisateur(id)
        )
    """)

    # Table simulation
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS simulation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vitesse_initiale REAL,
            angle_deg REAL,
            masse REAL,
            rayon REAL,
            date_simulation TEXT,
            distance_max REAL,
            hauteur_max REAL,
            session_id INTEGER,
            FOREIGN KEY(session_id) REFERENCES session(id)
        )
    """)

    connexion.commit()
    connexion.close()

# Fonction pour ajouter un utilisateur de test
def ajouter_utilisateur_test():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("INSERT OR IGNORE INTO utilisateur (nom, email) VALUES (?, ?)", ("TestUser", "test@example.com"))
    connexion.commit()
    connexion.close()

# Fonction pour ajouter un projectile de test
def ajouter_projectile_test():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("INSERT OR IGNORE INTO projectile (nom, masse, rayon) VALUES (?, ?, ?)", ("Balle", 0.2, 0.05))
    connexion.commit()
    connexion.close()

# Fonction pour ajouter des conditions par défaut
def ajouter_conditions_test():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("INSERT OR IGNORE INTO conditions (id, gravite, masse_volumique_air, coefficient_trainee) VALUES (1, ?, ?, ?)", (9.81, 1.225, 0.47))
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
def modele_projectile(t, etat, masse):
    x, y, vx, vy = etat
    vitesse = np.sqrt(vx**2 + vy**2)
    dxdt = vx
    dydt = vy
    dvxdt = -(coeff_resistance / masse) * vx * vitesse
    dvydt = -gravite - (coeff_resistance / masse) * vy * vitesse
    return np.array([dxdt, dydt, dvxdt, dvydt])

# Lancer simulation
def lancer_simulation():
    try:
        utilisateur_id = utilisateurs_ids[combo_utilisateur.current()]
        projectile_id = projectiles_ids[combo_projectile.current()]

        vitesse_initiale = float(entry_vitesse.get())
        angle_deg = float(entry_angle.get())

        # Récupérer projectile choisi
        connexion = sqlite3.connect("simulations.db")
        curseur = connexion.cursor()
        curseur.execute("SELECT masse, rayon FROM projectile WHERE id = ?", (projectile_id,))
        masse_projectile, rayon_projectile = curseur.fetchone()

        # Récupérer conditions environnementales
        curseur.execute("SELECT gravite, masse_volumique_air, coefficient_trainee FROM conditions WHERE id = 1")
        global gravite, masse_volumique_air, coefficient_trainee
        gravite, masse_volumique_air, coefficient_trainee = curseur.fetchone()

        connexion.commit()
        connexion.close()

        # Créer une session
        connexion = sqlite3.connect("simulations.db")
        curseur = connexion.cursor()
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        curseur.execute("INSERT INTO session (utilisateur_id, date_session) VALUES (?, ?)", (utilisateur_id, date_now))
        session_id = curseur.lastrowid
        connexion.commit()
        connexion.close()

        # Préparation de la simulation
        angle_rad = np.radians(angle_deg)
        section_transversale = np.pi * rayon_projectile**2
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
            etats[i] = pas_rk4(lambda t, e: modele_projectile(t, e, masse_projectile), temps[i-1], etats[i-1], pas_temps)
            if etats[i, 1] < 0:
                etats[i, 1] = 0
                break

        x = etats[:i+1, 0]
        y = etats[:i+1, 1]
        distance_max = max(x)
        hauteur_max = max(y)

        # Enregistrement simulation
        connexion = sqlite3.connect("simulations.db")
        curseur = connexion.cursor()
        curseur.execute("""
            INSERT INTO simulation (vitesse_initiale, angle_deg, masse, rayon, date_simulation, distance_max, hauteur_max, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (vitesse_initiale, angle_deg, masse_projectile, rayon_projectile, date_now, distance_max, hauteur_max, session_id))
        connexion.commit()
        connexion.close()

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

    except Exception as e:
        messagebox.showerror("Erreur", str(e))

# Initialiser la base de données
initialiser_bdd()
ajouter_utilisateur_test()
ajouter_projectile_test()
ajouter_conditions_test()

# Interface graphique
root = tk.Tk()
root.title("Simulation Avancée de Projectile")

# Choix utilisateur
tk.Label(root, text="Sélectionner Utilisateur:").grid(row=0, column=0)
connexion = sqlite3.connect("simulations.db")
curseur = connexion.cursor()
curseur.execute("SELECT id, nom FROM utilisateur")
utilisateurs = curseur.fetchall()
utilisateurs_noms = [u[1] for u in utilisateurs]
utilisateurs_ids = [u[0] for u in utilisateurs]
connexion.close()
combo_utilisateur = ttk.Combobox(root, values=utilisateurs_noms)
combo_utilisateur.grid(row=0, column=1)
combo_utilisateur.current(0)

# Choix projectile
tk.Label(root, text="Sélectionner Projectile:").grid(row=1, column=0)
connexion = sqlite3.connect("simulations.db")
curseur = connexion.cursor()
curseur.execute("SELECT id, nom FROM projectile")
projectiles = curseur.fetchall()
projectiles_noms = [p[1] for p in projectiles]
projectiles_ids = [p[0] for p in projectiles]
connexion.close()
combo_projectile = ttk.Combobox(root, values=projectiles_noms)
combo_projectile.grid(row=1, column=1)
combo_projectile.current(0)

# Vitesse et angle
tk.Label(root, text="Vitesse initiale (m/s)").grid(row=2, column=0)
entry_vitesse = tk.Entry(root)
entry_vitesse.grid(row=2, column=1)



tk.Label(root, text="Angle de lancement (°)").grid(row=3, column=0)
entry_angle = tk.Entry(root)
entry_angle.grid(row=3, column=1)

# Boutons
tk.Button(root, text="Lancer Simulation", command=lancer_simulation).grid(row=4, column=0, pady=10)
tk.Button(root, text="Quitter", command=root.quit).grid(row=4, column=1, pady=10)

root.mainloop()
