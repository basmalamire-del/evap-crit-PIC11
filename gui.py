# gui.py
import tkinter as tk
from tkinter import messagebox
from main import scenario_base

def lancer_simulation():
    try:
        scenario_base()
        messagebox.showinfo("Simulation", "Simulation terminée.\nLes résultats sont dans le terminal et /resultats/")
    except Exception as e:
        messagebox.showerror("Erreur", str(e))


def interface():
    root = tk.Tk()
    root.title("Simulateur Evaporation - Cristallisation")

    lbl = tk.Label(root, text="Interface du Projet PIC\nEvaporateurs + Cristallisation", font=("Arial", 14))
    lbl.pack(pady=10)

    btn = tk.Button(root, text="Lancer simulation complète", font=("Arial", 12), command=lancer_simulation)
    btn.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    interface()
