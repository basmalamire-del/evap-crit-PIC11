# thermodynamique.py
import numpy as np

def to_float(x, default=0.0):
    """
    Force un scalaire float même si x est un tableau numpy.
    """
    try:
        a = np.asarray(x)
        if a.size == 0:
            return float(default)
        return float(a.reshape(-1)[0])
    except Exception:
        return float(default)

def Tsat_water_from_Pbar(Pbar):
    """
    Saturation eau (approx) : entrée en bar, sortie en °C
    Approx simple (suffisant projet PIC)
    """
    P = max(to_float(Pbar), 0.01)
    # approximation “soft” : 1 bar -> 100°C ; 3.5 bar -> ~143°C
    return 100.0 + 43.0 * np.log(P)

def latent_heat_kJkg(Tc):
    """
    Chaleur latente approx (kJ/kg) en fonction de T (°C)
    """
    T = to_float(Tc, 100.0)
    return float(2500.0 - 2.3 * (T - 0.0))

def LMTD(dT1, dT2):
    """
    LMTD robuste, sans if sur tableaux.
    """
    dT1 = to_float(dT1)
    dT2 = to_float(dT2)
    if dT1 <= 0.0 or dT2 <= 0.0:
        return 0.0
    if abs(dT1 - dT2) < 1e-9:
        return float(dT1)
    return float((dT1 - dT2) / np.log(dT1 / dT2))
