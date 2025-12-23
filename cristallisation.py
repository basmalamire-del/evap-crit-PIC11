# cristallisation.py
import numpy as np

# -----------------------------
# Outils numeriques robustes
# (compatibles numpy 1.x et 2.x)
# -----------------------------
def trapz_robuste(y, x):
    """
    Intégration trapèzes sans dépendre de np.trapz / np.trapezoid
    Compatible partout (numpy 1.x / 2.x).
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if y.size < 2:
        return 0.0
    dx = np.diff(x)
    return float(np.sum(0.5 * (y[:-1] + y[1:]) * dx))


# -----------------------------
# Modèle cristallisation (batch)
# -----------------------------
def solubilite(T):
    # T en °C, retourne C* (g / 100 g solution) - corrélation donnée
    return 64.18 + 0.1337 * T + 5.52e-3 * T**2 - 9.73e-6 * T**3


def sursaturation(C, Cs):
    return max((C - Cs) / Cs, 0.0)


def nucleation(S, mT):
    kb = 1.5e10
    b = 2.5
    j = 0.5
    return kb * (S**b) * max(mT, 1e-12) ** j


def croissance(S, T):
    kg = 2.8e-7
    g = 1.5
    R = 8.314
    Eg = 45000
    return kg * (S**g) * np.exp(-Eg / (R * (T + 273.15)))


def moments(L, n):
    m0 = trapz_robuste(n, L)
    m1 = trapz_robuste(L * n, L)
    m2 = trapz_robuste((L**2) * n, L)

    if m0 <= 0:
        return 0.0, 0.0

    Lmean = m1 / m0
    var = max(m2 / m0 - Lmean**2, 0.0)
    CV = np.sqrt(var) / Lmean if Lmean > 0 else 0.0
    return float(Lmean), float(CV)


def simuler_cristallisation_batch(M, C_init, T_init, duree, dt=60.0, profil="lineaire"):
    """
    Retourne : L, n(L), hist
    hist contient : t, T, S, C, Cs, Lmean, CV
    """
    N = 80
    L = np.linspace(0.0, 8e-4, N)
    dL = L[1] - L[0]
    n = np.zeros_like(L)

    T = float(T_init)
    C = float(C_init)

    tvec = np.arange(0.0, float(duree) + float(dt), float(dt))

    hist = {"t": [], "T": [], "S": [], "C": [], "Cs": [], "Lmean": [], "CV": []}

    for t in tvec:
        Cs = float(solubilite(T))
        S = float(sursaturation(C, Cs))

        mT = trapz_robuste((L**3) * n, L)
        B = float(nucleation(S, mT))
        G = float(croissance(S, T))

        # Transport (upwind) - robuste
        if G > 0.0:
            n_new = np.copy(n)
            for i in range(1, N):
                n_new[i] = n[i] - dt * G * (n[i] - n[i - 1]) / dL
            n_new[0] = B / max(G, 1e-12)
            n = np.maximum(n_new, 0.0)

        # Evolution concentration (simple/stable)
        C = max(C - 0.02 * S * dt / 60.0, Cs)

        # Profils de refroidissement
        if profil == "lineaire":
            T = T_init - (T_init - 35.0) * (t / max(duree, 1e-12))
        elif profil == "expo":
            T = 35.0 + (T_init - 35.0) * np.exp(-0.003 * t)
        else:  # "S_const"
            T = max(T - 0.3 * (S - 0.05), 35.0)

        Lmean, CV = moments(L, n)

        hist["t"].append(float(t))
        hist["T"].append(float(T))
        hist["S"].append(float(S))
        hist["C"].append(float(C))
        hist["Cs"].append(float(Cs))
        hist["Lmean"].append(float(Lmean))
        hist["CV"].append(float(CV))

    return L, n, hist
