import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime

# Fonction pour initialiser la base de données
def initialiser_bdd():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS projectile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            masse REAL,
            rayon REAL
        )
    """)

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gravite REAL,
            masse_volumique_air REAL,
            coefficient_trainee REAL
        )
    """)

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER,
            date_session TEXT,
            FOREIGN KEY(utilisateur_id) REFERENCES utilisateur(id)
        )
    """)

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

def ajouter_utilisateur(nom, email):
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("INSERT INTO utilisateur (nom, email) VALUES (?, ?)", (nom, email))
    connexion.commit()
    connexion.close()

def ajouter_projectile(nom, masse, rayon):
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("INSERT INTO projectile (nom, masse, rayon) VALUES (?, ?, ?)", (nom, masse, rayon))
    connexion.commit()
    connexion.close()

def ajouter_conditions(gravite, masse_volumique_air, coefficient_trainee):
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("INSERT INTO conditions (gravite, masse_volumique_air, coefficient_trainee) VALUES (?, ?, ?)", (gravite, masse_volumique_air, coefficient_trainee))
    connexion.commit()
    connexion.close()

def creer_session(utilisateur_id):
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    curseur.execute("INSERT INTO session (utilisateur_id, date_session) VALUES (?, ?)", (utilisateur_id, date_now))
    session_id = curseur.lastrowid
    connexion.commit()
    connexion.close()
    return session_id

# Fonction RK4
def pas_rk4(fonction, t, état, pas_temps):
    k1 = fonction(t, état)
    k2 = fonction(t + pas_temps/2, état + pas_temps/2 * k1)
    k3 = fonction(t + pas_temps/2, état + pas_temps/2 * k2)
    k4 = fonction(t + pas_temps, état + pas_temps * k3)
    return état + pas_temps/6 * (k1 + 2*k2 + 2*k3 + k4)

# Modèle physique du projectile
def modèle_projectile(t, état):
    x, y, vx, vy = état
    vitesse = np.sqrt(vx**2 + vy**2)
    dxdt = vx
    dydt = vy
    dvxdt = -(coeff_resistance/masse) * vx * vitesse
    dvydt = -gravité - (coeff_resistance/masse) * vy * vitesse
    return np.array([dxdt, dydt, dvxdt, dvydt])

# Saisie utilisateur
def saisie_utilisateur():
    print("\n=== Nouvelle Simulation ===")
    vitesse_initiale = float(input("Vitesse initiale (m/s) : "))
    angle_deg = float(input("Angle de lancement (degrés) : "))
    masse = float(input("Masse du projectile (kg) : "))
    rayon = float(input("Rayon du projectile (m) : "))
    return vitesse_initiale, angle_deg, masse, rayon

# Enregistrement dans la BDD
def enregistrer_simulation(vitesse, angle, masse, rayon, distance_max, hauteur_max, session_id):
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    curseur.execute("""
        INSERT INTO simulation (
            vitesse_initiale, angle_deg, masse, rayon, date_simulation, distance_max, hauteur_max, session_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (vitesse, angle, masse, rayon, date_actuelle, distance_max, hauteur_max, session_id))
    connexion.commit()
    connexion.close()

# Affichage des simulations passées
def afficher_historique():
    connexion = sqlite3.connect("simulations.db")
    curseur = connexion.cursor()
    curseur.execute("SELECT * FROM simulation")
    print("\n=== Historique des Simulations ===")
    for ligne in curseur.fetchall():
        print(f"ID: {ligne[0]} | Vitesse: {ligne[1]} m/s | Angle: {ligne[2]}° | Masse: {ligne[3]} kg | Distance max: {ligne[6]:.2f} m")
    connexion.close()

# Paramètres fixes
gravité = 9.81
masse_volumique_air = 1.225
coefficient_traînée = 0.47

# Initialisation de la BDD
initialiser_bdd()

# Menu principal
while True:
    print("\n=== Menu Principal ===")
    print("1. Lancer une nouvelle simulation")
    print("2. Afficher l'historique")
    print("3. Quitter")
    choix = input("Choix : ")

    if choix == "1":
        connexion = sqlite3.connect("simulations.db")
        curseur = connexion.cursor()
        curseur.execute("SELECT id, nom FROM utilisateur")
        utilisateurs = curseur.fetchall()
        connexion.close()

        print("\n=== Sélectionnez un utilisateur ===")
        for user in utilisateurs:
            print(f"{user[0]}. {user[1]}")
        utilisateur_id = int(input("Entrez l'ID utilisateur : "))
        session_id = creer_session(utilisateur_id)

        vitesse_initiale, angle_deg, masse, rayon = saisie_utilisateur()

        angle_rad = np.radians(angle_deg)
        section_transversale = np.pi * rayon**2
        coeff_resistance = 0.5 * masse_volumique_air * coefficient_traînée * section_transversale
        vx0 = vitesse_initiale * np.cos(angle_rad)
        vy0 = vitesse_initiale * np.sin(angle_rad)
        état_initial = np.array([0, 0, vx0, vy0])

        pas_temps = 0.01
        temps_max = 10
        steps = int(temps_max / pas_temps)
        temps = np.linspace(0, temps_max, steps)
        états = np.zeros((steps, 4))
        états[0] = état_initial

        for i in range(1, steps):
            états[i] = pas_rk4(modèle_projectile, temps[i-1], états[i-1], pas_temps)
            if états[i, 1] < 0:
                états[i, 1] = 0
                break

        x = états[:i+1, 0]
        y = états[:i+1, 1]
        distance_max = max(x)
        hauteur_max = max(y)

        enregistrer_simulation(vitesse_initiale, angle_deg, masse, rayon, distance_max, hauteur_max, session_id)
        print(f"\nRésultats : Distance max = {distance_max:.2f} m | Hauteur max = {hauteur_max:.2f} m")

        plt.figure(figsize=(10, 6))
        plt.plot(x, y, label=f"Vitesse = {vitesse_initiale} m/s, Angle = {angle_deg}°")
        plt.title("Trajectoire d'un projectile")
        plt.xlabel("Distance (m)")
        plt.ylabel("Hauteur (m)")
        plt.grid(True)
        plt.legend()
        plt.axhline(0, color='black', linewidth=0.5)
        plt.show()

    elif choix == "2":
        afficher_historique()

    elif choix == "3":
        print("Au revoir !")
        break

    else:
        print("Choix invalide.")
