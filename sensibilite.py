import numpy as np
import pandas as pd
from evaporateurs import simulation_evaporation_multi_effets

def sensibilite_nombre_effets(
    F_kg_h: float,
    xF: float,
    xout: float,
    n_min: int = 2,
    n_max: int = 6,
    T_steam_C: float = 120.0,
    T_last_C: float = 60.0
):
    rows = []
    for n in range(int(n_min), int(n_max) + 1):
        res = simulation_evaporation_multi_effets(
            F_kg_h=F_kg_h,
            xF=xF,
            xout=xout,
            n_effets=n,
            T_steam_C=T_steam_C,
            T_last_C=T_last_C,
        )
        rows.append({"Nombre_effets": n, "Debit_vapeur_S": res["S"], "Surface_totale_A": res["A_total"]})
    return pd.DataFrame(rows)


def sensibilite_parametre(F, xF, xout, Tfeed, Psteam, param="F", valeurs=None):
    if valeurs is None:
        valeurs = np.linspace(0.5, 1.5, 5).tolist()
    S_list = []
    A_list = []
    E_list = []
    for fac in valeurs:
        Fv, xFv, xoutv = float(F), float(xF), float(xout)
        nev = 3
        Tsteam = float(Tfeed)
        if param == "F":
            Fv = float(F) * float(fac)
        elif param == "xF":
            xFv = float(xF) * float(fac)
        elif param == "xout":
            xoutv = float(xout) * float(fac)
        elif param == "Tfeed":
            Tsteam = float(Tfeed) * float(fac)
        elif param == "Psteam":
            Pval = float(Psteam) * float(fac)
            Tsteam = float(Tfeed) + (Pval - float(Psteam)) * 10.0
        elif param == "n_effets":
            nev = max(1, int(round(float(fac) * 3)))
        res = simulation_evaporation_multi_effets(
            F_kg_h=Fv,
            xF=xFv,
            xout=xoutv,
            n_effets=int(nev),
            T_steam_C=float(Tsteam),
            T_last_C=60.0,
        )
        S_list.append(res.get("S"))
        A_list.append(res.get("A_total"))
        E_list.append(res.get("economie"))
    return list(valeurs), S_list, A_list, E_list


def sensibilite_2D(F, xF, xout, Tfeed, Psteam, param1="F", param2="Psteam", n1=11, n2=11):
    base = {"F": float(F), "xF": float(xF), "xout": float(xout), "Tfeed": float(Tfeed), "Psteam": float(Psteam)}
    r1 = np.linspace(0.5, 1.5, int(n1))
    r2 = np.linspace(0.5, 1.5, int(n2))
    vals1 = base.get(param1, float(F)) * r1
    vals2 = base.get(param2, float(Psteam)) * r2
    X, Y = np.meshgrid(vals1, vals2)
    Sgrid = np.zeros_like(X, dtype=float)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            v1 = X[i, j]
            v2 = Y[i, j]
            Fv, xFv, xoutv = float(F), float(xF), float(xout)
            Tsteam = float(Tfeed)
            if param1 == "F":
                Fv = v1
            elif param1 == "xF":
                xFv = v1
            elif param1 == "xout":
                xoutv = v1
            elif param1 == "Tfeed":
                Tsteam = v1
            elif param1 == "Psteam":
                Tsteam = float(Tfeed) + (v1 - float(Psteam)) * 10.0
            if param2 == "F":
                Fv = v2
            elif param2 == "xF":
                xFv = v2
            elif param2 == "xout":
                xoutv = v2
            elif param2 == "Tfeed":
                Tsteam = v2
            elif param2 == "Psteam":
                Tsteam = float(Tfeed) + (v2 - float(Psteam)) * 10.0
            res = simulation_evaporation_multi_effets(
                F_kg_h=Fv,
                xF=xFv,
                xout=xoutv,
                n_effets=3,
                T_steam_C=float(Tsteam),
                T_last_C=60.0,
            )
            # on utilise la conso vapeur S (varie plus que 'economie')
            Sgrid[i, j] = res.get("S", np.nan)
    return X, Y, Sgrid


# aliases pour compatibilité si tu avais des noms accentués
sensibilité_parametre = sensibilite_parametre
sensibilité_2D = sensibilite_2D