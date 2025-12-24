# evaporateurs.py
import numpy as np


def simulation_evaporation_multi_effets(
    F_kg_h: float,
    xF: float,
    xout: float,
    n_effets: int,
    T_steam_C: float = 120.0,
    T_last_C: float = 60.0,
    U: float = 1500.0,  # W/m2/K
    lambda_kJ_kg: float = 2257.0
):
    """
    Modèle pédagogique (scalaire + valeurs par effet) pour évaporation multiple.
    Retourne un dict : S, economie, A_total, V_total, P, details (par effet)
    """

    # sécuriser types
    F_kg_h = float(F_kg_h)
    xF = float(xF)
    xout = float(xout)
    n = int(n_effets)
    T_steam_C = float(T_steam_C)
    T_last_C = float(T_last_C)
    U = float(U)
    lambda_kJ_kg = float(lambda_kJ_kg)

    if n < 1:
        raise ValueError("n_effets doit être >= 1")
    if xF <= 0 or xout <= 0 or xout <= xF:
        raise ValueError("Vérifier xF et xout (xout doit être > xF).")
    if T_steam_C <= T_last_C:
        raise ValueError("T_steam_C doit être > T_last_C.")
    if U <= 0:
        raise ValueError("U doit être > 0.")

    # Bilan matière (soluté conservé)
    P = F_kg_h * xF / xout            # débit produit (kg/h)
    V_total = max(F_kg_h - P, 0.0)    # eau évaporée (kg/h)

    # Répartition uniforme (simple)
    V_i = V_total / n                 # kg/h par effet

    # Economie vapeur (pédagogique)
    economie = min(float(n), 6.0)

    # Conso vapeur
    S = V_total / max(economie, 1e-12)

    # ΔT global et par effet
    dT_total = T_steam_C - T_last_C
    dT_i = dT_total / n

    # Températures par effet (profil linéaire)
    # Effet 1 : Thot ~ T_steam -> Tcold = Thot - dT_i
    # Effet n : Tcold ~ T_last
    T_hot = [T_steam_C - (i - 1) * dT_i for i in range(1, n + 1)]
    T_cold = [th - dT_i for th in T_hot]

    # Puissance et surfaces par effet
    # Q_i = V_i * lambda (kJ/kg) -> kW
    Q_i_kW = (V_i * lambda_kJ_kg) / 3600.0
    Q_i_W = Q_i_kW * 1000.0

    # A_i = Q/(U*dT)
    A_i = Q_i_W / (U * max(dT_i, 1e-9))
    A_total = A_i * n

    details = []
    for i in range(1, n + 1):
        details.append({
            "effect": i,
            "V_kg_h": float(V_i),
            "dT_K": float(dT_i),
            "A_m2": float(A_i),
            "T_hot_C": float(T_hot[i - 1]),
            "T_cold_C": float(T_cold[i - 1]),
        })

    return {
        "S": float(S),
        "economie": float(economie),
        "A_total": float(A_total),
        "V_total": float(V_total),
        "P": float(P),
        "details": details,
    }
