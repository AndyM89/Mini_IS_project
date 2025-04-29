import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Nom de la base de données
DB_NAME = 'projectile_simulation.db'

# Définir les tables et leurs champs
TABLES = {
    'Projectile': ['nom', 'masse', 'section', 'coefficient_frottement'],
    'Utilisateur': ['nom', 'email'],
    'Condition': ['temperature', 'vent', 'humidite'],
    'Simulation': ['utilisateur_id', 'projectile_id', 'condition_id', 'date_lancement'],
    'Resultat': ['simulation_id', 'vitesse_max', 'distance_max']
}

def create_tables():
    """Créer les tables dans la base de données"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Projectile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            masse REAL NOT NULL,
            section REAL NOT NULL,
            coefficient_frottement REAL NOT NULL
        );""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Condition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            vent REAL,
            humidite REAL
        );""")
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
        self.title("Gestion de Simulation de Projectiles")
        self.geometry("700x500")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        
        for table, fields in TABLES.items():
            tab = EntityTab(self.notebook, table, fields)
            self.notebook.add(tab, text=table)

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
        ttk.Button(btn_frame, text="Ajouter", command=self.add_record).pack(side='left', padx=5)
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
        values = []
        for field in self.fields:
            val = self.entries[field].get()
            if field == 'date_lancement' and not val:
                val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            values.append(val)
        placeholders = ', '.join('?' * len(values))
        try:
            self.run_query(f"INSERT INTO {self.table} ({', '.join(self.fields)}) VALUES ({placeholders})", values)
            self.load_records()
            messagebox.showinfo("Succès", f"Données ajoutées dans {self.table}")
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
            messagebox.showwarning("Attention", "Sélectionnez un enregistrement à mettre à jour")
            return
        record_id = self.tree.item(selected[0])['values'][0]
        values = []
        for field in self.fields:
            val = self.entries[field].get()
            if field == 'date_lancement' and not val:
                val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            values.append(val)
        assignments = ', '.join([f"{f}=?" for f in self.fields])
        try:
            self.run_query(
                f"UPDATE {self.table} SET {assignments} WHERE id=?",
                values + [record_id]
            )
            self.load_records()
            messagebox.showinfo("Succès", "Mise à jour réussie")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    create_tables()
    app = App()
    app.mainloop()
