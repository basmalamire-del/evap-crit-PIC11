# thermodynamique.py
import numpy as np

# --------- Helpers robustes (anti "truth value of array") ---------
def _as_array(x):
    return np.asarray(x)

def _to_scalar(x, default=0.0):
    """Convertit x en float scalaire si possible, sinon prend la moyenne."""
    a = _as_array(x)
    if a.size == 0:
        return float(default)
    if a.size == 1:
        return float(a.ravel()[0])
    return float(np.mean(a))

def _any_true(x):
    return bool(np.any(_as_array(x)))

def _all_true(x):
    return bool(np.all(_as_array(x)))


# --------- Fonctions thermo (simples + robustes) ---------
def lmtd(dT1, dT2, eps=1e-12):
    """
    LMTD robuste même si dT1/dT2 deviennent des arrays.
    Retourne un float.
    """
    dT1 = _as_array(dT1)
    dT2 = _as_array(dT2)

    # si l'une des ΔT est <= 0 => pas d'échange
    if _any_true(dT1 <= 0) or _any_true(dT2 <= 0):
        return 0.0

    # éviter division par 0 si dT1 ~ dT2
    diff = np.abs(dT1 - dT2)
    if _all_true(diff < eps):
        return _to_scalar(dT1)

    # LMTD = (dT1 - dT2) / ln(dT1/dT2)
    val = (dT1 - dT2) / np.log((dT1 + eps) / (dT2 + eps))
    # si tableau => scalaire
    return _to_scalar(val, default=0.0)


def U_global(type_echange="standard"):
    """
    Coefficient global (valeurs typiques).
    Tu peux ajuster selon ton guide si besoin.
    """
    if type_echange == "standard":
        return 1500.0  # W/m2/K
    if type_echange == "encrasse":
        return 900.0
    return 1200.0


def cp_eau(T=60.0):
    return 4180.0  # J/kg/K approx


def lambda_vapeur(Tsat=120.0):
    """
    Chaleur latente approx (kJ/kg -> J/kg).
    Approche linéaire autour 100-140°C.
    """
    # ~2257 kJ/kg à 100°C, ~2100 kJ/kg vers 140°C
    lam = 2257000.0 - 3500.0 * (Tsat - 100.0)
    return max(lam, 1800000.0)


def Tsat_from_Pbar(Pbar):
    """
    Température de saturation approx (°C) en fonction de P (bar abs).
    Approximation simple (suffisante pour un PIC).
    """
    Pbar = max(float(Pbar), 0.05)
    # approx: à 1 bar -> 100°C, à 2 bar -> 120°C, à 3.5 bar ~ 147°C
    # fit log:
    return 100.0 + 45.0 * np.log(Pbar)


def bpe_sucre(x):
    """
    Élévation du point d’ébullition (BPE) approximative pour solution sucrée.
    x = fraction massique (0-1).
    """
    x = float(x)
    x = min(max(x, 0.0), 0.85)
    return 8.0 * x  # °C (approx)
