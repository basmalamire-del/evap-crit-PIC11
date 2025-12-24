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
    lambda_kJ_kg: float = 2257.0,
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
    P = F_kg_h * xF / xout          # débit produit (kg/h)
    V_total = max(F_kg_h - P, 0.0)  # eau évaporée (kg/h)

    # Répartition uniforme (simple)
    V_i = V_total / n               # kg/h par effet

    # Economie vapeur (pédagogique)
    economie = min(float(n), 6.0)

    # Conso vapeur
    S = V_total / max(economie, 1e-12)

    # ΔT global et par effet
    dT_total = T_steam_C - T_last_C
    dT_i = dT_total / n

    # Températures par effet (profil linéaire)
    T_hot = [T_steam_C - (i - 1) * dT_i for i in range(1, n + 1)]
    T_cold = [th - dT_i for th in T_hot]

    # Puissance et surfaces par effet
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


class EvaporateurMultiple:
    """Classe wrapper pour compatibilité avec streamlit_app.py"""

    def __init__(self, F, xF, xout, Tfeed, Psteam, n_effets):
        self.F = float(F)
        self.xF = float(xF)
        self.xout = float(xout)
        self.Tfeed = float(Tfeed)
        self.Psteam = float(Psteam)
        self.n_effets = int(n_effets)

    def simuler(self):
        # On choisit une vapeur un peu plus chaude que le feed
        T_steam_C = self.Tfeed + 35.0
        T_last_C = 60.0

        out = simulation_evaporation_multi_effets(
            F_kg_h=self.F,
            xF=self.xF,
            xout=self.xout,
            n_effets=self.n_effets,
            T_steam_C=T_steam_C,
            T_last_C=T_last_C,
        )

        details = out.get("details", []) or []

        # listes par effet
        V_list = [d.get("V_kg_h", 0.0) for d in details] if details else None
        A_list = [d.get("A_m2") for d in details] if details else None
        T_list = [d.get("T_hot_C") for d in details] if details else None

        # construire L (débit liquide entrant à chaque effet) et x (concentration)
        x_list = None
        L_list = None
        if V_list:
            solute_kg_h = self.F * self.xF  # masse de soluté (kg/h)
            L_list = []
            x_list = []
            L_curr = float(self.F)
            for v in V_list:
                L_list.append(float(L_curr))
                x_val = solute_kg_h / max(L_curr, 1e-12)
                x_list.append(float(x_val))
                L_curr = max(0.0, L_curr - float(v))

        # garder compatibilité avec différents noms attendus
        return {
            "S": out.get("S"),
            "economie": out.get("economie"),
            "E": out.get("economie"),
            "A_total": out.get("A_total"),
            "A_totale": out.get("A_total"),
            "A_tot": out.get("A_total"),
            "A": A_list,
            "A_effets": A_list,
            "T": T_list,
            "T_effets": T_list,
            "Teb": T_list,
            "V": V_list,
            "V_effets": V_list,
            "debit_vapeur": V_list,
            "L": L_list,
            "L_effets": L_list,
            "x": x_list,
            "x_effets": x_list,
            "details": details,
        }
