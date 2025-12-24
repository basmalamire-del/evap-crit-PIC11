import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from evaporateurs import EvaporateurMultiple
from cristallisation import simuler_cristallisation_batch

try:
    from sensibilite import sensibilite_parametre, sensibilite_2D
except Exception:
    from sensibilite import sensibilité_parametre as sensibilite_parametre  # type: ignore
    from sensibilite import sensibilité_2D as sensibilite_2D  # type: ignore


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_fig(fig, filename: str):
    ensure_dir("figures")
    fig.tight_layout()
    fig.savefig(os.path.join("figures", filename), dpi=200)
    plt.close(fig)


def scenario():
    ensure_dir("figures")
    ensure_dir("exports")

    # Paramètres
    F, xF, xout, Tfeed, Psteam, n_effets = 20000.0, 0.15, 0.65, 85.0, 3.5, 3
    M_batch, C_init, T_init, duree_h, dt_s, profil = 5000.0, 65.0, 70.0, 4.0, 60.0, "lineaire"

    # 1) Evaporation
    evap = EvaporateurMultiple(F, xF, xout, Tfeed, Psteam, n_effets)
    res = evap.simuler()

    x = res.get("x", None)
    T = res.get("T", None)
    A = res.get("A", None)
    L = res.get("L", None)
    V = res.get("V", None)

    effets = np.arange(1, len(x) + 1) if x is not None else np.arange(1, n_effets + 1)

    df_evap = pd.DataFrame({"Effet": effets})
    if x is not None: df_evap["x"] = x
    if T is not None: df_evap["Teb (°C)"] = T
    if A is not None: df_evap["A (m²)"] = A
    if L is not None: df_evap["L (kg/h)"] = L
    if V is not None: df_evap["V (kg/h)"] = V
    df_evap.to_csv("exports/evaporation_resultats.csv", index=False)

    fig, ax = plt.subplots()
    ax.plot(effets, x, marker="o")
    ax.set_title("x vs effets")
    ax.grid(True)
    save_fig(fig, "evap_x.png")

    # 2) Cristallisation
    duree_s = int(duree_h * 3600)
    _, _, hist = simuler_cristallisation_batch(M_batch, C_init, T_init, duree_s, dt=dt_s, profil=profil)

    df_cr = pd.DataFrame({"t (s)": hist["t"]})
    for k in ["T", "S", "C", "Cs", "CV"]:
        if k in hist:
            df_cr[k] = hist[k]
    if "Lmean" in hist:
        df_cr["Lmean"] = hist["Lmean"]
    if "L_moy" in hist:
        df_cr["L_moy"] = hist["L_moy"]

    df_cr.to_csv("exports/cristallisation_resultats.csv", index=False)

    print("✅ Fichiers générés :")
    print(" - exports/evaporation_resultats.csv")
    print(" - exports/cristallisation_resultats.csv")
    print(" - figures/*.png")


if __name__ == "__main__":
    scenario()