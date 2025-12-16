# sensibilite.py
import numpy as np
from evaporateurs import EvaporateurMultiple


def sensibilite_parametre(F, xF, xout, Tfeed, Psteam, param="F", valeurs=None):
    if valeurs is None:
        valeurs = np.linspace(0.5, 1.5, 7)

    S_list, A_list, E_list = [], [], []

    for v in valeurs:
        F_loc, xF_loc, P_loc = F, xF, Psteam

        if param == "F":
            F_loc = F * v
        elif param == "xF":
            xF_loc = xF * v
        elif param == "Psteam":
            P_loc = Psteam * v
        else:
            raise ValueError("param doit être 'F', 'xF' ou 'Psteam'")

        evap = EvaporateurMultiple(F_loc, xF_loc, xout, Tfeed, P_loc, 3)
        r = evap.simuler()
        S_list.append(r["S"])
        A_list.append(r["A_totale"])
        E_list.append(r["E"])

    return valeurs, S_list, A_list, E_list


def sensibilite_2D(F, xF, xout, Tfeed, Psteam,
                   param1="F", param2="Psteam",
                   n1=9, n2=9):
    v1 = np.linspace(0.5, 1.5, n1)
    v2 = np.linspace(0.5, 1.5, n2)

    E_grid = np.zeros((n1, n2))
    X_grid = np.zeros((n1, n2))
    Y_grid = np.zeros((n1, n2))

    def map_val(param, factor):
        if param == "F":
            return F * factor
        if param == "xF":
            return xF * factor
        if param == "Psteam":
            return Psteam * factor
        return factor

    for i, a in enumerate(v1):
        for j, b in enumerate(v2):
            F_loc, xF_loc, P_loc = F, xF, Psteam

            if param1 == "F":
                F_loc = F * a
            elif param1 == "xF":
                xF_loc = xF * a
            elif param1 == "Psteam":
                P_loc = Psteam * a

            if param2 == "F":
                F_loc = F * b
            elif param2 == "xF":
                xF_loc = xF * b
            elif param2 == "Psteam":
                P_loc = Psteam * b

            evap = EvaporateurMultiple(F_loc, xF_loc, xout, Tfeed, P_loc, 3)
            r = evap.simuler()
            E_grid[i, j] = r["E"]

            X_grid[i, j] = map_val(param1, a)
            Y_grid[i, j] = map_val(param2, b)

    return X_grid, Y_grid, E_grid
