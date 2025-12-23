# evaporateurs.py
import numpy as np
from thermodynamique import Tsat_water_from_Pbar, latent_heat_kJkg, LMTD, to_float

def simuler_evaporation_multi_effets(
    n_effets: int,
    F_kg_h: float,
    xF: float,
    xout: float,
    T_feed_C: float,
    P_vapeur_bar: float,
    U_W_m2K: float = 1800.0,
    T_last_C: float = 60.0
):
    """
    Simulation simplifiée mais robuste d'une batterie multi-effets.
    Retour dict avec grandeurs scalaires + profils par effet.

    Hypothèses:
    - Bilan matière: soluté conservé, xout imposé
    - V_total = F - L
    - Economie ~ n_effets * 0.95 (valeur typique, stable)
    - Répartition de ΔT total sur effets de manière uniforme
    - Surface estimée via Q = V*lambda ≈ U*A*ΔT_lm
    """
    n = int(max(n_effets, 1))

    F = to_float(F_kg_h, 1.0)
    xF = float(max(min(xF, 0.95), 1e-6))
    xout = float(max(min(xout, 0.95), xF + 1e-6))
    Tfeed = to_float(T_feed_C, 25.0)
    Psteam = to_float(P_vapeur_bar, 2.0)

    # Produit liquide final (L) via conservation du soluté
    solute = F * xF
    L_final = solute / xout
    V_total = max(F - L_final, 0.0)

    # Economie (kg évaporé / kg vapeur)
    economie = max(0.8, 0.95 * n)
    S_steam = V_total / economie  # kg/h vapeur motrice

    # Températures
    T_steam = Tsat_water_from_Pbar(Psteam)
    T_last = min(to_float(T_last_C, 60.0), T_steam - 5.0)

    dT_total = max(T_steam - T_last, 10.0)
    dT_eff = dT_total / n

    T_cond = [T_steam - i * dT_eff for i in range(n)]
    T_boil = [T_steam - (i + 1) * dT_eff for i in range(n)]

    # Répartition d’évaporation par effet (simple)
    V_i = np.full(n, V_total / n, dtype=float)

    # Débits liquides par effet
    L_i = np.zeros(n, dtype=float)
    L_i[0] = F - V_i[0]
    for i in range(1, n):
        L_i[i] = L_i[i - 1] - V_i[i]

    # Concentrations par effet
    x_i = np.zeros(n, dtype=float)
    for i in range(n):
        denom = max(L_i[i], 1e-9)
        x_i[i] = solute / denom

    # Surface (estimation)
    # Q_i ≈ V_i * lambda(T_boil)
    # lambda en kJ/kg -> W*h/kg = (kJ/kg)*(1000J/kJ) / 3600
    A_i = np.zeros(n, dtype=float)
    for i in range(n):
        lam_kJkg = latent_heat_kJkg(T_boil[i])
        Q_Wh = V_i[i] * (lam_kJkg * 1000.0 / 3600.0)  # W*h
        # ΔT_lm ~ dT_eff (stable)
        dTlm = max(dT_eff, 1.0)
        # A = Q / (U*ΔT) ; Q en W*h → convert vers W en divisant par 1h (donc identique)
        A_i[i] = max(Q_Wh / (U_W_m2K * dTlm), 0.0)

    res = {
        "S": float(S_steam),
        "economie": float(economie),
        "A_total": float(np.sum(A_i)),
        "V_total": float(V_total),
        "L_final": float(L_final),
        "T_steam": float(T_steam),
        "effets": np.arange(1, n + 1, dtype=int),
        "V_i": V_i,
        "L_i": L_i,
        "x_i": x_i,
        "T_boil": np.array(T_boil, dtype=float),
        "T_cond": np.array(T_cond, dtype=float),
        "A_i": A_i,
    }
    return res
