import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import matplotlib.pyplot as plt
import math

DB_NAME = 'projectile_simulation.db'

# Définir uniquement les tables utiles
TABLES = {
    'Condition': ['temperature', 'vent', 'humidite']
}

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Projectile
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Projectile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            masse REAL NOT NULL,
            section REAL NOT NULL,
            coefficient_frottement REAL NOT NULL
        );""")
    # Utilisateur
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );""")
    # Condition
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Condition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            vent REAL,
            humidite REAL
        );""")
    # Simulation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Simulation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER NOT NULL,
            projectile_id INTEGER NOT NULL,
            condition_id INTEGER NOT NULL,
            date_lancement TEXT NOT NULL,
            FOREIGN KEY(utilisateur_id) REFERENCES Utilisateur(id),
            FOREIGN KEY(projectile_id) REFERENCES Projectile(id),
            FOREIGN KEY(condition_id) REFERENCES Condition(id)
        );""")
    # Resultat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Resultat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id INTEGER NOT NULL,
            vitesse_max REAL,
            distance_max REAL,
            FOREIGN KEY(simulation_id) REFERENCES Simulation(id)
        );""")
    conn.commit()
    conn.close()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulation Projectile Simplifiée")
        self.geometry("750x500")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        
        # Garder uniquement Condition
        for table, fields in TABLES.items():
            tab = EntityTab(self.notebook, table, fields)
            self.notebook.add(tab, text=table)
        
        # Onglet Simulation Trajectoire
        sim_tab = SimulationTab(self.notebook)
        self.notebook.add(sim_tab, text="Simulation Trajectoire")

class EntityTab(ttk.Frame):
    def __init__(self, container, table, fields):
        super().__init__(container)
        self.table = table
        self.fields = fields
        self.entries = {}
        
        form_frame = ttk.Frame(self)
        form_frame.pack(side='top', fill='x', padx=10, pady=10)
        
        for idx, field in enumerate(fields):
            lbl = ttk.Label(form_frame, text=field.capitalize() + ":")
            lbl.grid(row=idx, column=0, sticky='e', padx=5, pady=5)
            ent = ttk.Entry(form_frame)
            ent.grid(row=idx, column=1, sticky='w', padx=5, pady=5)
            self.entries[field] = ent
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(btn_frame, text="Ajouter Condition", command=self.add_record).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Mettre à jour", command=self.update_record).pack(side='left', padx=5)
        
        self.tree = ttk.Treeview(self, columns=['id'] + fields, show='headings')
        for col in ['id'] + fields:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=100, anchor='center')
        
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        self.load_records()

    def run_query(self, query, parameters=()):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        return cursor

    def load_records(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cursor = self.run_query(f"SELECT id, {', '.join(self.fields)} FROM {self.table}")
        for record in cursor.fetchall():
            self.tree.insert('', 'end', values=record)

    def add_record(self):
        values = [self.entries[field].get() for field in self.fields]
        placeholders = ', '.join('?' * len(values))
        try:
            self.run_query(f"INSERT INTO {self.table} ({', '.join(self.fields)}) VALUES ({placeholders})", values)
            self.load_records()
            messagebox.showinfo("Succès", "Condition ajoutée")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            for idx, field in enumerate(self.fields):
                self.entries[field].delete(0, tk.END)
                self.entries[field].insert(0, values[idx+1])

    def update_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez une Condition")
            return
        record_id = self.tree.item(selected[0])['values'][0]
        values = [self.entries[field].get() for field in self.fields]
        assignments = ', '.join([f"{f}=?" for f in self.fields])
        try:
            self.run_query(
                f"UPDATE {self.table} SET {assignments} WHERE id=?",
                values + [record_id]
            )
            self.load_records()
            messagebox.showinfo("Succès", "Condition mise à jour")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

class SimulationTab(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)
        
        self.entries = {}
        fields = ['Nom', 'Masse (kg)', 'Coeff_frottement', 'Angle (°)', 'Vitesse initiale (m/s)']
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=20)
        
        for idx, field in enumerate(fields):
            lbl = ttk.Label(form_frame, text=field + ":")
            lbl.grid(row=idx, column=0, sticky='e', padx=5, pady=5)
            ent = ttk.Entry(form_frame)
            ent.grid(row=idx, column=1, sticky='w', padx=5, pady=5)
            self.entries[field] = ent
        
        ttk.Button(self, text="Lancer Simulation", command=self.launch_simulation).pack(pady=10)

    def runge_kutta_4(self, f, t0, y0, h, n):
        t, y = t0, y0
        ts, ys = [t0], [y0]
        for _ in range(n):
            k1 = f(t, y)
            k2 = f(t + h/2, [y[i] + h/2 * k1[i] for i in range(len(y))])
            k3 = f(t + h/2, [y[i] + h/2 * k2[i] for i in range(len(y))])
            k4 = f(t + h, [y[i] + h * k3[i] for i in range(len(y))])
            y = [y[i] + h/6 * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) for i in range(len(y))]
            t += h
            ts.append(t)
            ys.append(y)
        return ts, ys

    def launch_simulation(self):
        try:
            nom = self.entries['Nom'].get()
            masse = float(self.entries['Masse (kg)'].get())
            coeff_frottement = float(self.entries['Coeff_frottement'].get())
            angle_deg = float(self.entries['Angle (°)'].get())
            vitesse_init = float(self.entries['Vitesse initiale (m/s)'].get())
            angle_rad = math.radians(angle_deg)
            
            vx0 = vitesse_init * math.cos(angle_rad)
            vy0 = vitesse_init * math.sin(angle_rad)
            g = 9.81

            def equations(t, y):
                x, y_pos, vx, vy = y
                v = math.sqrt(vx**2 + vy**2)
                fx = - coeff_frottement * v * vx / masse
                fy = - masse * g - coeff_frottement * v * vy / masse
                return [vx, vy, fx, fy]

            y0 = [0, 0, vx0, vy0]
            t0 = 0
            h = 0.01
            n = 1000

            ts, ys_ = self.runge_kutta_4(equations, t0, y0, h, n)

            xs = [p[0] for p in ys_]
            ys_positions = [p[1] for p in ys_]

            # Affichage du graphe
            plt.plot(xs, ys_positions)
            plt.xlabel('Distance (m)')
            plt.ylabel('Hauteur (m)')
            plt.title('Trajectoire du projectile')
            plt.grid()
            plt.show()

            # Sauvegarde automatique dans la base
            self.save_simulation(nom, masse, coeff_frottement, vitesse_init, max(xs), max([math.sqrt(p[2]**2 + p[3]**2) for p in ys_]))

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def save_simulation(self, nom, masse, coeff_frottement, vitesse_init, distance_max, vitesse_max):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Vérifier utilisateur par défaut
        cursor.execute("SELECT id FROM Utilisateur WHERE nom='Default'")
        user = cursor.fetchone()
        if not user:
            cursor.execute("INSERT INTO Utilisateur (nom, email) VALUES ('Default', 'default@example.com')")
            conn.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user[0]

        # Ajouter projectile
        cursor.execute("INSERT INTO Projectile (nom, masse, section, coefficient_frottement) VALUES (?, ?, ?, ?)",
                       (nom, masse, 0.01, coeff_frottement))
        projectile_id = cursor.lastrowid

        # Ajouter condition par défaut si vide
        cursor.execute("SELECT id FROM Condition")
        condition = cursor.fetchone()
        if not condition:
            cursor.execute("INSERT INTO Condition (temperature, vent, humidite) VALUES (20, 0, 50)")
            conn.commit()
            condition_id = cursor.lastrowid
        else:
            condition_id = condition[0]

        # Ajouter simulation
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO Simulation (utilisateur_id, projectile_id, condition_id, date_lancement) VALUES (?, ?, ?, ?)",
                       (user_id, projectile_id, condition_id, now))
        simulation_id = cursor.lastrowid

        # Ajouter résultat
        cursor.execute("INSERT INTO Resultat (simulation_id, vitesse_max, distance_max) VALUES (?, ?, ?)",
                       (simulation_id, vitesse_max, distance_max))
        conn.commit()
        conn.close()

        messagebox.showinfo("Succès", "Simulation et Résultats sauvegardés avec succès !")

if __name__ == "__main__":
    create_tables()
    app = App()
    app.mainloop()
