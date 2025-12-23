# sensibilite.py
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
