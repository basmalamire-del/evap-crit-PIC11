"""
thermodynamique.py
-------------------
Ce module regroupe les fonctions liées à la thermodynamique :
 - propriétés de l'eau et de la vapeur via CoolProp
 - point d'ébullition
 - chaleur latente
 - élévation du point d'ébullition (EPE) pour le saccharose (corrélation simplifiée)

Bibliothèques utilisées :
 - CoolProp.CoolProp : bibliothèque thermodynamique pour les fluides
 - numpy : pour d'éventuels calculs numériques
"""

from CoolProp.CoolProp import PropsSI  # Librairie de propriétés thermodynamiques
import numpy as np


def enthalpie_eau(T, P):
    """
    Calcule l'enthalpie spécifique de l'eau (J/kg) à une température T (K) et une pression P (Pa).

    PropsSI("H", "T", T, "P", P, "Water") :
      - "H" : on demande l'enthalpie
      - "T" : clé pour la température
      - "P" : clé pour la pression
      - "Water" : fluide considéré
    """
    return PropsSI("H", "T", T, "P", P, "Water")


def chaleur_latente(P):
    """
    Calcule la chaleur latente de vaporisation de l'eau (J/kg) à une pression P (Pa).

    On prend la différence entre enthalpie vapeur saturée (Q=1) et liquide saturé (Q=0).
    """
    h_v = PropsSI('H', 'P', P, 'Q', 1, 'Water')  # vapeur saturée
    h_l = PropsSI('H', 'P', P, 'Q', 0, 'Water')  # liquide saturé
    return h_v - h_l


def point_ebullition(P):
    """
    Donne la température d'ébullition de l'eau (K) à une pression P (Pa).

    On récupère la température de saturation (Q=0 ou Q=1).
    """
    return PropsSI("T", "P", P, "Q", 0, "Water")


def EPE_duhring(concentration_massique):
    """
    Élévation du point d'ébullition (EPE) en °C en fonction de la concentration massique de saccharose.

    Ici on utilise une corrélation très simplifiée :
        EPE = a * C_massique(%)
    avec a ≈ 0.06 °C par % massique.
    Par exemple, à 65% : EPE ≈ 3.9°C

    concentration_massique : fraction massique (0.0–1.0)
    """
    a = 0.06  # coefficient simplifié
    return a * concentration_massique * 100.0  # °C
