# evaporateurs.py
import numpy as np
from thermodynamique import lmtd, U_global, Tsat_from_Pbar, lambda_vapeur, bpe_sucre

# --------- Helpers robustes ---------
def _as_array(x):
    return np.asarray(x)

def _to_scalar(x, default=0.0):
    a = _as_array(x)
    if a.size == 0:
        return float(default)
    if a.size == 1:
        return float(a.ravel()[0])
    return float(np.mean(a))


class EvaporateurMultiple:
    """
    Batterie d'évaporateurs multiples (modèle PIC stable pour dashboard).
    Entrées:
        F (kg/h), xF, xout, Tfeed (°C), Psteam (bar), n_effets
    Sorties:
        dict avec S, E, A_totale + profils par effet (L, V, x, A, T, Tsat, ...)
    """

    def __init__(self, F, xF, xout, Tfeed, Psteam, n_effets=3):
        self.F = float(F)
        self.xF = float(xF)
        self.xout = float(xout)
        self.Tfeed = float(Tfeed)
        self.Psteam = float(Psteam)
        self.n = int(n_effets)

        if not (0 < self.xF < 1) or not (0 < self.xout < 1):
            raise ValueError("xF et xout doivent être entre 0 et 1.")
        if self.xout <= self.xF:
            raise ValueError("xout doit être > xF (concentration augmente).")
        if self.n < 1:
            raise ValueError("n_effets >= 1")

    def simuler(self):
        # --- Bilan matière global ---
        solute = self.F * self.xF
        L_final = solute / self.xout
        V_tot = self.F - L_final  # eau évaporée totale (kg/h)

        # --- Répartition simple par effet (stable) ---
        # On répartit l’évaporation uniformément (tu peux adapter si ton guide impose autre chose)
        V = np.full(self.n, V_tot / self.n, dtype=float)

        # Débits liquides par effet
        L = np.zeros(self.n + 1, dtype=float)
        x = np.zeros(self.n + 1, dtype=float)
        L[0] = self.F
        x[0] = self.xF

        for i in range(self.n):
            L[i + 1] = L[i] - V[i]
            L[i + 1] = max(L[i + 1], 1e-6)
            x[i + 1] = solute / L[i + 1]

        # --- Profils thermiques ---
        # Vapeur motrice (effet 1)
        Tsteam = Tsat_from_Pbar(self.Psteam)

        # On suppose une chute de température totale disponible
        # (valeur typique, ajustable)
        T_last = 60.0  # °C, condenseur/dernier effet
        dT_total = max(Tsteam - T_last, 10.0)
        dT_eff = dT_total / self.n

        T_boil = np.zeros(self.n, dtype=float)
        Tsat = np.zeros(self.n, dtype=float)
        for i in range(self.n):
            Tsat[i] = Tsteam - (i + 1) * dT_eff
            # BPE sucre
            T_boil[i] = Tsat[i] + bpe_sucre(x[i + 1])

        # --- Surfaces d'échange ---
        U = U_global("standard")
        A = np.zeros(self.n, dtype=float)

        # Hypothèse : chaleur = V[i] * lambda (approx)
        for i in range(self.n):
            lam = lambda_vapeur(Tsat[i])  # J/kg
            Q = V[i] * lam / 3600.0  # W (car V en kg/h)

            # ΔT1/ΔT2 (robuste)
            # côté chaud: Tsat[i] (condensation), côté froid: T_boil[i]
            dT1 = Tsat[i] - T_boil[i]
            dT2 = Tsat[i] - (T_boil[i] - 2.0)  # petit écart pour éviter dT1==dT2
            DTlm = lmtd(dT1, dT2)

            if DTlm <= 0:
                A[i] = 0.0
            else:
                A[i] = Q / (U * DTlm)

        A_totale = float(np.sum(A))

        # --- Consommation vapeur S et économie ---
        # Modèle simple: consommation vapeur ~ évaporation 1er effet
        # (si ton guide impose autre chose, remplace seulement ce bloc)
        S = float(V[0])
        E = float(V_tot / max(S, 1e-9))

        # Résultats
        res = {
            "S": S,
            "E": E,
            "A_totale": A_totale,
            "V_tot": float(V_tot),
            "L": L,              # taille n+1
            "V": V,              # taille n
            "x": x,              # taille n+1
            "A": A,              # taille n
            "Tsteam": float(Tsteam),
            "Tsat": Tsat,        # taille n
            "T_boil": T_boil,    # taille n
        }
        return res
