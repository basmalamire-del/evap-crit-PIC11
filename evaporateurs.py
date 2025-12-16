# evaporateurs.py
# Modèle simplifié d'une batterie d'évaporateurs multiples (pédagogique)
# Retourne un dictionnaire compatible Streamlit : S, E, A, A_totale, T, x, L, V

import numpy as np
from dataclasses import dataclass
from CoolProp.CoolProp import PropsSI


def _Tsat_eau(P_bar: float) -> float:
    """Température de saturation eau (°C) à la pression P (bar abs)."""
    T = PropsSI("T", "P", P_bar * 1e5, "Q", 0, "Water")
    return T - 273.15


def _chaleur_latente_bar(P_bar: float) -> float:
    """Chaleur latente de vaporisation (J/kg) à P (bar abs)."""
    h_v = PropsSI("H", "P", P_bar * 1e5, "Q", 1, "Water")
    h_l = PropsSI("H", "P", P_bar * 1e5, "Q", 0, "Water")
    return h_v - h_l


def _EPE_duhring(xm: float) -> float:
    """
    Élévation du point d'ébullition (°C) vs fraction massique saccharose.
    Corrélation simple type Dühring (approx).
    """
    x = xm * 100.0  # %
    if x < 50:
        A, B = 0.03, 0.00015
    else:
        A, B = 0.045, 0.00030
    return A * x + B * x * x


def _Teb_solution(P_bar: float, xm: float) -> float:
    """Température d'ébullition solution saccharose/eau (°C)."""
    return _Tsat_eau(P_bar) + _EPE_duhring(xm)


@dataclass
class Effet:
    P_bar: float
    U: float  # W/m²/K


class EvaporateurMultiple:
    """
    Batterie d'évaporateurs multiples (simplifiée et stable).

    Entrées:
      F (kg/h), xF (-), xout (-), T_feed (°C), Psteam (bar abs), n_effets (2..5)

    Sorties (via simuler()):
      L, V, x, T, A, A_totale, S, E
    """

    def __init__(self, F, xF, xout, T_feed_C, P_steam_bar, n_effets=3):
        self.F = float(F)
        self.xF = float(xF)
        self.xout = float(xout)
        self.T_feed = float(T_feed_C)
        self.Psteam = float(P_steam_bar)
        self.n = int(n_effets)

        if not (2 <= self.n <= 5):
            raise ValueError("n_effets doit être entre 2 et 5.")
        if not (0 < self.xF < 1 and 0 < self.xout < 1):
            raise ValueError("xF et xout doivent être des fractions (0..1).")
        if self.xout <= self.xF:
            raise ValueError("xout doit être > xF (concentration augmente).")

        # Pressions par effet (approx, bar abs)
        self.P_eff = np.linspace(2.5, 0.15, self.n)

        # U typiques (W/m²/K)
        U_base = [2500, 2200, 1800, 1600, 1500]
        self.U_eff = U_base[:self.n]

        self.effets = [Effet(self.P_eff[i], self.U_eff[i]) for i in range(self.n)]

    def bilan_matiere(self):
        """Bilans matière simplifiés avec évaporation totale répartie uniformément."""
        F = self.F
        xF = self.xF
        xout = self.xout
        n = self.n

        # Liquide sortie global
        Lout = F * xF / xout
        Vtot = F - Lout

        # Répartition uniforme
        V = np.full(n, Vtot / n)

        # Débits liquides
        L = np.zeros(n)
        L[0] = F - V[0]
        for i in range(1, n):
            L[i] = L[i - 1] - V[i]

        # Concentrations
        x = np.zeros(n)
        x[0] = F * xF / L[0]
        for i in range(1, n):
            x[i] = x[i - 1] * L[i - 1] / L[i]

        return L, V, x, Lout, Vtot

    def simuler(self):
        """
        Simulation stable, renvoie:
          {"L","V","x","T","A","A_totale","S","E"}
        """
        L, V, x, Lout, Vtot = self.bilan_matiere()

        # Températures d'ébullition
        Teb = np.array([_Teb_solution(self.effets[i].P_bar, x[i]) for i in range(self.n)])

        # Vapeur de chauffe
        Tsteam = _Tsat_eau(self.Psteam) + 10.0
        lambda_steam = _chaleur_latente_bar(self.Psteam)

        # kg/h -> kg/s
        V_s = V / 3600.0

        Q = np.zeros(self.n)  # W
        A = np.zeros(self.n)  # m²

        for i in range(self.n):
            lambda_i = _chaleur_latente_bar(self.effets[i].P_bar)
            Q[i] = V_s[i] * lambda_i

            if i == 0:
                dT = max(Tsteam - Teb[0], 1.0)
            else:
                dT = max(Teb[i - 1] - Teb[i], 1.0)

            A[i] = Q[i] / (self.effets[i].U * dT)

        Q_tot = float(np.sum(Q))
        S_s = Q_tot / lambda_steam
        S_h = S_s * 3600.0

        E = Vtot / S_h if S_h > 0 else 0.0

        return {
            "L": L,
            "V": V,
            "x": x,
            "T": Teb,
            "A": A,
            "A_totale": float(np.sum(A)),
            "S": float(S_h),
            "E": float(E),
        }

    def consommation_vapeur(self):
        return self.simuler()["S"]

    def economie_vapeur(self):
        return self.simuler()["E"]
