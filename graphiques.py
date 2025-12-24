# graphiques.py
import matplotlib.pyplot as plt
import os

def init_output_dir():
    if not os.path.exists("resultats"):
        os.makedirs("resultats")


def graphique_cristallisation(hist, titre="Profil de cristallisation"):
    init_output_dir()

    t = hist["t"] if "t" in hist else range(len(hist["T"]))
    plt.figure()
    plt.plot(t, hist["T"], label="Température (°C)")
    plt.plot(t, hist["S"], label="Sursaturation S")
    plt.xlabel("Temps (s)")
    plt.legend()
    plt.title(titre)
    plt.grid()
    plt.savefig("resultats/cristallisation.png")
    plt.close()

    plt.figure()
    plt.plot(t, hist["Lmean"], label="Taille moyenne L̄ (m)")
    plt.plot(t, hist["CV"], label="Coefficient de variation CV")
    plt.xlabel("Temps (s)")
    plt.legend()
    plt.title("Évolution granulométrique")
    plt.grid()
    plt.savefig("resultats/granulometrie.png")
    plt.close()


def graphique_evaporation(evap_dict):
    init_output_dir()

    x = evap_dict["x"]
    T = evap_dict["T"]
    A = evap_dict["A"]
    effets = range(1, len(x)+1)

    plt.figure()
    plt.plot(effets, T, "o-")
    plt.xlabel("Effet")
    plt.ylabel("Teb (°C)")
    plt.title("Températures d'ébullition par effet")
    plt.grid()
    plt.savefig("resultats/evap_T.png")
    plt.close()

    plt.figure()
    plt.bar(effets, A)
    plt.xlabel("Effet")
    plt.ylabel("Surface (m²)")
    plt.title("Surface d'échange par effet")
    plt.grid()
    plt.savefig("resultats/evap_A.png")
    plt.close()