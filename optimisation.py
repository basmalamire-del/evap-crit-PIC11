"""
optimisation.py
----------------
Ce module regroupe :
 - l'étude de l'impact du nombre d'effets (2 à 5)
 - le calcul des coûts d'exploitation annuels (OPEX)
 - une analyse économique globale simple (TCI, coût/tonne, ROI)

Bibliothèques :
 - numpy : calculs
 - evaporateurs : notre modèle d'évaporateur multiple
"""

import numpy as np
from evaporateurs import EvaporateurMultiple


def etudier_nombre_effets(F, Xf, Xout, T_feed, P_steam, max_effets=5):
    """
    Étudie l'impact du nombre d'effets (2,3,4,5) sur :
      - la consommation spécifique de vapeur
      - la surface totale d'échange
      - le coût d'investissement approximatif C_evap

    Retourne une liste de dictionnaires de résultats.
    """
    resultats = []
    for n in range(2, max_effets+1):
        evap = EvaporateurMultiple(F, Xf, Xout, T_feed, P_steam, n_effets=n)
        sim = evap.simuler()
        m_steam = evap.consommation_vapeur()
        econ = evap.economie_vapeur()

        A_tot = sim["A_totale"]
        # Coût d'investissement évaporateurs (formule de l'énoncé)
        Cevap = 15000.0 * (A_tot**0.65)

        resultats.append({
            "n_effets": n,
            "m_steam": m_steam,
            "economie": econ,
            "A_totale": A_tot,
            "Cevap": Cevap
        })
    return resultats


def couts_exploitation_annuels(m_steam_h, cout_vapeur_t=25.0,
                               eau_m3_h=10.0, cout_eau=0.15,
                               P_elec_kW=50.0, cout_elec=0.12,
                               n_operateurs=3, cout_mo=35.0,
                               h_an=8000.0):
    """
    Calcule les coûts d'exploitation annuels (OPEX) de manière simplifiée.

    Paramètres :
      m_steam_h   : débit vapeur (kg/h)
      cout_vapeur_t : €/tonne de vapeur
      eau_m3_h    : débit d'eau de refroidissement (m3/h) (approx.)
      cout_eau    : €/m3
      P_elec_kW   : puissance électrique (kW)
      cout_elec   : €/kWh
      n_operateurs: nombre d'opérateurs
      cout_mo     : €/h par opérateur
      h_an        : heures de fonctionnement par an

    Retour :
      OPEX annuel (€/an)
    """
    # Vapeur
    vapeur_t_h = m_steam_h / 1000.0          # t/h
    C_vapeur = vapeur_t_h * cout_vapeur_t * h_an

    # Eau de refroidissement
    C_eau = eau_m3_h * cout_eau * h_an

    # Électricité
    C_elec = P_elec_kW * cout_elec * h_an

    # Main d'œuvre
    C_mo = n_operateurs * cout_mo * h_an

    return C_vapeur + C_eau + C_elec + C_mo


def analyse_economique_globale(Cevap_total, Ccrist, Cech,
                               OPEX_annuel,
                               production_t_an,
                               taux_actualisation=0.1,
                               duree_vie=10):
    """
    Analyse économique très simplifiée :

      - TCI = C_evap_total + C_crist + C_ech
      - OPEX_annuel = coûts d'exploitation
      - coût_tonne = OPEX_annuel / production annuelle (t/an)
      - ROI_approx = TCI / bénéfice_annuel (ici pris comme OPEX pour simplifier)

    En réalité, il faudrait connaître le prix de vente du sucre pour calculer un ROI réaliste.
    """
    TCI = Cevap_total + Ccrist + Cech
    cout_tonne = OPEX_annuel / max(production_t_an, 1e-6)
    # Ici on prend un ROI très simplifié (à adapter dans le rapport)
    ROI = TCI / max(OPEX_annuel, 1e-6)

    return {
        "TCI": TCI,
        "OPEX": OPEX_annuel,
        "cout_tonne": cout_tonne,
        "ROI_approx": ROI
    }